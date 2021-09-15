import logging
from re import M
from telegram.ext import (
    Updater
)
from ..handler import get_handlers
from urllib.parse import urljoin

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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
        )
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
        self.updater.start_polling()
        self.updater.idle()