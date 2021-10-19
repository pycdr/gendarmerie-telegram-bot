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
import html

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def count(text: str) -> int:
    if all(x=="+" for x in text):
        return len(text)
    return 0

def generate_text(score: int, name: str, result: int) -> str:
    return  f">>> users[{repr(name)}] += {score}\n"\
            f">>> users[{repr(name)}]\n"\
            f"{result}"

def handler(update: Update, context: CallbackContext, model, token: str):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if update.message.reply_to_message:
            if is_admin(update.message.chat.id, update.message.from_user.id, token):
                score_count = count(update.message.text)
                if not score_count:
                    return
                group = model.Group.get(model.Group.id == update.message.chat.id)
                user = next(iter(
                    user for user in group.user
                    if user.id == update.message.from_user.id
                ), None)
                if not user:
                    user = model.User.create(
                        id = update.message.reply_to_message.from_user.id,
                        group = group,
                        score = score_count(update.message.text),
                        ban = False,
                        banned_with_message = None
                    )
                    user.save()
                else:
                    user.score += score_count
                update.message.delete()
                text = generate_text(
                    score_count,
                    update.message.reply_to_message.from_user.full_name,
                    user.score
                )
                update.message.reply_to_message.reply_text(
                    f"<code>{html.escape(text)}</code>",
                    parse_mode="HTML"
                )
                return True
                