from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Bot,
    Chat
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
import os, shutil

from telegram.message import Message

EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)
GET_GROUP_DB, GET_COMMAND_DB, GET_USERS_DB, CONFIRM = range(4)

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def start_process(update: Update, context: CallbackContext, model, token):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        update.message.delete()
        return
    admin_id = int(os.getenv("ADMIN", "0"))
    if admin_id == update.message.from_user.id:
        update.message.reply_text(
            "OK! send me the .db file of your group:"
        )
        return GET_GROUP_DB
    else:
        update.message.reply_text("0`_´0")

def status_get_groups_db_by_document(update: Update, context: CallbackContext, model, token) -> int:
    file = context.bot.getFile(update.message.document.file_id)
    file.download(".downloaded_groups.db")
    update.message.reply_text(
        "OK! now, send the commands .db file: "
    )
    return GET_COMMAND_DB

def status_get_commands_db_by_document(update: Update, context: CallbackContext, model, token) -> int:
    file = context.bot.getFile(update.message.document.file_id)
    file.download(".downloaded_commands.db")
    update.message.reply_text(
        "OK! now, send the users .db file: "
    )
    return GET_USERS_DB

def status_get_users_db_by_document(update: Update, context: CallbackContext, model, token) -> int:
    file = context.bot.getFile(update.message.document.file_id)
    file.download(".downloaded_users.db")
    update.message.reply_text(
        "OK! for there .db files, are you sure you wanna replace main .db files with them? nitice that **previous .db files will be deleted forever!** if you want to get backup, cancel this process and use /backup command.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(EMOJI_LIKE, callback_data="0301"+"1"),
            InlineKeyboardButton(EMOJI_DISLIKE, callback_data="0301"+"0")
        ]])
    )
    return CONFIRM

def status_confirm_by_callback(update: Update, context: CallbackContext, model, token) -> int:
    query = update.callback_query
    query.answer()
    do = (query.data[4:] == "1")
    if do:
        shutil.move(".downloaded_groups.db", "groups.db")
        shutil.move(".downloaded_commands.db", "commands.db")
        shutil.move(".downloaded_users.db", "users.db")
        model.groups_database.init("groups.db")
        model.commands_database.init("commands.db")
        model.users_database.init("users.db")
        query.edit_message_text(
            "done!",
            reply_markup=InlineKeyboardMarkup([])
        )
    else:
        query.edit_message_text(
            "canceled.",
            reply_markup=InlineKeyboardMarkup([])
        )
    return ConversationHandler.END

def cancel_process(update: Update, context: CallbackContext):
    context.user_data.clear()
    update.message.reply_text(
        "canceled."
    )
    return ConversationHandler.END

def creator(model, token):
    handler = ConversationHandler(
        entry_points=[
            CommandHandler("database", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP_DB: [
                MessageHandler(Filters.document, pass_model_and_token(status_get_groups_db_by_document, model, token))
            ],
            GET_COMMAND_DB: [
                MessageHandler(Filters.document, pass_model_and_token(status_get_commands_db_by_document, model, token))
            ],
            GET_USERS_DB: [
                MessageHandler(Filters.document, pass_model_and_token(status_get_users_db_by_document, model, token))
            ],
            CONFIRM: [
                CallbackQueryHandler(
                    pass_model_and_token(status_confirm_by_callback, model, token),
                    pattern=r"^0301(0|1)$"
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return handler
