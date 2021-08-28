#!/usr/bin/env python3

from getpass import getpass


def main() -> None:
	from argparse import ArgumentParser
	parser = ArgumentParser(
		prog = "GTB",
		description = "telegram bot to handle groups, easy to use!",
		epilog = "welcome to Barareh! :)"
	)
	parser.add_argument(
		"token",
		help = "token of your telegram bot",
		type = str
	)
	parser.add_argument(
		"--test-model",
		help="test <Model> part",
		action="store_true"
	)
	args = parser.parse_args()
	if args.test_model:
		from src import start_model_test
		start_model_test(token=args.token)
	else:
		from src import start_bot
		start_bot(
		    token = args.token
		)

if __name__ == "__main__":
	main()
