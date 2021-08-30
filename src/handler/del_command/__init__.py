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

GET_GROUP, GET_COMMAND, GET_BACK = range(3)
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
            callback_data="0200"+str(group.id)
        )]
        for group in model.Group.select()
        if is_admin(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to delete some of its commands (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP

def state_get_group_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
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
    context.user_data["0200group_id"] = group_id
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these commands to remove all of **commands in row**:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data = "0200"+command.names) for name in json.loads(command.names)]
            for command in model.Group.get(model.Group.id == group_id).normal_commands
        ] + [[InlineKeyboardButton("back to the previous menu", callback_data="0200"+'GET_BACK')]])
    )
    return GET_COMMAND

def state_get_command_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    if query.data[4:] != "GET_BACK":
        group_id = context.user_data["0200group_id"]
        command = next(command for command in model.NormalCommand.select().where(
            model.NormalCommand.names == query.data[4:]
        ) if command.group.id == group_id)
        query.answer()
        names = command.names
        group_name = command.group.name
        command.delete_instance()
        query.edit_message_text(
            f"commands {names} are removed for group {group_name}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("back to the commands", callback_data="0200"+'GET_BACK')]])
        )
        return GET_BACK
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0200"+str(group.id)
            )]
            for group in model.Group.select()
            if is_admin(group.id, (update.message or update.callback_query).from_user.id, token)
        ])
        query.edit_message_text(
            "OK! choose one of your groups to delete some of its commands (if there's any! :D)",
            reply_markup=keyboard
        )
        return GET_GROUP 

def state_get_back_by_callback(update: Update, context: CallbackContext, model, token: str) -> int:
    query = update.callback_query
    query.answer()
    group_id = context.user_data["0200group_id"]
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these commands:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data = "0200"+command.names) for name in json.loads(command.names)]
            for command in model.Group.get(model.Group.id == group_id).normal_commands
        ] + [[InlineKeyboardButton("back to the previous menu", callback_data="0200"+'GET_BACK')]])
    )
    return GET_COMMAND

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
    del_command_handler = ConversationHandler(
        entry_points=[
            CommandHandler("delcommand", pass_model_and_token(start_process, model, token))
        ],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_group_by_callback, model, token), 
                    pattern=r'^0200-\d+$'
                )
            ],
            GET_COMMAND: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_command_by_callback, model, token),
                    pattern=r'0200.+'
                )
            ],
            GET_BACK: [
                CallbackQueryHandler(
                    pass_model_and_token(state_get_back_by_callback, model, token),
                    pattern='0200GET_BACK'
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_process)
        ]
    )
    return del_command_handler
