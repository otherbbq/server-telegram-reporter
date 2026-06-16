import logging
import os
import argparse
from pathlib import Path
from datetime import date

from helper.telegram import Telegram
from helper.config import Config

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default=f"{Path(__file__).parent}/config.json")
    args = parser.parse_args()

    config = Config(args.config)
    config.load_configs()

    log_file = Path(config.log_path) / f"{date.today()}_log.txt" if config.log_path else Path(__file__).parent / "log" / f"{date.today()}_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

    token = os.getenv("TG_BOT_TOKEN")

    if token is None:
        raise RuntimeError(
            "Missing bot token. Set TG_BOT_TOKEN."
        )

    bot = Telegram(token, config=config)
    bot.run()


if __name__ == "__main__":
    main()