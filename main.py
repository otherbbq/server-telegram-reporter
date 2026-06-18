import logging
import os
import argparse
import importlib
import threading
from pathlib import Path
from datetime import date

from helper.telegram import Telegram
from helper.config import Config
from plugins.base import PluginBase

def load_plugins(directories: list[Path], telegram_bot: Telegram, config: Config, log_file: Path) -> None:
    for directory in directories:
        if not directory.exists():
            logging.warning("The directory '%s' does not exist.", directory)
            continue

        for file in directory.glob("*.py"):
            if file.stem == "__init__":
                continue
            module_path = ".".join(file.with_suffix("").relative_to(Path(__file__).parent).parts)
            _start_plugin(module_path, telegram_bot=telegram_bot, config=config, log_file=log_file)

        for package_dir in directory.iterdir():
            if not package_dir.is_dir() or not (package_dir / "__init__.py").exists():
                continue
            module_path = ".".join(package_dir.relative_to(Path(__file__).parent).parts)
            _start_plugin(module_path, telegram_bot=telegram_bot, config=config, log_file=log_file)


def _start_plugin(module_path: str, telegram_bot: Telegram, config: Config, log_file: Path) -> None:
    module = importlib.import_module(module_path)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
            instance = attr(bot=telegram_bot, config=config, log_file=log_file)
            thread = threading.Thread(target=instance.run, daemon=True)
            thread.start()
            logging.info("Started plugin %s", attr_name)


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

    plugin_directories = [Path(__file__).parent / "plugins" / "builtin", Path(__file__).parent / "plugins" / "user"]
    for dir in plugin_directories:
        dir.mkdir(parents=True, exist_ok=True)

    load_plugins(
        directories=plugin_directories,
        telegram_bot=bot,
        config=config,
        log_file=log_file
    )

    bot.run()


if __name__ == "__main__":
    main()