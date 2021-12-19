#!/usr/bin/env python3

def main() -> None:
    from os import getenv

    from dotenv import load_dotenv

    from src import start_bot
    load_dotenv()
    token = getenv("TOKEN")
    webhook = getenv("WEBHOOK", None)
    start_bot(
        token=token,
        webhook=webhook
    )


if __name__ == "__main__":
    main()
