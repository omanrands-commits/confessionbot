# 🤫 Anonymous Confession Bot — Setup Guide

## What you need
- Python 3.10+
- A Telegram bot token (free, from @BotFather)
- Your `confessions.txt` file (the one you already have)

---

## Step 1 — Install the dependency

```bash
pip install python-telegram-bot
```

---

## Step 2 — Create your bot on Telegram

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts (give it any name and username)
4. BotFather gives you a token like: `7812345678:AAFxyz...`
5. Copy that token

---

## Step 3 — Add the bot to your group

1. Open your Telegram group
2. Tap the group name → Add Members → search your bot's username → Add
3. Make the bot an **Admin** (it needs permission to post messages)

---

## Step 4 — Configure the bot

Open `confession_bot.py` and edit the top section:

```python
BOT_TOKEN        = "7812345678:AAFxyz..."   # ← paste your token here
GROUP_ID         = -1003876111043            # ← already set
INTERVAL         = 15                        # seconds between auto-posts
CONFESSIONS_FILE = "confessions.txt"         # path to your confessions file
```

---

## Step 5 — Place your files together

Put these three files in the same folder:

```
my_bot/
├── confession_bot.py
├── confessions.txt        ← your pre-written confessions
└── (confession_counter.txt will be created automatically)
```

---

## Step 6 — Run the bot

```bash
python confession_bot.py
```

You'll see logs like:
```
Loaded 1000 unique scheduled confessions.
Scheduled posting enabled: one confession every 15 seconds.
Bot is running. Press Ctrl+C to stop.
```

---

## How it works

### Community submissions
- Members open a private chat with your bot
- They send `/start` to get the welcome message
- They type their confession and send it
- The bot posts it to the group as `🤫 Confession #42` — completely anonymous
- The member gets a confirmation that it was posted

### Scheduled posts
- The bot reads `confessions.txt`, shuffles all entries, and posts one every **15 seconds**
- When it runs through the whole file, it reshuffles and starts again
- The counter keeps incrementing across both community and scheduled posts

---

## Running forever (optional)

### On Linux/Mac — using `screen`:
```bash
screen -S confessions
python confession_bot.py
# Press Ctrl+A then D to detach
```

### Using `nohup`:
```bash
nohup python confession_bot.py &> bot.log &
```

### As a systemd service (Linux):
Create `/etc/systemd/system/confessionbot.service`:
```ini
[Unit]
Description=Telegram Confession Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/confession_bot.py
WorkingDirectory=/path/to/
Restart=always

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl enable confessionbot
sudo systemctl start confessionbot
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Forbidden: bot is not a member` | Add the bot to your group and make it admin |
| `Unauthorized` | Double-check your BOT_TOKEN |
| Confessions not loading | Make sure `confessions.txt` is in the same folder as the script |
| Bot stops after a while | Use `screen`, `nohup`, or systemd to keep it running |
