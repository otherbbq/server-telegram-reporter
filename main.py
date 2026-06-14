import logging
import os
import sys
from helper.telegram import Telegram

def main() -> None:
    # TODO: add custom config file paths by adding execution flags

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    token = os.getenv("TG_BOT_TOKEN")

    if token is None:
        raise RuntimeError(
            "Missing bot token. Set TG_BOT_TOKEN."
        )

    bot = Telegram(token)
    bot.run()


if __name__ == "__main__":
    main()