from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot,
    Message
)
from telegram.ext import (
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    Filters
)


def main_handle(update: Update, context: CallbackContext, model, token):
    update.message.delete()

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    handle_added_group_commands_handler = MessageHandler(
        Filters.status_update.new_chat_members | Filters.status_update.left_chat_member,
        pass_model_and_token(main_handle, model=model, token=token)
    )
    return handle_added_group_commands_handler
