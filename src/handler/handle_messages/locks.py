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
    if message.forward_from or message.forward_from_chat or message.forward_from_message_id:
        delete()

def handler(update: Update, context: CallbackContext, model, token: str):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if not is_admin(update.message.chat.id, update.message.from_user.id, token):
            if model.Group.get(model.Group.id == update.message.chat.id).locks[0].forward:
                forward_lock(
                    message = update.message,
                    delete = update.message.delete
                )
                return True
