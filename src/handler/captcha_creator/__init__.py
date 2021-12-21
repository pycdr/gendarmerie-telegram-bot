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

def start_captcha(update: Update, context: CallbackContext, model, token):
    update.message.delete()
    if update.message.left_chat_member:
        if (update.message.from_user.id, update.message.chat.id) in model.captcha:
            model.captcha[(update.message.from_user.id, update.message.chat.id)]["message"].delete()
    #chat_member = context.bot.get_chat_member(
    #    chat_id = update.message.chat.id,
    #    user_id = update.message.from_user.id
    #)
    permissions = ChatPermissions(
        can_send_messages = True, #chat_member.can_send_messages,
        can_send_media_messages = True, #chat_member.can_send_media_messages,
        can_send_polls = False, #chat_member.can_send_polls,
        can_send_other_messages = False, #chat_member.can_send_other_messages,
        can_add_web_page_previews = True, #chat_member.can_add_web_page_previews,
        can_change_info = False, #chat_member.can_change_info,
        can_invite_users = False, #chat_member.can_invite_users,
        can_pin_messages = False, #chat_member.can_pin_messages
    )
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
    text =  "hello " + \
            f"<a href=\"tg://user?id={update.message.from_user.id}\">{html.escape(update.message.from_user.full_name)}</a>" + \
            "! You have 15 minutes to answer the #captcha"
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
    model.captcha[(update.message.from_user.id, update.message.chat.id)] = {
        "result": result,
        "message": new_message,
        "user_id": update.message.from_user.id,
        "permissions": permissions,
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
