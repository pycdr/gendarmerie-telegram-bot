from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot,
    message,
    user
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters
)

GET_GROUP, GET_TYPE, GET_REGEX, GET_BACK = range(4)
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
            callback_data="0203"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to delete a filter (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP

def state_get_group_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
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
    context.user_data["0203group_id"] = group_id
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these filter types:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("remove message", callback_data="0203"+"0")],
            [
                InlineKeyboardButton("restrict user", callback_data="0203"+"1"),
                InlineKeyboardButton("ban user", callback_data="0203"+"2")
            ],
            [InlineKeyboardButton("back to the previous menu", callback_data="0203"+'GET_BACK')]
            ])
        )
    return GET_TYPE

def state_get_type_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    if query.data[4:] != "GET_BACK":
        try:
            type_id = int(query.data[4:])
        except ValueError:
            query.answer("invalid type id!")
            return ConversationHandler.END
        if type_id not in range(3):
            query.answer("the type id is not found!")
            return ConversationHandler.END
        query.answer()
        context.user_data["0203type_id"] = type_id
        type_as_str = ["remove message mode", "restrict user mode", "ban user mode"][type_id]
        query.edit_message_text(
            f"OK! for {type_as_str}, choose one of this regexes to remove it:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(msg_filter.regex, callback_data="0203"+msg_filter.regex)]
                for msg_filter in model.Group.get(
                    model.Group.id == context.user_data["0203group_id"]
                ).filters.select().where(
                    model.Filter.type_id == type_id
                )
            ] + [[InlineKeyboardButton("get back to the previous menu", callback_data="0203"+"GET_BACK")]])
        )
        return GET_REGEX
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0203"+str(group.id)
            )]
            for group in model.Group.select()
            if is_admin(group.id, (update.message or update.callback_query).from_user.id, token)
        ])
        query.edit_message_text(
            "OK! choose one of your groups to delete a filter (if there's any! :D)",
            reply_markup=keyboard
        )
        return GET_GROUP 

def state_get_regex_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    type_id = context.user_data["0203type_id"]
    if query.data[4:] != "GET_BACK":
        regex = query.data[4:]
        group_id = context.user_data["0203group_id"]
        msg_filter = next((msg_filter for msg_filter in model.Filter.select().where(
            model.Filter.type_id == type_id
        ) if msg_filter.group.id == group_id and msg_filter.regex == regex), False)
        if not msg_filter:
            query.answer("oops! nothing found for you!")
            return GET_BACK
        regex = msg_filter.regex
        type_as_str = ["remove message mode", "restrict user mode", "ban user mode"][type_id]
        group_name = msg_filter.group.name
        msg_filter.delete_instance()
        query.edit_message_text(
            f"regex {regex} from {type_as_str} is removed for group {group_name}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("back to the commands", callback_data="0203"+'GET_BACK')]])
        )
        return GET_BACK
    else:
        query.answer()
        query.edit_message_text(
            f"OK! for group \"{model.Group.get(model.Group.id == context.user_data['0203group_id']).name}\", select one of these filter types:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("remove message", callback_data="0203"+"0")],
                [
                    InlineKeyboardButton("restrict user", callback_data="0203"+"1"),
                    InlineKeyboardButton("ban user", callback_data="0203"+"2")
                ],
                [InlineKeyboardButton("back to the previous menu", callback_data="0203"+'GET_BACK')]
                ])
            )
        return GET_TYPE

def state_get_back_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    query.answer()
    group_id = context.user_data["0203group_id"]
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these special commands:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("remove message", callback_data="0203"+"0")],
            [
                InlineKeyboardButton("restrict user", callback_data="0203"+"1"),
                InlineKeyboardButton("ban user", callback_data="0203"+"2")
            ],
            [InlineKeyboardButton("back to the previous menu", callback_data="0203"+'GET_BACK')]
            ])
        )
    return GET_TYPE

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
    get_special_handler = ConversationHandler(
        entry_points=[
            CommandHandler("delfilter", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_by_callback, model, token), 
                    pattern=r'^0203-\d+$'
                )
            ],
            GET_TYPE: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_type_by_callback, model, token),
                    pattern=r'0203.+'
                )
            ],
            GET_REGEX: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_regex_by_callback, model, token),
                    pattern=r"0203.+"
                )
            ],
            GET_BACK: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_back_by_callback, model, token),
                    pattern='0203GET_BACK'
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return get_special_handler
