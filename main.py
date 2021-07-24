#!/usr/bin/env python3
from libs import bot
from getpass import getpass

def main() -> None:
	"""\
this function will be called whenever the "main.py" is executed.
arguments:
$ ./main.py 'token'
"""
	from argparse import ArgumentParser
	parser = ArgumentParser(
		prog = "PyBot",
		description = "telegram bot for handling groups, easy to use!",
		epilog = "welcome to Barareh! :)"
	)
	parser.add_argument(
		"token",
		help = "token of your telegram bot",
		type = str
	)
	parser.add_argument(
		"host",
		help = "mysql host",
		type = str
	)
	parser.add_argument(
		"user",
		help = "mysql user name",
		type = str
	)
	parser.add_argument(
		"database",
		help = "mysql database",
		type = str
	)
	args = parser.parse_args()
	token: str = args.token
	host: str = args.host
	user: str = args.user
	database: str = args.database
	password: str = getpass("password: ")
	app = bot.App(
		token, host = host,
		user = user, database = database, password = password
	)
	app.init()
	app.run()

if __name__ == "__main__":
	main()
