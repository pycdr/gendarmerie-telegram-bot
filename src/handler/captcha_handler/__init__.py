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
import time

def confirm_captcha(update: Update, context: CallbackContext, model, token):
    query = update.callback_query
    code = query.data[:6]
    try:
        user_id = int(query.data[6:])
    except ValueError:
        query.answer("invalid query!")
        return
    if code == "remove":
        if context.bot.get_chat_member(
            chat_id = query.message.chat.id,
            user_id = query.from_user.id).status not in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR):
            query.answer("(ಠ_ಠ)")
            return
        context.bot.ban_chat_member(
            chat_id = query.message.chat.id,
            user_id = user_id
        )
        model.captcha[(user_id, query.message.chat.id)]["job"].schedule_removal()
        model.captcha[(user_id, query.message.chat.id)]["message"].delete()
        del model.captcha[(user_id, query.message.chat.id)]
        return
    if code == "unlock":
        if context.bot.get_chat_member(
            chat_id = query.message.chat.id,
            user_id = query.from_user.id).status not in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR):
            query.answer("(ಠ_ಠ)")
            return
        context.bot.restrict_chat_member(
            chat_id = query.message.chat.id,
            user_id = user_id,
            until_date = time.time()+10e10,
            permissions = model.captcha[(user_id, query.message.chat.id)]["permissions"]
        )
        model.captcha[(user_id, query.message.chat.id)]["job"].schedule_removal()
        model.captcha[(user_id, query.message.chat.id)]["message"].delete()
        del model.captcha[(user_id, query.message.chat.id)]
        return
    if user_id != query.from_user.id:
        query.answer("(ಠ_ಠ)")
        return
    if code == model.captcha[(user_id, query.message.chat.id)]["result"]:
        query.answer("Correct!")
        print(model.captcha[(user_id, query.message.chat.id)]["permissions"])
        context.bot.restrict_chat_member(
            chat_id = query.message.chat.id,
            user_id = user_id,
            until_date = time.time()+10e10,
            permissions = model.captcha[(user_id, query.message.chat.id)]["permissions"]
        )
        model.captcha[(user_id, query.message.chat.id)]["job"].schedule_removal()
        model.captcha[(user_id, query.message.chat.id)]["message"].delete()
        del model.captcha[(user_id, query.message.chat.id)]
        return
    else:
        model.captcha[(user_id, query.message.chat.id)]["locks"] -= 1
        if model.captcha[(user_id, query.message.chat.id)]["locks"] > 0:
            query.answer(f"Wrong! you have still {model.captcha[(user_id, query.message.chat.id)]['locks']} lock(s)!")
            return
        else:
            query.answer("GOODBYE ROBOT!")
            context.bot.ban_chat_member(
                chat_id = model.captcha[(user_id, query.message.chat.id)]["message"].chat.id,
                user_id = user_id
            )
            model.captcha[(user_id, query.message.chat.id)]["job"].schedule_removal()
            model.captcha[(user_id, query.message.chat.id)]["message"].delete()
            del model.captcha[(user_id, query.message.chat.id)]
            return 

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    return CallbackQueryHandler(
        pass_model_and_token(confirm_captcha, model, token),
        pattern=r'[0-9a-zA-Z]{6}[0-9]+'
    )
