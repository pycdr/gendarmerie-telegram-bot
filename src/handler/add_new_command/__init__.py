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
    Filters
)
import json, html

GET_GROUP, GET_COMMANDS, GET_TEXT, DELETE_REPLIED, ADMIN_ONLY = range(5)

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
            callback_data=str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to add normal command (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP

def state_get_group_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    try:
        group_id = int(query.data)
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
    context.user_data["group_id"] = group_id
    query.edit_message_text(
        "OK! now, send you command. just use normal characters."
        "also, each line you write is a command itself. like:\n"
        "command1\n"
        "command2\n"
        "...",
        reply_markup=InlineKeyboardMarkup([])
    )
    return GET_COMMANDS

def status_get_commands_by_message(update: Update, context: CallbackContext, model, token: str) -> int:
    commands = [*map(str.lower, update.message.text.split("\n"))]
    context.user_data["commands"] = commands
    if any(
            command in json.loads(cmd.names) for cmd in model.Group.get(
                model.Group.id == context.user_data["group_id"]
            ).normal_commands
            for command in commands
        ):
        update.message.reply_text(
            "you have defined one/some of these commands! please send another(s):"
        )
        return GET_COMMANDS
    update.message.reply_text(
        "now, send me the command text\n"
        "there are some futures for you that you can put in the text:\n"
        "{user_mention}: puts the user mention with its name\n"
    )
    return GET_TEXT

def status_get_text_by_message(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data["text"] = text
    update.message.reply_text(
        "OK, so tell me should i delete the message, which the command is replying it?\n"\
        "*don't worry! it won't work for normal users*",
        reply_markup=ReplyKeyboardMarkup([
            [EMOJI_LIKE, EMOJI_DISLIKE]
        ])
    )
    return DELETE_REPLIED

def status_get_delete_replied(update: Update, context: CallbackContext):
    text = update.message.text
    if text not in (EMOJI_LIKE, EMOJI_DISLIKE):
        update.message.reply_text(
            "Invalid message! please choose from the keyboard"
        )
        return DELETE_REPLIED
    context.user_data["delete_replied"] = [EMOJI_DISLIKE, EMOJI_LIKE].index(text)
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
        return ADMIN_ONLY
    context.user_data["admin_only"] = [EMOJI_DISLIKE, EMOJI_LIKE].index(text)
    new_command = model.NormalCommand(
        group = model.Group.get(model.Group.id == context.user_data["group_id"]),
        names = json.dumps(context.user_data["commands"]),
        text = context.user_data["text"],
        delete_replied = bool(context.user_data["delete_replied"]),
        admin_only = bool(context.user_data["admin_only"])
    )
    new_command.save()
    update.message.reply_text(
        f"done! your nromal command details:\n"
        f"group: {html.escape(new_command.group.name)}\n"
        f"names: {html.escape(','.join(context.user_data['commands']))}\n"
        f"text:\n"
        f"<code>{html.escape(new_command.text)}</code>\n"
        f"delete replied message: {[EMOJI_DISLIKE, EMOJI_LIKE][new_command.delete_replied]}\n"
        f"admin only: {[EMOJI_DISLIKE, EMOJI_LIKE][new_command.admin_only]}",
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

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    add_new_command_handler = ConversationHandler(
        entry_points=[
            CommandHandler("addcommand", pass_model_and_token(start_process, model, token)),
            CommandHandler("newcommand", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_by_callback, model, token), 
                    pattern=r'^-\d+$'
                )
            ],
            GET_COMMANDS: [
                MessageHandler(
                    Filters.text,
                    pass_model_and_token(status_get_commands_by_message, model, token)
                )
            ],
            GET_TEXT: [
                MessageHandler(
                    Filters.text,
                    status_get_text_by_message
                )
            ],
            DELETE_REPLIED: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    status_get_delete_replied
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
        ],
        allow_reentry = True
    )
    return add_new_command_handler
