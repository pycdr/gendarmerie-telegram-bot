import telebot
from rich.console import Console
from rich.progress import Progress
from pprint import pprint

from json import load
texts: dict = load(open("texts.json", 'r'))
	
class App:
	def __init__(self, token: str, **kwargs: dict):
		self.bot: telebot.TeleBot = telebot.TeleBot(token)
		self.bot_token: str = token
		self.admins_list: list = kwargs.get("admins", ())
		self.cli_console = Console()
		self.cli_console.rule("Bot object defined")
		self.cli_console.print("token:", self.bot_token)
	
	@property
	def token(self) -> str: return self.bot_token
	@token.setter
	def token(self, new_token) -> None:
		self.bot_token: str = new_token
		self.bot: telebot.TeleBot = telebot.TeleBot(new_token)
		self.cli_console.rule("token updated!")
		self.cli_console.log("token:", new_token)
	
	@property
	def admins(self) -> list: return self.admins_list
	@admins.setter
	def admins(self, new_list) -> None:
		self.admins_list: list = new_list
		self.cli_console.rule("admins list updated!")
		self.cli_console.log("admin list:", new_list)
	
	def log_message(self, message: dict) -> None:
		self.cli_console.log(f"message from \
{message.from_user.first_name} \
{message.from_user.last_name} \
(@{message.from_user.username}: \
{message.from_user.id}):", message)
	
	class handle:
		def mode1(self, message, name):
			"""\
* private:
	1. reply message
	2. send message
* group:
	* sent by admin:
		1. delete message
		2. delete replied message
		3. send message (mentioned the user)
	* sent by user:
		1. delete message
		2. reply the replied message
		3. send message (no mention)
"""
			self.log_message(message)
			if message.chat.type == "private":
				self.bot.reply_to(
						message,
					texts["private"]["command"][name]
				)
			elif message.chat.type in ("group", "supergroup"):
				if self.bot.get_chat_member(
					message.chat.id,
					message.from_user.id
				).status in ("administrator", "creator"):
					self.bot.delete_message(
						message.chat.id, 
						message.message_id
					)
					self.bot.delete_message(
						message.reply_to_message.chat.id,
						message.reply_to_message.message_id
					)
					self.bot.send_message(
						message.chat.id,
						texts["group"]["command"][name]["admin"].format(
							user = "["+str(message.reply_to_message.from_user.first_name)+" "+str(message.reply_to_message.from_user.last_name or "")+"](tg://user?id="+str(message.reply_to_message.from_user.id)+")"
						),
						parse_mode = "MarkDown"
					)
				else:
					self.bot.reply_to(
						message.reply_to_message,
						texts["group"]["command"][name]["user"]
					)
					self.bot.delete_message(
						message.chat.id,
						message.message_id
					)
		def mode2(self, message, name):
			"""\
* private:
	1. reply message
	2. send message
* group:
	* sent by admin:
		1. reply message
		2. send message
	* sent by user:
		1. delete sent message
"""
			self.log_message(message)
			if message.chat.type == "private":
				self.bot.reply_to(
					message, 
					texts["private"]["command"][name]
				)
			elif message.chat.type in ("group", "supergroup"):
				if self.bot.get_chat_member(
					message.chat.id,
					message.from_user.id
				).status in ("administrator", "creator"):
					self.bot.reply_to(
						message,
						texts["group"]["command"][name]
					)
				else:
					self.bot.delete_message(
						message.chat.id,
						message.message_id
					)
	
	def init(self):
		with Progress() as progress:
			task: int = progress.add_task("init", total = 1)
			@self.bot.message_handler(
				commands = ['start']
			)
			def start(message):
				self.handle.mode2(self, message, "start")
			progress.update(task, advance = 1)
			@self.bot.message_handler(
				commands = ['about']
			)
			def help(message):
				self.handle.mode2(self, message, "help")
			progress.update(task, advance = 1)
			@self.bot.message_handler(
				commands = ['help']
			)
			def about(message):
				self.handle.mode2(self, message, "about")
			progress.update(task, advance = 1)
			
			@self.bot.message_handler(
				func = lambda message: message.text in ("!l", "!learn", "!learning")
			)
			def learning(message):
				self.handle.mode1(self, message, "learning")
			progress.update(task, advance = 1)
			
			@self.bot.message_handler(
				func = lambda message: message.text in ("!a", "!ask")
			)
			def ask(message):
				self.log_message(message)
				if message.chat.type == "private":
					self.bot.reply_to(
						message,
						texts["private"]["command"]["ask"]
					)
				elif message.chat.type in ("group", "supergroup"):
					self.bot.reply_to(
						message.reply_to_message,
						texts["group"]["command"]["ask"]
					)
					self.bot.delete_message(
						message.chat.id,
						message.message_id
					)
			progress.update(task, advance = 1)
			
			@self.bot.message_handler(
				func = lambda message: message.text in ("!p", "!prj", "!project")
			)
			def project(message):
				self.handle.mode1(self, message, "project")
			progress.update(task, advance = 1)
			
			@self.bot.message_handler(
				func = lambda message: message.text in ("!i", "!irrelevant")
			)
			def irrelevant(message):
				self.handle.mode1(self, message, "irrelevant")
			progress.update(task, advance = 1)
			
			@self.bot.message_handler(
				func = lambda message: message.text in ("!b", "!bot", "!telebot")
			)
			def telegram_bot(message):
				self.handle.mode1(self, message, "telegram_bot")
			progress.update(task, advance = 1)
			
	def run(self):
		try:
			self.init()
			self.cli_console.log("initialization done.")
			self.cli_console.log("app is going to run...")
			self.bot.polling()
		except Exception as err:
			self.cli_console.log("got error while polling:", err)
