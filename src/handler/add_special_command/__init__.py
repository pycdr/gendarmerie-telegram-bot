import re, json, html
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot,
    message
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters,
    conversationhandler
)
from telegram.keyboardbutton import KeyboardButton

GET_GROUP, GET_TYPE, GET_GOOGLING_REGEX, GET_GOOGLING_TEXT, GET_DICTIONARY_REGEX, GET_DICTIONARY_DATA, GET_DICTIONARY_TEXT, DELETE_REPLIED, ADMIN_ONLY = range(9)
TYPE_GOOGLING, TYPE_DICT = range(2)
EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def start_process(update: Update, context: CallbackContext, model, token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        Bot(token).delete_message(
            update.message.chat.id,
            update.message.message_id
        )
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0002"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to add special command (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP

def get_group_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    try:
        group_id = int(query.data[4:])
    except ValueError:
        query.answer("invalid group id!")
        return ConversationHandler.END
    if not next(iter(model.Group.select().where(model.Group.id == group_id)), False):
        query.answer("group doesn't exists anymore, maybe in my list! add with /add command.")
        return ConversationHandler.END
    if not is_admin(group_id, query.from_user.id, token):
        query.answer("you are not admin!!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0002group_id"] = group_id
    query.edit_message_text(
        "OK! now, select one of these options for your special command: ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("googling mode (with bmbgk.ir)", callback_data="0002"+str(TYPE_GOOGLING))],
            [InlineKeyboardButton("dictionary mode", callback_data="0002"+str(TYPE_DICT))]
        ])
    )
    return GET_TYPE

def get_type_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    try:
        type_id = int(query.data[4:])
        if type_id not in range(2):
            query.answer("invalid type id!")
            return ConversationHandler.END
    except ValueError:
        query.answer("invalid type id!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0002type_id"] = type_id
    if type_id == TYPE_GOOGLING:
        context.user_data["0002data"] = None
        query.edit_message_text(
            "Fine! so, tell me how is your regular expression for it? (the [first] group in your RE will be selected as URL query)",
            reply_markup=InlineKeyboardMarkup([])
        )
        return GET_GOOGLING_REGEX
    elif type_id == TYPE_DICT:
        query.edit_message_text(
            "Fine! so, tell me how is your regular expression for it? (the [first] group in your RE will be selected as dictionary key)",
            reply_markup=InlineKeyboardMarkup([])
        )
        return GET_DICTIONARY_REGEX

def get_googling_regex_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    context.user_data["0002regex"] = update.message.text
    update.message.reply_text(
        "OK! so, tell me the message, which will be sent to the mentioned user\n"
        "use {googling_url} to put the generated URL.\n"\
        "also, you can use {user_mention} to mention the user"
    )
    return GET_GOOGLING_TEXT

def get_googling_text_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    context.user_data["0002text"] = update.message.text
    update.message.reply_text(
        "OK, so tell me should i delete the message, which the command is replying it?\n"\
        "*don't worry! it won't work for normal users*",
        reply_markup=ReplyKeyboardMarkup([
            [EMOJI_LIKE, EMOJI_DISLIKE]
        ])
    )
    return DELETE_REPLIED

def get_dict_regex_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    context.user_data["0002regex"] = update.message.text
    update.message.reply_text(
        "OK! so, tell me the message, which will be sent to the mentioned user\n"
        "use {dict_key} to put the key, and {dict_value} for value\n"\
        "also, you can use {user_mention} to mention the user"
    )
    return GET_DICTIONARY_TEXT

def get_dict_text_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    context.user_data["0002text"] = update.message.text
    update.message.reply_text(
        "OK! now, send me the dictionary data, like this:\n"
        "key1:value1\n"
        "key2:value2\n"
        "...",
        reply_markup=ReplyKeyboardMarkup([])
    )
    return GET_DICTIONARY_DATA

def get_dict_data_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    res = re.findall(r'([ \w]+:[ \w]+)+', update.message.text)
    res_dict = {
        key.strip(): value.strip()
        for key, value in (
            items.split(':')
            for items in res
        )
    }
    context.user_data["0002data"] = json.dumps(res_dict)
    update.message.reply_text(
        "OK! i catched this data:\n"
        f"{chr(10).join(map(':'.join, res_dict.items()))}\n"
        "if it's not what you want, skip the task with /cancel and try again!\n"
        "otherwise, tell me should i delete the message, which the command is replying it?\n"\
        "*don't worry! it won't work for normal users*",
        reply_markup=ReplyKeyboardMarkup([
            [EMOJI_LIKE, EMOJI_DISLIKE]
        ])
    )
    return DELETE_REPLIED

def status_get_delete_replied(update: Update, context: CallbackContext, model, token: str) -> int:
    text = update.message.text
    if text not in (EMOJI_LIKE, EMOJI_DISLIKE):
        update.message.reply_text(
            "Invalid message! please choose from the keyboard"
        )
        return DELETE_REPLIED
    context.user_data["0002delete_replied"] = [EMOJI_DISLIKE, EMOJI_LIKE].index(text)
    update.message.reply_text(
        "OK! as the last question: is/are the command(s) just for admins or not?",
        reply_markup=ReplyKeyboardMarkup([
            [EMOJI_LIKE, EMOJI_DISLIKE]
        ])
    )
    return ADMIN_ONLY

def status_get_admin_only(update: Update, context: CallbackContext, model, token: str):
    text = update.message.text
    if text not in (EMOJI_LIKE, EMOJI_DISLIKE):
        update.message.reply_text(
            "Invalid message! please choose from the keyboard"
        )
        return DELETE_REPLIED
    context.user_data["0002admin_only"] = [EMOJI_DISLIKE, EMOJI_LIKE].index(text)
    # add to model:
    type_id = context.user_data["0002type_id"]
    group_id = context.user_data["0002group_id"]
    regex = context.user_data["0002regex"]
    data = context.user_data["0002data"]
    text = context.user_data["0002text"]
    delete_replied = context.user_data["0002delete_replied"]
    admin_only = context.user_data["0002admin_only"]
    new_special_command = model.SpecialCommand(
        type_id = type_id,
        group = model.Group.get(model.Group.id == group_id),
        regex = regex,
        data = data,
        text = text,
        delete_replied = delete_replied,
        admin_only = admin_only
    )
    new_special_command.save()
    update.message.reply_text(
        f"done! your special command details:\n"
        f"group: {html.escape(new_special_command.group.name)}\n"
        f"regex: {html.escape(regex)}\n"
        f"data: {html.escape(str(json.loads(data)) if data else 'NOTHING!')}\n"
        f"text:\n"
        f"<code>{html.escape(text)}</code>\n"
        f"delete replied message: {[EMOJI_DISLIKE, EMOJI_LIKE][new_special_command.delete_replied]}\n"
        f"admin only: {[EMOJI_DISLIKE, EMOJI_LIKE][new_special_command.admin_only]}",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END

def cancel_process(update: Update, context: CallbackContext):
    context.user_data.clear()
    update.message.reply_text(
        "canceled."
    )
    return ConversationHandler.END

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    add_special_command_handler = ConversationHandler(
        entry_points=[
            CommandHandler("addspecial", pass_model_and_token(start_process, model, token)),
            CommandHandler("newspecial", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(get_group_by_callback, model, token),
                    pattern=r'^0002-\d+$'
                )
            ],
            GET_TYPE: [
                CallbackQueryHandler(
                    pass_model_and_token(get_type_by_callback, model, token),
                    pattern=r'^0002(0|1)$'
                )
            ],
            GET_GOOGLING_REGEX: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_googling_regex_by_message, model, token)
                )
            ],
            GET_DICTIONARY_REGEX: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_dict_regex_by_message, model, token)
                )
            ],
            GET_GOOGLING_TEXT: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_googling_text_by_message, model, token)
                )
            ],
            GET_DICTIONARY_TEXT: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_dict_text_by_message, model, token)
                )
            ],
            GET_DICTIONARY_DATA: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(get_dict_data_by_message, model, token)
                )
            ],
            DELETE_REPLIED: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(status_get_delete_replied, model, token)
                )
            ],
            ADMIN_ONLY: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    pass_model_and_token(status_get_admin_only, model, token)
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return add_special_command_handler