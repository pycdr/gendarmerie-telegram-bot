from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ChatMember,
    Chat,
    Bot
)
from telegram.ext import (
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    Filters
)
import html, re, json
from urllib.parse import urlencode

TYPE_GOOGLING, TYPE_DICT = range(2)

def is_admin(chat_id: int, user_id: int, token: str):
    return Bot(token).get_chat_member(chat_id, user_id).status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR)

def handler(update: Update, context: CallbackContext, model, token: str):
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        command = next((
            command
            for command in model.Group.get(
                model.Group.id == update.message.chat.id
            ).normal_commands
            if update.message.text in json.loads(command.names)
        ), False)
        if command:
            text = command.text
            delete_replied = command.delete_replied
            admin_only = command.admin_only
            Bot(token).delete_message(update.message.chat.id, update.message.message_id)
            res = html.escape(text).format(
                user_mention = f"<a href=\"tg://user?id={update.message.reply_to_message.from_user.id}\">{update.message.reply_to_message.from_user.full_name}</a>"
            )
            if is_admin(update.message.chat.id, update.message.from_user.id, token):
                if delete_replied:
                    Bot(token).delete_message(update.message.chat.id, update.message.reply_to_message.message_id)
                    Bot(token).send_message(
                        update.message.chat.id,
                        res,
                        parse_mode = "HTML"
                    )
                else:
                    update.message.reply_to_message.reply_text(
                        res,
                        parse_mode = "HTML"
                    )
            else:
                if admin_only:
                    return
                else:
                    update.message.reply_to_message.reply_text(
                        res,
                        parse_mode = "HTML"
                    )
        else:
            res = next(iter(
                command
                for command in model.Group.get(model.Group.id == update.message.chat.id).special_commands
                if re.match(command.regex, update.message.text)
            ), False)
            if res:
                type_id = res.type_id
                group_id = res.group.id
                regex = res.regex
                data = res.data
                text = res.text
                delete_replied = res.delete_replied
                admin_only = res.admin_only
                if type_id == TYPE_GOOGLING:
                    groups = re.match(regex, update.message.text).groups()
                    if groups:
                        search_text = groups[0]
                        url = f"http://bmbgk.ir/?{urlencode({'q': search_text})}"
                        res = html.escape(text).format(
                            googling_url = url,
                            user_mention = f"<a href=\"tg://user?id={update.message.reply_to_message.from_user.id}\">{update.message.reply_to_message.from_user.full_name}</a>"
                        )
                elif type_id == TYPE_DICT:
                    groups = re.match(regex, update.message.text).groups()
                    if groups:
                        dict_key = groups[0]
                        data = json.loads(data)
                        dict_value = data.get(dict_key, "NOT FOUND!")
                        res = res = html.escape(text).format(
                            dict_key = dict_key,
                            dict_value = dict_value,
                            user_mention = f"<a href=\"tg://user?id={update.message.reply_to_message.from_user.id}\">{update.message.reply_to_message.from_user.full_name}</a>"
                        )
                Bot(token).delete_message(update.message.chat.id, update.message.message_id)
                if is_admin(update.message.chat.id, update.message.from_user.id, token):
                    if delete_replied:
                        Bot(token).delete_message(update.message.chat.id, update.message.reply_to_message.message_id)
                        Bot(token).send_message(
                            update.message.chat.id,
                            res,
                            parse_mode = "HTML"
                        )
                    else:
                        update.message.reply_to_message.reply_text(
                            res,
                            parse_mode = "HTML"
                        )
                else:
                    if admin_only:
                        return
                    else:
                        update.message.reply_to_message.reply_text(
                            res,
                            parse_mode = "HTML"
                        )
