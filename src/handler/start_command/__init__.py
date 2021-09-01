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

PERMISSION_ERROR_DOC = """class PermissionError(OSError)
 |  Not enough permissions."""
GREEN = chr(128994)
BLUE = chr(128309)
RED = chr(128308)
PURPLE = chr(128995)
YELLOW = chr(128993)
DESCRIPTION = f"""{GREEN} /addgroup : send in your group, so i'll add it to my list, and i'll handle your group (with you, honey!)
{GREEN} /addcommand : send in PV, so we'll add a new command to your group
{GREEN} /addspecial : need a special command? so i'll suggest you some options with this command. just send in my PV!
{GREEN} /addfilter : add a new filter. send in PV.
{GREEN} /export : export commands from a group to another one.

{BLUE} /getcommand : just for admins! send in PV, and i'll show you command. then, you'll select one and i'll show you it details
{BLUE} /getspecial : like /getcommad , but for special commands
{BLUE} /getfilter : get the list of filters
{BLUE} /watch : like /getcommand, but for all users in a group. 

{RED} /delgroup : send in PV to remove your group from my list. really wanna do it?! :(
{RED} /delcommand : send in PV, and i'll show your command to remove some of them
{RED} /delspecial : like /delcommand , but ... you know the differences!
{RED} /delfilter : remove a filter from a group.

{PURPLE} /locks : we'll lock somethings (like forward messages), just send in PV

{YELLOW} /cancel : cancel any process and any command, whenever you wanna stop the task!
{YELLOW} /start : ಠ_ಠ"""

def handler(update: Update, context: CallbackContext, model, token: str) -> int:
    if update.message.chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        Bot(token).delete_message(
            update.message.chat.id,
            update.message.message_id
        )
        return
    update.message.reply_text(
        "Hi! I am PermissionError Bot! so, who am i?\n"
        f"<code>{PERMISSION_ERROR_DOC}</code>\n"
        "anyway! there's a list of my command. you can choose any of them, if you want, or if you have to!\n"
        f"{DESCRIPTION}",
        parse_mode="HTML"
    )
    

def pass_model_and_token(function, model, token):
    """this function is used to pass <Model> object"""
    def wrapper(update: Update, context: CallbackContext):
        return function(update=update, context=context, model=model, token=token)
    return wrapper

def creator(model, token):
    start_command_handler = CommandHandler(
        "start",
        pass_model_and_token(handler, model, token)
    )
    return start_command_handler
