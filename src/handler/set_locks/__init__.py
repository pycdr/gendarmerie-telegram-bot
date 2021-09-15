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
    Filters
)
import html, json

GET_GROUP, GET_PROP = range(2)
EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)
EMOJI_TRUE = chr(9989)
EMOJI_FALSE = chr(10060)
PROPS = ("forward",)

def bool_emoji(status: bool) -> str:
    return [EMOJI_FALSE, EMOJI_TRUE][status]

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
            callback_data="0500"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to set some locks (if there's any! :D)",
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
    context.user_data["0500group_id"] = group_id
    group = model.Group.get(model.Group.id == context.user_data["0500group_id"])
    query.edit_message_text(
        f"OK! for group \"{group.name}\", select one of these options to change it:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"lock forward: {bool_emoji(group.locks[0].forward)}", callback_data="0500"+"forward")
            ],
            [
                InlineKeyboardButton("back to the previous menu", callback_data="0500"+"GET_BACK")
            ]
        ])
    )
    return GET_PROP

def state_get_prop_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    if query.data[4:] == "GET_BACK":
        query.answer()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0500"+str(group.id)
            )]
            for group in model.Group.select()
            if is_admin(group.id, update.message.from_user.id, token)
        ])
        query.edit_message_text(
            "OK! choose one of your groups to set some locks (if there's any! :D)",
            reply_markup=keyboard
        )
        return GET_GROUP
    if query.data[4:] not in PROPS:
        query.answer("invalid prop!")
        return GET_PROP
    prop = query.data[4:]
    group = model.Group.get(model.Group.id == context.user_data["0500group_id"])
    model.Locks.update(**{
        prop: not getattr(group.locks[0], prop)
    }).where(model.Locks.group == group).execute()
    query.answer("done!")
    query.edit_message_text(
        f"OK! for group \"{group.name}\", select one of these options to change it:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"lock forward: {bool_emoji(group.locks[0].forward)}", callback_data="0500"+"forward")
            ],
            [
                InlineKeyboardButton("back to the previous menu", callback_data="0500"+"GET_BACK")
            ]
        ])
    )
    return GET_PROP

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
    set_locks_handler = ConversationHandler(
        entry_points=[
            CommandHandler("locks", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_by_callback, model, token), 
                    pattern=r'^0500-\d+$'
                )
            ],
            GET_PROP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_prop_by_callback, model, token),
                    pattern=r'0500.+'
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return set_locks_handler
