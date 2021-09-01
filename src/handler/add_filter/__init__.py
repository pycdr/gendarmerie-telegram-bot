from datetime import datetime, timedelta
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot,
    message
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters,
    conversationhandler
)

GET_GROUP, GET_TYPE, GET_REGEX = range(3)
TYPE_REMOVE, TYPE_RESTRICT, TYPE_BAN = range(3)
EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def start_process(update: Update, context: CallbackContext, model, token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        Bot(token).delete_message(
            update.message.chat.id,
            update.message.message_id
        )
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0003"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to add new filter (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP

def get_group_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    try:
        group_id = int(query.data[4:])
    except ValueError:
        query.answer("invalid group id!")
        return ConversationHandler.END
    if not next(iter(model.Group.select().where(model.Group.id == group_id)), False):
        query.answer("group doesn't exists anymore, maybe in my list! add with /add command.")
        return ConversationHandler.END
    if not is_admin(group_id, query.from_user.id, token):
        query.answer("you are not admin!!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0003group_id"] = group_id
    query.edit_message_text(
        "OK! now, choose one of these types for your filter (* restrict mode will be set for 1 day):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("remove message", callback_data="0003"+"0")],
            [
                InlineKeyboardButton("restrict user", callback_data="0003"+"1"),
                InlineKeyboardButton("ban user", callback_data="0003"+"2")
            ],
            [InlineKeyboardButton("back to the previous menu", callback_data="0003"+"GET_BACK")]
        ])
    )
    return GET_TYPE

def get_type_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    if query.data[4:] == "GET_BACK":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0003"+str(group.id)
            )]
            for group in model.Group.select()
            if is_admin(group.id, update.message.from_user.id, token)
        ])
        update.message.reply_text(
            "OK! choose one of your groups to add new filter (if there's any! :D)",
            reply_markup=keyboard
        )
        return GET_GROUP
    try:
        type_id = int(query.data[4:])
        if type_id not in range(3):
            query.answer("invalid type id!")
            return ConversationHandler.END
    except ValueError:
        query.answer("invalid type id!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0003type_id"] = type_id
    query.edit_message_text(
        "OK! now, send the regex to detect the message (notice that it uses <re.match>): ",
        reply_markup=InlineKeyboardMarkup([])
    )
    return GET_REGEX

def get_regex_by_message(update: Update, context: CallbackContext, model, token: str):
    regex = update.message.text
    context.user_data["0003regex"] = regex
    # add to model:
    group = model.Group.get(model.Group.id == context.user_data["0003group_id"])
    type_id = context.user_data["0003type_id"]
    regex = regex # :/
    new_filter = model.Filter.create(
        group = group,
        type_id = type_id,
        regex = regex,
        restrict_until = datetime.now() + timedelta(1)
    )
    update.message.reply_text(
        f"done! your filter details:\n"
        f"group: {new_filter.group.name}\n"
        f"regex: {regex}\n"
        f"type: {['remove message', 'restrict user', 'ban user'][type_id]}",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def cancel_process(update: Update, context: CallbackContext):
    context.user_data.clear()
    update.message.reply_text(
        "canceled."
    )
    return ConversationHandler.END

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    add_filter_handler = ConversationHandler(
        entry_points=[
            CommandHandler("addfilter", pass_model_and_token(start_process, model, token)),
            CommandHandler("newfilter", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(get_group_by_callback, model, token),
                    pattern=r'^0003-\d+$'
                )
            ],
            GET_TYPE: [
                CallbackQueryHandler(
                    pass_model_and_token(get_type_by_callback, model, token),
                    pattern=r'^0003(0|1|2)$'
                )
            ],
            GET_REGEX: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_regex_by_message, model, token)
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return add_filter_handler
