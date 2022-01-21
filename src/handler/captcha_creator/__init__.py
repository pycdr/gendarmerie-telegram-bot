from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot,
    Message,
    ChatPermissions
)
from telegram.ext import (
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    Filters
)
import string, random, html, time
from captcha.image import ImageCaptcha
from io import BytesIO

VALID_CHARS = string.ascii_letters + string.digits

def generate_captcha(code: str) -> BytesIO:
    return ImageCaptcha().generate(code)

def auto_remove_function(message, user_id, chat_id, model):
    message.delete()
    del model.captcha[(user_id, chat_id)]

def start_captcha(update: Update, context: CallbackContext, model, token):
    update.message.delete()
    if update.message.left_chat_member:
        if (update.message.from_user.id, update.message.chat.id) in model.captcha:
            model.captcha[(update.message.from_user.id, update.message.chat.id)]["message"].delete()
        return
    if update.message.chat.id not in model.anti_spam_data:
        model.anti_spam_data[update.message.chat.id] = [(update.message.from_user.id, time.time())]
    else:
        model.anti_spam_data[update.message.chat.id].append((update.message.from_user.id, time.time()))
        if len(model.anti_spam_data[update.message.chat.id]) < 10:
            t = time.time()
            if t - model.anti_spam_data[update.message.chat.id][-1][1] < 1:
                model.anti_spam_data[update.message.chat.id].append((update.message.from_user.id, t))
            else:
                model.anti_spam_data[update.message.chat.id] = model.anti_spam_data[update.message.chat.id][-1:]
        else:
            d = model.anti_spam_data[update.message.chat.id][-1][1] - model.anti_spam_data[update.message.chat.id][0][1]
            if d <= 9:
                for user_id, _ in model.anti_spam_data[update.message.chat.id]:
                    context.bot.ban_chat_member(chat_id = update.message.chat.id, user_id = user_id)
                    model.captcha[(user_id, update.message.chat.id)]["message"].delete()
                model.anti_spam_data[update.message.chat.id].clear()
            else:
                del model.anti_spam_data[update.message.chat.id][0]
    context.bot.restrict_chat_member(
        chat_id = update.message.chat.id,
        user_id = update.message.from_user.id,
        until_date = time.time(),
        permissions = ChatPermissions(False, False, False, False, False, False, False, False)
    )
    result = "".join(random.sample(VALID_CHARS, 6))
    while result in ("remove", "unlock"):
        result = "".join(random.sample(VALID_CHARS, 6))
    image = generate_captcha(result)
    wrong_answers = ["".join(random.sample(VALID_CHARS, 6)) for _ in range(5)]
    for i in range(5):
        while wrong_answers[i] in ("remove", "unlock"):
            wrong_answers[i] = "".join(random.sample(VALID_CHARS, 6))
    text =  "سلام " + \
            f"<a href=\"tg://user?id={update.message.from_user.id}\">{html.escape(update.message.from_user.full_name)}</a>" + \
            " شما ۱۵ دقیقه وقت دارید تا به #کپچا جواب بدهید!"
    button_list = [
        [
            InlineKeyboardButton(wrong_answers[0], callback_data = wrong_answers[0]+str(update.message.from_user.id)),
            InlineKeyboardButton(wrong_answers[1], callback_data = wrong_answers[1]+str(update.message.from_user.id)),
            InlineKeyboardButton(wrong_answers[2], callback_data = wrong_answers[2]+str(update.message.from_user.id))
        ],
        [
            InlineKeyboardButton(wrong_answers[3], callback_data = wrong_answers[3]+str(update.message.from_user.id)),
            InlineKeyboardButton(wrong_answers[4], callback_data = wrong_answers[4]+str(update.message.from_user.id)),
            InlineKeyboardButton(result, callback_data = result+str(update.message.from_user.id))
        ]
    ]
    random.shuffle(button_list[0])
    random.shuffle(button_list[1])
    random.shuffle(button_list)
    new_message = context.bot.send_photo(
        chat_id = update.message.chat.id,
        photo = image,
        caption = text,
        reply_markup = InlineKeyboardMarkup(
            button_list+[[
                InlineKeyboardButton("remove ❌", callback_data="remove"+str(update.message.from_user.id)),
                InlineKeyboardButton("unlock 🔓", callback_data="unlock"+str(update.message.from_user.id))
            ]]
        ),
        parse_mode = "HTML"
    )
    permissions = context.bot.get_chat(
        chat_id = update.message.chat.id
    ).permissions
    model.captcha[(update.message.from_user.id, update.message.chat.id)] = {
        "result": result,
        "message": new_message,
        "user_id": update.message.from_user.id,
        "chat_id": update.message.chat.id,
        "permissions": permissions,
        "job": context.job_queue.run_once(
            (lambda _: auto_remove_function(
                message = new_message,
                user_id = update.message.from_user.id,
                chat_id = update.message.chat.id,
                model = model
            )),
            900,
            context = context
        ),
        "locks": 3 # if it becomes zero, the user will be removed!
    }

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    return MessageHandler(
        Filters.status_update.new_chat_members | Filters.status_update.left_chat_member,
        pass_model_and_token(start_captcha, model=model, token=token)
    )
