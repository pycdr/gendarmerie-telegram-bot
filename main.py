#!/usr/bin/env python3.6
import bot
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

def main() -> None:
	"""\
this function will be called whenever the "main.py" is executed.
arguments:
$ ./main.py 'token' -a/--admin @id1 @id2 ...
"""
	from os.path import exists
	if exists('./config.json'):
		from json import load
		data: dict = load(open("./config.json", 'r'))
		token: str = data['token']
		admins: list = data['users']['admins']
	else:
		from argparse import ArgumentParser
		parser = ArgumentParser(
			prog = "PyBot",
			description = "simple telegram bot."
		)
		parser.add_argument(
			"token",
			help = "token of your telegram bot",
			type = str,
			required = True
		)
		parser.add_argument(
			"-a", "--admins",
			help = "list of admins (@id1,@id2,...)",
			action = "extend",
			nargs = "+",
			required = False
		)
		args = parser.parse_args()
		token: str = args.token
		admins: list = args.admins
	
	class Handler(FileSystemEventHandler):
		def on_modified(self, event):
			if event.src_path == ".":
				data: dict = load(open("./config.json", 'r'))
				if app.token != data["token"]:
					app.token: str = data["token"]
				if app.admins != data["users"]["admins"]:
					app.admins: list = data["users"]["admins"]
				new_texts: dict = load(open("texts.json", 'r'))
				if bot.texts != new_texts:
					bot.texts = new_texts
	
	handler: Handler = Handler()
	observer = Observer()
	observer.schedule(handler,  path='.',  recursive = False)
	observer.start()
	app: bot.App = bot.App(token, admins = admins)
	try:
		app.run()
	except Exception as err:
		app.cli_console.log("got error while running app:", err)
	app.cli_console.rule("exit")
	observer.stop()
	observer.join()
	app.cli_console.log("exit program...")
	
if __name__ == "__main__":
	main()
