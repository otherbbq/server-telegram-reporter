import json
import logging
import os
from pathlib import Path

class Config:
    def __init__(self, config_file: str):
        self.file = Path(config_file)
        self.config = {}
        self.default_configs = {
            "log_path": "",
            "max_strikes": 5
        }

    def load_configs(self) -> None:
        if os.path.exists(self.file):
            with open(self.file) as file:
                self.config = json.load(file)
        else:
            with open(self.file, "w") as file:
                json.dump(self.default_configs, file, indent=4)
            self.config = self.default_configs

    def __getattr__(self, key):
        try:
            return self.config.get(key)
        except:
            raise AttributeError("No config named %s in config file", key)