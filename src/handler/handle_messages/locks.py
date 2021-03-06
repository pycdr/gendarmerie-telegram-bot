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

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def forward_lock(message: Message, delete):
    if (message.forward_from_chat or message.forward_from) and (message.from_user.id != getattr(message.forward_from, "id", None)):
        delete()
        return True

def handler(update: Update, context: CallbackContext, model, token: str):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if not (
            is_admin(update.message.chat.id, update.message.from_user.id, token) or \
            update.message.from_user.id in (1087968824, 777000) # GroupAnonymousBot and Telegram :)
        ):
            group = model.Group.get(model.Group.id == update.message.chat.id)
            if group.locks[0].forward and forward_lock(
                    message = update.message,
                    delete = update.message.delete
                ):
                return True
