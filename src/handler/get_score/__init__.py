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

GET_GROUP, GET_USER = range(2)
EMOJI_PLUS, EMOJI_MINUS = 10133, 10134
PROPS = ("forward",)

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def start_process(update: Update, context: CallbackContext, model, token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if not is_admin(update.message.chat.id, update.message.from_user.id, token):
            update.message.delete()
        elif update.message.reply_to_message:
            update.message.delete()
            user = next((
                user
                for user in model.User.select().where(
                    model.User.id == update.message.reply_to_message.from_user.id
                )
                if user.group.id == update.message.chat.id
            ), None)
            name = update.message.reply_to_message.from_user.full_name
            if not user:
                update.message.reply_to_message.reply_text(
                    "<code>"+html.escape(f">>> score[{repr(name)}]\n0")+"</code>",
                    parse_mode="HTML"
                )
            else:
                score = user.score
                name = update.message.reply_to_message.from_user.full_name
                update.message.reply_to_message.reply_text(
                    "<code>"+html.escape(f">>> score[{repr(name)}]\n{score}")+"</code>",
                    parse_mode="HTML"
                )
        else:
            user = next((
                user
                for user in model.User.select(
                    model.User.id == update.message.from_user.id
                )
                if user.group.id == update.message.chat.id
            ), None)
            name = update.message.from_user.full_name
            if not user:
                update.message.reply_text(
                    "<code>"+html.escape(f">>> score[{repr(name)}]\n0")+"</code>",
                    parse_mode="HTML"
                )
            else:
                score = user.score
                name = update.message.from_user.full_name
                update.message.reply_text(
                    "<code>"+html.escape(f">>> score[{repr(name)}]\n{score}")+"</code>",
                    parse_mode="HTML"
                )
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0104"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to get users score (if there's any! :D)",
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
        query.answer("group doesn't exists anymore, maybe in my list! add with /addgroup command.")
        return ConversationHandler.END
    if not is_admin(group_id, query.from_user.id, token):
        query.answer("you are not admin!!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0104group_id"] = group_id
    group = model.Group.get(model.Group.id == context.user_data["0104group_id"])
    top_users = sorted(group.users, key = lambda user:user.score)[-10:][::-1]
    query.edit_message_text(
        f"top 10 for group \"{group.name}\":",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(user.name, callback_data = "0104"+"PASS"),
                    InlineKeyboardButton(f"{user.score}", callback_data = "0104"+"PASS")
                ]
                for user in top_users
            ]+[
                [
                    InlineKeyboardButton("back to the previous menu", callback_data="0104"+"GET_BACK")
                ]
            ]
        )
    )
    return GET_USER

def state_get_user_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    if query.data[4:] == "GET_BACK":
        query.answer()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0104"+str(group.id)
            )]
            for group in model.Group.select()
            if is_admin(group.id, query.from_user.id, token)
        ])
        query.edit_message_text(
            "OK! choose one of your groups to get top users (if there's any! :D)",
            reply_markup=keyboard
        )
        return GET_GROUP
    elif query.data[4:] == "PASS":
        query.answer()
        return GET_USER
    else:
        query.answer("invalid query!")
        return GET_USER

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
            CommandHandler("score", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_by_callback, model, token), 
                    pattern=r'^0104-\d+$'
                )
            ],
            GET_USER: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_user_by_callback, model, token),
                    pattern=r'0104.+'
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return set_locks_handler
