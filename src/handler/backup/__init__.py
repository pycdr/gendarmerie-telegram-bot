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
import os

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def backup(update: Update, context: CallbackContext, model, token):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        update.message.delete()
        return
    admin_id = int(os.getenv("ADMIN", "0"))
    if admin_id == update.message.from_user.id:
        update.message.reply_text(
            "OK! wait a little..."
        ).reply_document(
            open("./groups.db", 'rb')
        ).reply_document(
            open("./commands.db", 'rb')
        ).reply_document(
            open("./users.db", 'rb')
        )
    else:
        update.message.reply_text("0`_´0")

def creator(model, token):
    handler = CommandHandler("backup", pass_model_and_token(backup, model, token))
    return handler
