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
from threading import Thread
import time

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def is_creator(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.CREATOR,)

def score_count(text: str) -> int:
    if all(x=="+" for x in text):
        return min(len(text), 4)
    elif all(x=="-" or x=="—" for x in text):
        return -min(text.count("-")+text.count("—")*2, 4)
    return 0

def generate_text(score: int, name: str, result: int) -> str:
    return  f">>> score[{repr(name)}] {'+' if score>0 else '-'}= {score}\n"\
            f">>> score[{repr(name)}]\n"\
            f"{result}"

messages_for_deletion = []
SLEEP_TIME = 10
def thread_func():
    while 1:
        current_time = time.time()
        for message, s_time in messages_for_deletion:
            if current_time-s_time >= SLEEP_TIME:
                message.delete()
                messages_for_deletion.remove((message, s_time))
        time.sleep(1)
deletion_thread = Thread(target = thread_func)
deletion_thread.start()

def handler(update: Update, context: CallbackContext, model, token: str):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        if update.message.reply_to_message:
            if is_admin(update.message.chat.id, update.message.from_user.id, token):
                score_value = score_count(update.message.text)
                if not score_value:
                    return
                if is_admin(
                    update.message.reply_to_message.chat.id,
                    update.message.reply_to_message.from_user.id,
                    token
                ) and not is_creator(
                    update.message.chat.id,
                    update.message.from_user.id,
                    token
                ):
                    update.message.delete()
                    return
                group = model.Group.get(model.Group.id == update.message.chat.id)
                user = next(iter(
                    user for user in group.users
                    if user.id == update.message.reply_to_message.from_user.id
                ), None)
                if not user:
                    user = model.User.create(
                        id = update.message.reply_to_message.from_user.id,
                        name = update.message.reply_to_message.from_user.full_name,
                        group = group,
                        score = score_value,
                        ban = False,
                        banned_with_message = None
                    )
                    user.save()
                else:
                    user.score += score_value
                    user.save()
                update.message.delete()
                text = generate_text(
                    score_value,
                    update.message.reply_to_message.from_user.full_name,
                    user.score
                )
                res = update.message.reply_to_message.reply_text(
                    f"<code>{html.escape(text)}</code>",
                    parse_mode="HTML"
                )
                messages_for_deletion.append((res, time.time()))
                return True
                