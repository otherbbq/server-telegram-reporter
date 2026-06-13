import json
import logging
import secrets
from pathlib import Path
import telebot
from helper.config import Config

class Telegram:
    # TODO: add custom config file paths by adding execution flags

    def __init__(self, token: str, users_file: str = "user_data.json") -> None:
        self.config= Config(f"{Path(__file__).parent.parent}/config.json")
        self.token = token
        self.bot = telebot.TeleBot(token)
        self.users_file = Path(users_file)
        self.pending_tokens: dict[str, dict[str, int | str]] = {}

        if not self.users_file.exists():
            self._save_users({})

        self._register_handlers()

    def run(self) -> None:
        self.config.load_configs()
        self.bot.infinity_polling()

    def send_message_to_authenticated_users(self, text: str) -> None:
        users = self._load_users()

        for username, data in users.items():
            if data["role"] == "authenticated":
                chat_id = data.get("chat_id")
                if chat_id is None:
                    logging.warning("Cannot message @%s: missing chat_id", username)
                    continue

                self.bot.send_message(chat_id, text)

    def _register_handlers(self) -> None:
        @self.bot.message_handler(commands=["start"])
        def handle_start(message: telebot.types.Message) -> None:
            username = self._get_username(message)
            users = self._load_users()
            role = users.get(username, {}).get("role")
            strikes = users.get(username, {}).get("strikes")
            max_strikes = self.config.max_strikes

            # this check is redundant. It only checks the validity of all the data inside user_data.json
            # TODO: bundle this code inside a function
            
            if strikes >= max_strikes and role != "banned":
                self.bot.send_message(message.chat.id, "You are banned from authenticating.")
                users[username]["role"] = "banned"
                self._save_users(users)
                logging.info(f"{username} has been banned after exceding the maximum ammount of strikes.")
                return

            if role == "banned":
                self.bot.send_message(message.chat.id, "You are banned from authenticating.")
                return

            if role == "authenticated":
                self.bot.send_message(message.chat.id, "You are already authenticated.")
                return

            auth_token = secrets.token_urlsafe(24)
            self.pending_tokens[username] = {
                "auth_token": auth_token,
                "chat_id": message.chat.id,
            }

            logging.info("Authentication token for @%s: %s", username, auth_token)
            self.bot.send_message(message.chat.id, "Paste authentication token in this chat")
        
        @self.bot.message_handler(commands=["authenticate"])
        def handle_message(message: telebot.types.Message) -> None:
            username = self._get_username(message)
            users = self._load_users()
            role = users.get(username, {}).get("role")
            strikes = users.get(username, {}).get("strikes")
            max_strikes = self.config.max_strikes

            if strikes >= max_strikes and role != "banned":
                self.bot.send_message(message.chat.id, "You are banned from authenticating.")
                users[username]["role"] = "banned"
                self._save_users(users)
                logging.info(f"{username} has been banned after exceding the maximum ammount of strikes.")
                return

            # TODO: add reasons to bans
            if role == "banned":
                self.bot.send_message(message.chat.id, "You are banned from authenticating.")
                return

            if role == "authenticated":
                self.bot.send_message(message.chat.id, "You are already authenticated.")
                return

            auth_token = secrets.token_urlsafe(24)
            self.pending_tokens[username] = {
                "auth_token": auth_token,
                "chat_id": message.chat.id,
            }

            logging.info("Authentication token for @%s: %s", username, auth_token)
            self.bot.send_message(message.chat.id, "Paste authentication token in this chat")

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message: telebot.types.Message) -> None:
            username = self._get_username(message)
            users = self._load_users()
            role = users.get(username, {}).get("role")
            strikes = users.get(username, {}).get("strikes")
            max_strikes = self.config.max_strikes

            if role == "banned":
                self.bot.send_message(message.chat.id, "You are banned from authenticating.")
                return

            text = (message.text or "").strip()
            pending = self.pending_tokens.get(username)     # returns none if the user has no pending auth token

            if pending is None:
                return
            
            elif text != pending.get("auth_token"):
                if not users[username]:
                    self.bot.send_message(message.chat.id, "Invalid authentication token.")
                    self.bot.send_message(message.chat.id, "Request a new one with /authenticate or /start.")
                    users[username] = {
                        "role": "unauthenticated",
                        "chat_id": message.chat.id,
                        "strikes": 1
                    }

                # TODO: fix edge case here
                # this does not account for the eventuality the user edits user_data.json manually

                elif role == "unauthenticated":
                    self.bot.send_message(message.chat.id, "Invalid authentication token.")
                    if strikes >= (max_strikes - 1):
                        self.bot.send_message(message.chat.id, "You have exceded the maximum ammout of authentication attempts. Your account will be banned.")
                        users[username]["role"] = "banned"
                    else:
                        self.bot.send_message(message.chat.id, "Request a new one with /authenticate or /start.")
                    users[username]["strikes"] = strikes + 1
                self._save_users(users)
                return

            del self.pending_tokens[username]
            users[username] = {
                "role": "authenticated",
                "chat_id": message.chat.id,
                "strikes": 0
            }
            self._save_users(users)
            self.bot.send_message(message.chat.id, "You have been authenticated.")
            # TODO: edit the logging handler and make it send logs to authenticated users (the user should be able to set logging level)
            logging.info(f"{username} has authenticated to the bot.")

    def _load_users(self) -> dict[str, dict[str, int | str | None]]:
        users: dict[str, dict[str, int | str | None]] = {}
        content = self.users_file.read_text(encoding="utf-8").strip()

        if not content:
            return users

        try:
            raw_users = json.loads(content)
        except json.JSONDecodeError:
            logging.warning("Invalid users JSON in %s", self.users_file)
            return users

        if not isinstance(raw_users, dict):
            logging.warning("Invalid users data in %s: expected object", self.users_file)
            return users

        for username, data in raw_users.items():
            if not isinstance(username, str):
                continue

            if not isinstance(data, dict):
                logging.warning("Invalid user data for @%s", username)
                continue

            role = data.get("role")
            chat_id = data.get("chat_id")
            strikes = data.get("strikes")

            if not isinstance(role, str):
                logging.warning("Invalid role for @%s", username)
                continue

            if chat_id is not None and not isinstance(chat_id, int):
                try:
                    chat_id = int(chat_id)
                except (TypeError, ValueError):
                    logging.warning("Invalid chat_id for @%s: %s", username, chat_id)
                    chat_id = None

            users[username.strip().lstrip("@")] = {
                "role": role,
                "chat_id": chat_id,
                "strikes": strikes
            }

        return users

    def _save_users(self, users: dict[str, dict[str, int | str | None]]) -> None:
        self.users_file.write_text(
            json.dumps(users, indent=4, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _get_username(message: telebot.types.Message) -> str:
        user = message.from_user

        if user is None:
            return f"chat_{message.chat.id}"

        return user.username or f"id_{user.id}"