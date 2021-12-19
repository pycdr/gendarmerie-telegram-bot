import logging
from os.path import exists
from threading import Thread
from time import sleep
from urllib.parse import urljoin

from telegram.ext import Updater

from ..handler import get_handlers


class Bot:
    def __init__(
        self,
        token: str,
        model,
        base_url: str
    ) -> None:
        self.model = model
        self.enable_log()
        self.updater = Updater(
            token=token,
            base_url=base_url
        )
        self.token = token
        self.init()

    def init(self):
        for handler in get_handlers(self.model, self.token):
            self.updater.dispatcher.add_handler(
                handler
            )

    def enable_log(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)
        logger = logging.getLogger(__name__)

    def webhook(self, url):
        self.updater.start_webhook(
            listen="0.0.0.0",
            port=5000,
            url_path=self.token
        )
        self.updater.bot.setWebhook(
            urljoin(url, self.token)
        )
        self.updater.idle()

    def start(self):
        def check_db_files():
            last_groups_db_content = b""
            last_commands_db_content = b""
            while True:
                sleep(5)
                if not exists("groups.db"):
                    with open("groups.db", 'wb') as groups_file:
                        groups_file.write(last_groups_db_content)
                    self.model.groups_database.init("groups.db")
                else:
                    last_groups_db_content = open("groups.db", 'rb').read()
                if not exists("commands.db"):
                    with open("commands.db", 'wb') as commands_file:
                        commands_file.write(last_commands_db_content)
                    self.model.commands_database.init("commands.db")
                else:
                    last_commands_db_content = open("commands.db", 'rb').read()
        self.check_db_files_thread = Thread(target=check_db_files)
        self.check_db_files_thread.start()
        self.updater.start_polling()
        self.updater.idle()
