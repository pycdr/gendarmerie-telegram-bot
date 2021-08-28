from telegram import Update
from telegram.ext import (
    CallbackContext,
    Filters,
    MessageHandler
)

from .locks import handler as locks_handler
from .commands import handler as commands_handler

HANDLERS = (
    locks_handler,
    commands_handler
)

def main_handle(update: Update, context: CallbackContext, model, token):
    for handler in HANDLERS:
        handler(update, context, model, token)

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    handle_added_group_commands_handler = MessageHandler(
        Filters.text & ~Filters.command,
        pass_model_and_token(main_handle, model=model, token=token)
    )
    return handle_added_group_commands_handler
