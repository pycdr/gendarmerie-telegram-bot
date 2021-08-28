import logging
from re import M
from telegram.ext import (
    Updater
)
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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
        )
        logger = logging.getLogger(__name__)
    
    def start(self):
        self.updater.start_polling()
        self.updater.idle()