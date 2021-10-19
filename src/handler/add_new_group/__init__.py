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

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def add_group(update: Update, context: CallbackContext, model, token):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if next(iter(
            model.Group.select().where(
                model.Group.id == update.message.chat.id
                )
            ), False):
            update.message.reply_text(
                "your group is in my list! send to another one ツ"
            )
        # elif is_admin(update.message.chat.id, update.message.from_user.id, token):
        elif int(os.getenv("ADMIN", "0")) == update.message.from_user.id:
            new_group = model.Group.create(
                id = update.message.chat.id,
                username = update.message.chat.username or "",
                name = update.message.chat.title
            )
            new_group.save()
            new_lock = model.Locks.create(
                group = new_group,
                forward = False
            )
            new_lock.save()
            update.message.reply_text(
                "OK! I added your group to my groups list. now, return to the private chat to add command, enable futures, etc."
            )
        else:
            if not update.message.delete():
                update.message.reply_text(
                    "I'm not admin, and you'e not neither!"
                )
    else:
        update.message.reply_text(
            "please send this command in your group!"
        )

def creator(model, token):
    handler = CommandHandler("addgroup", pass_model_and_token(add_group, model, token))
    return handler