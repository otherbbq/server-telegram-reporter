# Server Telegram Reporter

A lightweight telegram bot for sending server events and status messages to authenticated Telegram users.

## Setup

Install python 3.10 or later.

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your Telegram bot token:

```bash
export TG_BOT_TOKEN="your_bot_token_here"
```

Run the bot:

```bash
python main.py
```  

## Authentication

After the bot is up and running you have to authenticate your account.  

Start a chat with the bot and run:

```text
/start
```

or:

```text
/authenticate
```

The bot logs an authentication token on the server. Paste that token back into the Telegram chat to authenticate the user.

Authenticated users are stored in `user_data.json`.

## Status

This project is still in development.

Planned features are:  
- Custom behaviour support
- Better logging
- Configuration file