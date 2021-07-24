import telebot
from telebot.apihelper import ApiTelegramException
from os.path import exists
from .database import MySQLHandler
from traceback import format_exc as traceback_format_exc

class App:
	"""this class contains all methods and objects used to build telegram bot and logs."""
	def __init__(self, token: str, **kwargs: dict):
		self.mysql = MySQLHandler(**kwargs)
		self.bot = telebot.TeleBot(token)
		self.info = self.bot.get_me()
		self.mode = {} # user_id: (current_level (-1=nothing, 0=cmd-names, 1=cmd-text, 2=cmd-delete_replied, 3=cmd-admin_only, 4=submitation, 5=process), (...))

	def log_message(self, message: dict) -> None:
		pass

	def add_commands(self, group_data: tuple, commands_names: list, commands_text: str, delete_replied: bool, admin_only: bool) -> (bool, str):
		for command_name in commands_names:
			res, err = self.mysql.add_command(group_data[0], command_name, commands_text, delete_replied, admin_only)
			if not res:
				break
		else:
			err = ''
		return res, err

	def init(self):
		@self.bot.message_handler(commands = ['start'])
		def start(message):
			if message.chat.type in ("group", "supergroup"):
				if self.bot.get_chat_member(
					message.chat.id,
					message.from_user.id
				).status in ("administrator", "creator"):
					self.bot.reply_to(
						message,
						f"click there to add command: t.me/{self.info.username}?start={message.chat.id}"
					)
				else:
					try:
						self.bot.delete_message(
							message.chat.id,
							message.from_user.id
						)
					except ApiTelegramException:
						pass
			else:
				parts: list = message.text.split(" ")
				if len(parts) > 2:
					self.bot.reply_to(
						message,
						"invalid parameters! please just send /start without anything else!"
					)
				elif len(parts) == 2:
					try:
						group_id = int(parts[1])
						successful, res = self.mysql.get_group(group_id)
						if successful == False:
							if res:
								self.bot.reply_to(
									message,
									"unsuccessful: "+res
								)
							else:
								self.bot.reply_to(
									message,
									"no group found for you. send /add in your group to add it."
								)
							return
						if res:
							if self.bot.get_chat_member(
								res[0],
								message.from_user.id
							).status in ("administrator", "creator"):
								self.mode.update({
									message.from_user.id: (1, (res, ))
								})
								self.bot.send_message(
									message.chat.id,
									"OK, send me some new command names (can contain charaters from ascii code 33 to 126, like letters, numbers and ...). please list them like this:\n```command1\ncommand2\n...```\n**notice that they will do the same job!**\nyou can send /cancel to cancel the process.",
									parse_mode = "MarkDown"
								)
							else:
								self.bot.reply_to(
									message,
									";)"
								)
						else:
							self.bot.reply_to(
								f"no group found by id {group_id}. please add the bot to your group, then send /start there."
							)
					except ValueError:
						self.bot.reply_to(
							message,
							"invalid group argument!"
						)
				else:
					successful, res = self.mysql.get_groups()
					if successful == False:
						self.bot.reply_to(
							message,
							"unsuccessful: "+res
						)
						return
					groups = [
						group
						for group in res
						if self.bot.get_chat_member(
							group[0],
							message.from_user.id
						).status in ("administrator", "creator")
					]
					self.bot.reply_to(
						message,
						"your group: \n" + "\n".join(
							f"➕ {x[1]} {'('+x[2]+')' if x[2] else ''}: t.me/{self.info.username}?start={x[0]}"
							for x in groups
						) if len(groups) > 0 else "no group for you:("
					)

		@self.bot.message_handler(commands = ['cancel'])
		def cancel(message):
			self.mode[message.from_user.id] = (-1, ())
			self.bot.send_message(message.chat.id, "process canceled")

		@self.bot.message_handler(commands = ['add'])
		def add(message):
			if message.chat.type in ("group", "supergroup"):
				if self.bot.get_chat_member(
					message.chat.id,
					message.from_user.id
				).status in ("administrator", "creator"):
					res, err = self.mysql.add_group(message.chat.id, message.chat.title, message.chat.username or "NULL")
					if not res:
						self.bot.reply_to(
							message,
							"unsuccessful: "+err
						)
					else:
						self.bot.send_message(
							message.chat.id,
							f"done! now, click here to add a new command:  t.me/{self.info.username}?start={message.chat.id}"
						)
				else:
					try:
						self.bot.delete_message(
							message.chat.id,
							message.message_id
						)
					except ApiTelegramException:
						pass
			else:
				self.bot.send_message(
					message.chat.id,
					"please send this command in your group!"
				)

		@self.bot.message_handler(content_types = ["text"])
		def check_msg(message):
			user_id = message.from_user.id
			chat_id = message.chat.id
			if user_id not in self.mode: return
			mode, data = self.mode[user_id]
			if mode == 0:
				# data: ((group_id, group_name, group_username), )
				commands = [x for x in message.text.split('\n') if x != '']
				if not all(all(33 <= ord(x) <= 126 for x in command) for command in commands):
					self.bot.send_message(
						chat_id,
						"invalid command found! you can just use this characters:\n```!\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~```\nplease send valid commands again: ",
						parse_mode = "MarkDown"
					)
					return
				self.mode[user_id] = (1, (*data, commands))
				self.bot.send_message(
					chat_id,
					"commands saved! now, please send the command text (and nothing else! just in 1 message):\n(also, you can mention user and add its name to the text. just write %user_mention% where you want)"
				)
			elif mode == 1:
				# data: ((group_id, group_name, group_username), [command1, command2, ...])
				self.mode[user_id] = (2, (*data, message.text))
				markup = telebot.types.ReplyKeyboardMarkup(row_width = 2)
				markup.add(
					telebot.types.KeyboardButton("✅"),
					telebot.types.KeyboardButton("❌")
				)
				self.bot.send_message(
					message.chat.id,
					"text saved! now, tell me should i delete the message which you will reply it with the command?\n* don't worry! this option will just work for administrators",
					reply_markup = markup
				)
			elif mode == 2:
				# data: ((group_id, group_name, group_username), [command1, command2, ...], "text")
				res = message.text
				if res not in "❌✅":
					self.reply_to(
						message,
						"invalid message! just choose one of these keyboards..."
					)
					return
				self.mode[user_id] = (3, (*data, bool("❌✅".index(res))))
				markup = telebot.types.ReplyKeyboardMarkup(row_width = 2)
				markup.add(
					telebot.types.KeyboardButton("✅"),
					telebot.types.KeyboardButton("❌")
				)
				self.bot.send_message(
					message.chat.id,
					"option saved! now, tell me is it only for administrators? \n(if it is, so normal users won't be able to use these commands)",
					reply_markup = markup
				)
			elif mode == 3:
				# data: ((group_id, group_name, group_username), [command1, command2, ...], "text", delete_replied)
				res = message.text
				if res not in "❌✅":
					self.reply_to(
						message,
						"invalid message! just choose one of these keyboards..."
					)
					return
				self.mode[user_id] = (4, (*data, bool("❌✅".index(res))))
				markup = telebot.types.ReplyKeyboardMarkup(row_width = 2)
				markup.add(
					telebot.types.KeyboardButton("✅"),
					telebot.types.KeyboardButton("❌")
				)
				self.bot.send_message(
					message.chat.id,
					"option saved! now, tell me is it only for administrators? \n(if it is, so normal users won't be able to use these commands)",
					reply_markup = markup
				)
			elif mode == 4:
				# data: ((group_id, group_name, group_username), [command1, command2, ...], "text", delete_replied, admin_only)
				res = message.text
				if res not in "❌✅":
					self.reply_to(
						message,
						"invalid message! just choose one of these keyboards..."
					)
					return
				self.mode[user_id] = (5, (*data, bool("❌✅".index(res))))
				markup = telebot.types.ReplyKeyboardMarkup(row_width = 2)
				markup.add(
					telebot.types.KeyboardButton("✅"),
					telebot.types.KeyboardButton("❌")
				)
				mode, ((group_id, group_name, group_username), commands_names, commands_text, delete_replied, admin_only) = self.mode[user_id]
				self.bot.send_message(
					message.chat.id,
					f"option saved! so, this is the details of your command(s):▶️ group \"{group_name}\"{' @'+group_username if group_username else ''} (id: {group_id})\n▶️ command names:\n{chr(10).join(commands_names)}\n▶️ text:\n{commands_text}\n▶️ delete replied message: {['no', 'yes'][delete_replied]}\n▶️ only for administrators: {['no', 'yes'][admin_only]}\nso, are you sure to add it?",
					reply_markup = markup
				)
			elif mode == 5:
				res = message.text
				if res not in "❌✅":
					self.reply_to(
						message,
						"invalid message! just choose one of these keyboards..."
					)
					return
				if "❌✅".index(res):
					successful, err = self.add_commands(*data)
					if successful:
						self.bot.send_message(
							message.chat.id,
							"done! ",
							reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
						)
					else:
						self.bot.send_message(
							message.chat.id,
							"unsuccessful:( i reported this to my creator, sorry for this!",
							reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
						)
						print("error catchen for data (", data, ") - error: ", err)
				else:
					self.bot.send_message(
						message.chat.id,
						"process canceled.",
						reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
					)
				self.mode[user_id] = (-1, ())

	def run(self):
		self.bot.polling()
