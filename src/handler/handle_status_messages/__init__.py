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
    ConversationHandler,
    CallbackQueryHandler,
    Filters
)
import string, random, html
from captcha.image import ImageCaptcha
from io import BytesIO

VALID_CHARS = string.ascii_letters + string.digits

def generate_captcha(code: str) -> BytesIO:
    return ImageCaptcha().generate(code)

GET_CAPTCHA = range(1)

def auto_action(context: CallbackContext):
    user_id = context.job.context.user_data["captcha_delete_queue"]["user_id"]
    context.bot.ban_chat_member(                                chat_id = context.job.context.user_data["captcha_delete_queue"]["chat_id"],
        user_id = user_id)
    context.job.context.user_data["captcha"][user_id]["message"].delete()
    del context.job.context.user_data["captcha"][user_id]
    del context.job.context.user_data["captcha_delete_queue"]

def start_captcha(update: Update, context: CallbackContext, model, token):
    update.message.delete()
    if update.message.left_chat_member:
        return ConversationHandler.END
    result = "".join(random.sample(VALID_CHARS, 6))
    image = generate_captcha(result)
    wrong_answers = ["".join(random.sample(VALID_CHARS, 6)) for _ in range(5)]
    text =  "hello " + \
            f"<a href=\"tg://user?id={update.message.from_user.id}\">{html.escape(update.message.from_user.full_name)}</a>" + \
            "!\nplease enter text from the image."
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
        reply_markup = InlineKeyboardMarkup(button_list),
        parse_mode = "HTML"
    )

    if not "captcha" in context.user_data:
        context.user_data["captcha"] = {}

    #TODO: context.user_data is user exclusive; meaning that for every user, 
    # a unique instanse of CallbackContext object will be created and
    # referenced throughout their requests to the bot. therefore, 
    # it is unnecessary to use [user_id] as an indice in the context.user_data
    # object. This should be fixed for readability and simplisity improvement.

    context.user_data["captcha_delete_queue"] = {
            "chat_id": update.message.chat.id,
            "user_id": update.message.from_user.id
            } #Add parameters for simplisity and ease of access

    context.user_data["captcha"][update.message.from_user.id] = {
        "result": result,
        "message": new_message,
        "user_id": update.message.from_user.id,
        "locks": 3 # if it becomes zero, the user will be removed!
    }
    context.user_data["captcha_job"] = context.job_queue.run_once(auto_action, 30, context=context) # Add a job so that it would get fired up in 30seconds
    return GET_CAPTCHA

def confirm_captcha(update: Update, context: CallbackContext, model, token):
    query = update.callback_query
    code = query.data[:6]
    try:
        user_id = int(query.data[6:])
    except ValueError:
        query.answer("invalid query!")
        return GET_CAPTCHA
    # if you are watching this code, i wanna take an exam!
    # Q: why the following <if> statement won't be executed at all? 
    # good luck!
    if user_id != query.from_user.id:
        query.answer("(ಠ_ಠ)")
        return GET_CAPTCHA
    if code == context.user_data["captcha"][user_id]["result"]:
        query.answer("Correct!")
        context.user_data["captcha_job"].schedule_removal() # un-schedule auto ban job
        context.user_data["captcha"][user_id]["message"].delete()
        del context.user_data["captcha"][user_id]
        return ConversationHandler.END
    else:
        context.user_data["captcha"][user_id]["locks"] -= 1
        if context.user_data["captcha"][user_id]["locks"] > 0:
            query.answer(f"Wrong! you have still {context.user_data['captcha'][user_id]['locks']} lock(s)!")
            return GET_CAPTCHA
        else:
            query.answer("GOODBYE ROBOT!")
            context.bot.ban_chat_member(
                chat_id = context.user_data["captcha"][user_id]["message"].chat.id,
                user_id = user_id
            )
            context.user_data["captcha"][user_id]["message"].delete()
            del context.user_data["captcha"][user_id]
            del context.user_data["captcha_delete_queue"]
            return ConversationHandler.END

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    handle_added_group_commands_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.status_update.new_chat_members | Filters.status_update.left_chat_member,
                pass_model_and_token(start_captcha, model=model, token=token)
            )
        ],
        states={
            GET_CAPTCHA: [
                CallbackQueryHandler(
                    pass_model_and_token(confirm_captcha, model, token)
                )
            ]
        },
        fallbacks=[]
    )
    
    return handle_added_group_commands_handler
