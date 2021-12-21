#!/usr/bin/env python3

def main() -> None:
	from src import start_bot
	from dotenv import load_dotenv
	from os import getenv
	load_dotenv()
	token = getenv("TOKEN")
	webhook = getenv("WEBHOOK", None)
	start_bot(
		token = token,
		webhook = webhook
	)

if __name__ == "__main__":
	main()
