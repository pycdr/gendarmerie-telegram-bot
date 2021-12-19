import html
import json

from telegram import (Bot, Chat, ChatMember, InlineKeyboardButton,
                      InlineKeyboardMarkup, Update,)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler,)

GET_GROUP, GET_COMMAND, GET_BACK = range(3)
EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)


def is_joined(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(
        chat_id,
        user_id).status in (
        ChatMember.ADMINISTRATOR,
        ChatMember.CREATOR,
        ChatMember.MEMBER)


def start_process(
        update: Update,
        context: CallbackContext,
        model,
        token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        Bot(token).delete_message(
            update.message.chat.id,
            update.message.message_id
        )
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=group.name,
            callback_data="0102" + str(group.id)
        )]
        for group in model.Group.select()
        if is_joined(group.id, update.message.from_user.id, token)
    ])
    update.message.reply_text(
        "OK! choose one of your groups to watch command (if there's any! :D)",
        reply_markup=keyboard
    )
    return GET_GROUP


def state_get_group_by_callback(
        update: Update,
        context: CallbackContext,
        model,
        token: str) -> int:
    query = update.callback_query
    try:
        group_id = int(query.data[4:])
    except ValueError:
        query.answer("invalid group id!")
        return ConversationHandler.END
    if not next(
            iter(
                model.Group.select().where(
                    model.Group.id == group_id)),
            False):
        query.answer("group doesn't exists anymore, maybe in my list!")
        return ConversationHandler.END
    if not is_joined(group_id, query.from_user.id, token):
        query.answer("you are kicked, restricted or left!")
        return ConversationHandler.END
    query.answer()
    context.user_data["0102group_id"] = group_id
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these commands:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data="0102" + command.names) for name in json.loads(command.names)]
            for command in model.Group.get(model.Group.id == group_id).normal_commands
            if not command.admin_only
        ] + [[InlineKeyboardButton("back to the previous menu", callback_data="0102" + 'GET_BACK')]])
    )
    return GET_COMMAND


def state_get_command_by_callback(
        update: Update,
        context: CallbackContext,
        model,
        token: str) -> int:
    query = update.callback_query
    if query.data[4:] != "GET_BACK":
        group_id = context.user_data["0102group_id"]
        command = next(
            command
            for command in model.NormalCommand.select().where(
                model.NormalCommand.names == query.data[4:])
            if command.group.id == group_id)
        query.answer()
        text = command.text
        delete_replied = command.delete_replied
        admin_only = command.admin_only
        query.edit_message_text(
            f"here are the details for commands {command.names} for group \"{command.group.name}\":\n"
            f"text: \n<code>{html.escape(text)}</code>\n",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton(
                        "back to the commands",
                        callback_data="0102" + 'GET_BACK')]]))
        return GET_BACK
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=group.name,
                callback_data="0102" + str(group.id)
            )]
            for group in model.Group.select()
            if is_joined(group.id, (update.message or update.callback_query).from_user.id, token)
        ])
        query.edit_message_text(
            "OK! choose one of your groups to get command details (if there's any! :D)",
            reply_markup=keyboard)
        return GET_GROUP


def state_get_back_by_callback(
        update: Update,
        context: CallbackContext,
        model,
        token: str) -> int:
    query = update.callback_query
    query.answer()
    group_id = context.user_data["0102group_id"]
    query.edit_message_text(
        f"OK! for group \"{model.Group.get(model.Group.id == group_id).name}\", select one of these commands:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data="0102" + command.names) for name in json.loads(command.names)]
            for command in model.Group.get(model.Group.id == group_id).normal_commands
            if not command.admin_only
        ] + [[InlineKeyboardButton("back to the previous menu", callback_data="0102" + 'GET_BACK')]])
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
        return function(
            update=update,
            context=context,
            model=model,
            token=token)
    return wrapper


def creator(model, token):
    get_command_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "watch",
                pass_model_and_token(
                    start_process,
                    model,
                    token))],
        states={
            GET_GROUP: [
                CallbackQueryHandler(
                    pass_model_and_token(
                        state_get_group_by_callback,
                        model,
                        token),
                    pattern=r'^0102-\d+$')],
            GET_COMMAND: [
                CallbackQueryHandler(
                    pass_model_and_token(
                        state_get_command_by_callback,
                        model,
                        token),
                    pattern=r'0102.+')],
            GET_BACK: [
                CallbackQueryHandler(
                    pass_model_and_token(
                        state_get_back_by_callback,
                        model,
                        token),
                    pattern='0102GET_BACK')]},
        fallbacks=[
            CommandHandler(
                "cancel",
                cancel_process)])
    return get_command_handler
