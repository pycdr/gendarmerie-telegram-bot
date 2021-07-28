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
		self.mode = {}
		# user_id: (
		# 	current_level (
		# 		-1 = nothing,
		# 		0 = AddCmd-CmdNames,
		# 		1 = AddCmd-CmdText,
		# 		2 = AddCmd-CmdDeleteReplied,
		# 		3 = AddCmd-CmdAdminOnly,
		# 		4 = AddCmd-Submitation,
		# 		5 = DelCmd-GetGroupId,
		# 		6 = DelCmd-GetCmdName
		# 	),
		# 	(...)
		# )
		self.commands = {} # chat_id: {command_name: (text, deleted_replied, admin_only)}
		successful, res = self.mysql.get_commands()
		if not successful:
			print("unsuccessful for get commands:", res)
			exit()
		for command in res:
			group_id = command[4]
			command_name = command[0]
			if group_id not in self.commands:
				self.commands[group_id] = {}
			self.commands[group_id][command_name] = command

	def log_message(self, message: dict) -> None:
		pass

	def add_commands(self, group_data: tuple, commands_names: list, commands_text: str, delete_replied: bool, admin_only: bool) -> (bool, str):
		for command_name in commands_names:
			res, err = self.mysql.add_command(group_data[0], command_name, commands_text, delete_replied, admin_only)
			if not res:
				break
			if group_data[0] not in self.commands:
				self.commands[group_data[0]] = {}
			self.commands[group_data[0]][command_name] = (command_name, commands_text, delete_replied, admin_only, group_data[0])
		else:
			err = ''
		return res, err

	def init(self):
		@self.bot.message_handler(commands = ['start'])
		def start(message):
			self.mode[message.from_user.id] = (-1, ())
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
									message.from_user.id: (0, (res, ))
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
					if not successful:
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
			self.bot.send_message(message.chat.id, "process canceled", markup = telebot.types.ReplyKeyboardRemove(selective=False))
		
		@self.bot.message_handler(commands = ['del'])
		def delete(message):
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
			successful, res = self.mysql.get_groups()
			if not successful:
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
			markup = telebot.types.ReplyKeyboardMarkup(row_width = 4 if len(groups) > 4 else len(groups))
			for group in groups:
				markup.add(str(group[0]))
			self.bot.send_message(
				message.chat.id,
				"your group: \n" + "\n".join(
					f"➕ {x[1]} {'('+x[2]+')' if x[2] else ''}: {x[0]}"
					for x in groups
				)+"\nso, choose one of these group IDs:" if len(groups) > 0 else "no group for you:(",
				reply_markup = markup if len(groups) > 0 else telebot.types.ReplyKeyboardRemove(selective=False)
			)
			if len(groups) > 0:
				self.mode[message.from_user.id] = (5, ())

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
			if user_id not in self.mode:
				self.mode[user_id] = (-1, ())
			mode, data = self.mode[user_id]
			if message.chat.type in ("group", "supergroup"):
				command = message.text
				if chat_id not in self.commands or command not in self.commands[chat_id]:
					return
				_, text, delete_replied, admin_only, _ = self.commands[chat_id][command]
				is_admin = self.bot.get_chat_member(
					message.chat.id,
					message.from_user.id
				).status in ("administrator", "creator")
				if admin_only and not is_admin:
					return
				self.bot.delete_message(
					message.chat.id,
					message.message_id
				)
				if delete_replied:
					try:
						if is_admin:
							if message.reply_to_message:
								self.bot.delete_message(
									message.reply_to_message.chat.id,
									message.reply_to_message.message_id
								)
						if message.reply_to_message:
							self.bot.send_message(
								message.chat.id,
								text.format(user_mention = "["+str(message.reply_to_message.from_user.first_name)+" "+str(message.reply_to_message.from_user.last_name or "")+"](tg://user?id="+str(message.reply_to_message.from_user.id)+")"),
								parse_mode = "MarkDown"
							)
					except ApiTelegramException:
						pass
				else:
					try:
						if message.reply_to_message:
							self.bot.reply_to(
								message.reply_to_message,
								text
							)
					except ApiTelegramException:
						pass
				return
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
					"commands saved! now, please send the command text (and nothing else! just in 1 message):\n(also, you can mention user and add its name to the text. just write {user_mention} where you want)"
				)
			elif mode == 1:
				# data: ((group_id, group_name, group_username), [command1, command2, ...])
				text = message.text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
				self.mode[user_id] = (2, (*data, text))
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
				mode, ((group_id, group_name, group_username), commands_names, commands_text, delete_replied, admin_only) = self.mode[user_id]
				self.bot.send_message(
					message.chat.id,
					f"option saved! so, this is the details of your command(s):▶️ group \"{group_name}\"{' @'+group_username if group_username else ''} (id: {group_id})\n▶️ command names:\n{chr(10).join(commands_names)}\n▶️ text:\n{commands_text}\n▶️ delete replied message: {['no', 'yes'][delete_replied]}\n▶️ only for administrators: {['no', 'yes'][admin_only]}\nso, are you sure to add it?",
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
				if "❌✅".index(res):
					successful, err = self.add_commands(*data)
					if successful:
						self.bot.send_message(
							message.chat.id,
							"done! ",
							reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
						)
					else:
						if err == '':
							self.bot.send_message(
								message.chat.id,
								"it has been set for your group! if you want to delete this command, use /del to do it.",
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
			elif mode == 5:
				if not message.text.isnumeric():
					self.bot.reply_to(
						message,
						"invalid group id! please choose from the keyboard:"
					)
					return
				group = int(message.text.isnumeric())
				self.mode[user_id] = (6, (group))
				commands = self.mysql.get_commands(group)
				if len(commands) == 0:
					self.bot.send_message(
						chat_id,
						"no command for your group!\nset command with command /start",
						reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
					)
					self.mode[user_id] = (-1, ())
				markup = telebot.types.ReplyKeyboardMarkup(row_width = 4 if len(commands) > 4 else len(commands))
				for group in groups:
					markup.add(group[0])
				self.bot.send_message(
					chat_id,
					"Ok, now, choose one of these commands:\n"+'\n'.join(
						command[0]
						for command in commands
					)
				)
				
			elif mode == 6:
				command = message.text
				group = data[0]
				if command not in self.mysql.get_commands(group):
					self.bot.reply_to(
						message,
						"invalid command! please choose from the keyboard:"
					)
					return
				successful, err = self.mysql.remove_command(group, command)
				if successful:
					self.bot.send_message(
						chat_id,
						"done!",
						reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
					)
				else:
					self.bot.send_message(
						message.chat.id,
						"unsuccessful:( i reported this to my creator, sorry for this!",
						reply_markup = telebot.types.ReplyKeyboardRemove(selective=False)
					)
					print("error catchen for data (", data, ") - error: ", err)
				self.mode[user_id] = (-1, ())

	def run(self):
		self.bot.polling()
