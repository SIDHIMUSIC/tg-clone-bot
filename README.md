# 🤖 TG Auto React + Clone Bot (Advanced)

Powerful Telegram Bot with:

- ⚡ **Auto React** (multiple styles + delay control)
- 🔄 **Clone System** with Approve / Reject / Delete buttons
- 👮 **Admin System** (add / remove admins)
- 📢 **Force Subscribe** (channel join required)
- 📣 **Broadcast** (with owner approval)
- 📊 **Stats** + full control commands
- ✨ Beautiful `/start` (reaction → sticker → message)

---

## ✨ Features Overview

| Feature | Description |
|---------|-------------|
| Auto React | Multiple styles + **Auto detect** (jab bot admin bane kisi channel me) (default, fire, cute, royal, dark, party) + adjustable delay |
| Clone + Approval | Reply `/clone` → Log chat me preview + buttons |
| Broadcast | `/broadcast` → goes for owner approval → then sends to all users |
| Admin System | Owner can add/remove admins |
| Force Join | Users must join your channel before using bot |
| Stats | Live users, pending clones, settings etc. |
| Controls | Start/Stop clone & auto-react anytime |

---

## 🚀 Setup

```bash
git clone <your-repo-url>
cd tg-auto-react-clone-bot

python -m venv venv
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your values

python bot.py
```

---


---

## 🚀 Deploy on Heroku (One Click)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/YOUR_USERNAME/tg-auto-react-clone-bot)

> **Note:** Upar wale button me `YOUR_USERNAME` ko apne GitHub username se replace kar dena.

### Manual Heroku Deploy:

1. GitHub pe repo upload karo
2. [Heroku Dashboard](https://dashboard.heroku.com) pe jaake **New App** banao
3. **Deploy** tab → Connect GitHub → Select repo
4. **Settings** → Config Vars me saari values daalo (API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOG_CHAT_ID etc.)
5. **Resources** tab me `worker` dyno ON karo
6. Deploy!

### Important Config Vars for Heroku:

| Key | Required | Example |
|-----|----------|---------|
| `API_ID` | ✅ | `12345678` |
| `API_HASH` | ✅ | `abcdef...` |
| `BOT_TOKEN` | ✅ | `123456:ABC...` |
| `OWNER_ID` | ✅ | `123456789` |
| `LOG_CHAT_ID` | ✅ | `-1001234567890` |
| `FORCE_SUB_CHANNEL` | ❌ | `@YourChannel` |
| `FORCE_SUB_CHANNEL_ID` | ❌ | `-100xxxx` |
| `SUPPORT_CHANNEL` | ❌ | `@YourSupport` |
| `AUTO_REACT_CHATS` | ❌ | `-100111,-100222` |
| `DEFAULT_CLONE_TARGET` | ❌ | `-100333` |


## ⚙️ Important .env Settings

```env
API_ID=
API_HASH=
BOT_TOKEN=
OWNER_ID=
LOG_CHAT_ID=                 # Approve/Reject buttons yahan aayenge

FORCE_SUB_CHANNEL=@YourChannel
FORCE_SUB_CHANNEL_ID=-100xxxx

SUPPORT_CHANNEL=@YourSupport
AUTO_REACT_CHATS=-100aaa,-100bbb
DEFAULT_CLONE_TARGET=-100ccc

REACT_DELAY_MIN=1.0
REACT_DELAY_MAX=3.5
```

---

## 📌 Commands

### Everyone
| Command | Description |
|---------|-------------|
| `/start` | Beautiful start + force sub check |
| `/help` | Help |
| `/id` | Get chat/user/message ID |

### Admins + Owner
| Command | Description |
|---------|-------------|
| `/clone` | Reply to message to clone |
| `/broadcast` | Reply to message → broadcast request (needs approval) |
| `/stats` | Bot statistics |
| `/styles` | Show reaction styles |
| `/setstyle <name>` | Change reaction style |
| `/ping` | Check bot alive |

### Owner Only
| Command | Description |
|---------|-------------|
| `/addadmin <id>` | Add admin |
| `/removeadmin <id>` | Remove admin |
| `/admins` | List all admins |
| `/setdelay <min> <max>` | Set reaction delay |
| `/clonestop` / `/clonestart` | Toggle clone system |
| `/reactstop` / `/reactstart` | Toggle auto react |

---

## 🔄 How Clone + Broadcast Works

1. Admin replies to any message with `/clone` or `/broadcast`
2. Preview + original message goes to **LOG_CHAT**
3. Buttons appear:
   - ✅ **Approve** → clones / broadcasts
   - ❌ **Reject**
   - 🗑 **Delete Request**
4. Only Admins/Owner can press buttons

Broadcast goes to **all users** who have started the bot (after approval).

---

## 🎨 Reaction Styles

- `default` → 👍 ❤️ 🔥 👏 😍
- `fire` → 🔥 💥 ⚡ 🌋 ❤️‍🔥
- `cute` → 🥰 😘 💖 ✨ 🌸
- `royal` → 👑 💎 🏆 ⚜️ 💫
- `dark` → 🖤 💀 😈 🦇 🩸
- `party` → 🎉 🥳 🎊 🍾 💃

Change with: `/setstyle fire`

---

## 📁 Project Structure

```
tg-auto-react-clone-bot/
├── bot.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── data/               # auto created
    ├── admins.json
    ├── settings.json
    ├── users.json
    └── pending_clones.json
```

---

## ⚠️ Notes

- Bot Token mode recommended
- Force Sub channel me bot ko **admin** banana better hai
- LOG_CHAT me bot ko message bhejne ki permission chahiye
- `.env` aur `data/` folder kabhi public mat karna

---

Made with ❤️ for Telegram automation
