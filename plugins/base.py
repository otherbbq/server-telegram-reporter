import time
import logging
from typing import Literal
from pathlib import Path

from helper.telegram import Telegram
from helper.config import Config

class PluginBase:
    def __init__(self, downtime: float | int | Literal["realtime"], bot: Telegram, config: Config, log_file: Path) -> None:
        self.downtime = downtime
        self.bot = bot
        self.config = config
        self.log_file = log_file

        if downtime == "realtime":
            logging.warning("Plugin %s runs at realtime speed and will use all available resources.", self.__class__.__name__)

    def execute(self) -> None:
        raise NotImplementedError

    def run(self) -> None:
        while True:
            self.execute()
            if isinstance(self.downtime, int | float):
                time.sleep(self.downtime)