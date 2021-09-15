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
import html, json

GET_GROUP_FROM, GET_COMMAND, GET_GROUP_TO = range(3)
EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)
ASCII_ART = """\
(\____/)
( 0 ͜ ʖ0)
 \╭☞  \╭☞"""

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def start_process(update: Update, context: CallbackContext, model, token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        update.message.delete()
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0400"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of there groups to get a command to export to another group (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP_FROM

def state_get_group_from_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
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
    context.user_data["0400group_id"] = group_id
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these commands to export:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data="0400"+command.names) for name in json.loads(command.names)]
            for command in model.Group.get(model.Group.id == group_id).normal_commands
        ])
    )
    return GET_COMMAND

def state_get_command_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    command = next(iter(
        command
        for command in model.Group.get(
            model.Group.id == context.user_data["0400group_id"]
        ).normal_commands
        if command.names == query.data[4:]
    ), False)
    if not command:
        query.answer("command not found!")
        return GET_COMMAND
    query.answer()
    context.user_data["0400command"] = command
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0400"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, query.from_user.id, token)\
            and group.id != context.user_data["0400group_id"]
    ])
    query.edit_message_text(
        f"OK! so, select one to export commands {command.names} there:",
        reply_markup = keyboard
    )
    return GET_GROUP_TO

def state_get_group_to_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
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
    command = context.user_data["0400command"]
    new_command = model.NormalCommand.create(
        group = model.Group.get(model.Group.id == group_id),
        names = command.names,
        text = command.text,
        delete_replied = command.delete_replied,
        admin_only = command.admin_only
    )
    new_command.save()
    name_group_from = model.Group.get(
        model.Group.id == context.user_data["0400group_id"]
    ).name
    name_group_to = model.Group.get(
        model.Group.id == group_id
    ).name
    query.edit_message_text(
        "done! command exported successfully!\n"
        f"<code>{html.escape(ASCII_ART)}</code>\n"
        f": from group: {html.escape(name_group_from)}\n"
        f": to group: {html.escape(name_group_to)}\n"
        ": command:\n"
        f"---: names: {command.names}\n"
        f"---: text: \n<code>{command.text}</code>\n"
        f"---: delete replied message: {[EMOJI_DISLIKE, EMOJI_LIKE][command.delete_replied]}\n"
        f"---: admin only: {[EMOJI_DISLIKE, EMOJI_LIKE][command.admin_only]}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([])
    )
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
    get_command_handler = ConversationHandler(
        entry_points=[
            CommandHandler("export", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP_FROM: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_from_by_callback, model, token), 
                    pattern=r'^0400-\d+$'
                )
            ],
            GET_COMMAND: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_command_by_callback, model, token),
                    pattern=r'0400.+'
                )
            ],
            GET_GROUP_TO: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_to_by_callback, model, token), 
                    pattern=r'^0400-\d+$'
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return get_command_handler
