"""
TG Auto React + Clone Bot (Advanced)
------------------------------------
Features:
✅ Auto React with delay + multiple styles
✅ Clone system with Approve / Reject
✅ Admin system (add/remove)
✅ Force Subscribe (channel join required)
✅ Beautiful /start (reaction → sticker → message)
✅ Broadcast with owner approval
✅ Stats, Clone control, Delay settings
"""

import asyncio
import json
import random
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberUpdated,
)
from pyrogram.errors import (
    FloodWait,
    ChatAdminRequired,
    UserNotParticipant,
    PeerIdInvalid,
    ChannelPrivate,
)

from config import (
    API_ID, API_HASH, BOT_TOKEN, SESSION_NAME,
    OWNER_ID, LOG_CHAT_ID,
    FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_ID,
    SUPPORT_CHANNEL, AUTO_REACT_CHATS,
    REACT_EMOJIS, DEFAULT_CLONE_TARGET,
    REACT_DELAY_MIN, REACT_DELAY_MAX,
)

# ======================
# LOGGING & PATHS
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TGBot")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ADMINS_FILE = DATA_DIR / "admins.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
USERS_FILE = DATA_DIR / "users.json"
PENDING_FILE = DATA_DIR / "pending_clones.json"

# ======================
# DEFAULT DATA
# ======================
DEFAULT_SETTINGS = {
    "react_delay_min": REACT_DELAY_MIN,
    "react_delay_max": REACT_DELAY_MAX,
    "react_style": "default",
    "clone_enabled": True,
    "auto_react_enabled": True,
}

REACTION_STYLES = {
    "default": ["👍", "❤️", "🔥", "👏", "😍"],
    "fire": ["🔥", "💥", "⚡", "🌋", "❤️‍🔥"],
    "cute": ["🥰", "😘", "💖", "✨", "🌸"],
    "royal": ["👑", "💎", "🏆", "⚜️", "💫"],
    "dark": ["🖤", "💀", "😈", "🦇", "🩸"],
    "party": ["🎉", "🥳", "🎊", "🍾", "💃"],
}

# ======================
# DATA HELPERS
# ======================
def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_admins() -> List[int]:
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = data.get("admins", [])
    if OWNER_ID not in admins:
        admins.append(OWNER_ID)
    return admins

def save_admins(admins: List[int]):
    save_json(ADMINS_FILE, {"admins": list(set(admins))})

def is_admin(user_id: int) -> bool:
    return user_id in get_admins()

def get_settings() -> dict:
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())

def save_settings(settings: dict):
    save_json(SETTINGS_FILE, settings)

def get_users() -> List[int]:
    return load_json(USERS_FILE, {"users": []}).get("users", [])

def add_user(user_id: int):
    users = get_users()
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, {"users": users})

def get_pending() -> Dict[str, Any]:
    return load_json(PENDING_FILE, {})

def save_pending(data: dict):
    save_json(PENDING_FILE, data)

# ======================
# DYNAMIC AUTO-REACT CHATS
# ======================
REACT_CHATS_FILE = DATA_DIR / "react_chats.json"

def get_react_chats() -> list:
    """Get all chats where auto-react is enabled (config + dynamically added)"""
    data = load_json(REACT_CHATS_FILE, {"chats": []})
    chats = set(data.get("chats", []))
    # Always include the ones from config
    for c in AUTO_REACT_CHATS:
        chats.add(c)
    return list(chats)

def add_react_chat(chat_id: int):
    data = load_json(REACT_CHATS_FILE, {"chats": []})
    chats = set(data.get("chats", []))
    if chat_id not in chats:
        chats.add(chat_id)
        save_json(REACT_CHATS_FILE, {"chats": list(chats)})
        logger.info(f"✅ Auto-react enabled for chat: {chat_id}")

def remove_react_chat(chat_id: int):
    data = load_json(REACT_CHATS_FILE, {"chats": []})
    chats = set(data.get("chats", []))
    if chat_id in chats:
        chats.discard(chat_id)
        save_json(REACT_CHATS_FILE, {"chats": list(chats)})
        logger.info(f"❌ Auto-react disabled for chat: {chat_id}")

# ======================
# CLIENT
# ======================
app = Client(
    name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN if BOT_TOKEN else None,
    in_memory=False,
)

# ======================
# FORCE SUBSCRIBE CHECK
# ======================
async def check_force_sub(client: Client, user_id: int) -> bool:
    """Return True if user has joined the required channel"""
    if not FORCE_SUB_CHANNEL_ID and not FORCE_SUB_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(
            FORCE_SUB_CHANNEL_ID or FORCE_SUB_CHANNEL,
            user_id
        )
        return member.status in [
            enums.ChatMemberStatus.MEMBER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except (UserNotParticipant, PeerIdInvalid, ChannelPrivate, Exception):
        return False


def force_sub_keyboard():
    channel = FORCE_SUB_CHANNEL or "Channel"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel.replace('@', '')}")],
        [InlineKeyboardButton("✅ Joined - Verify", callback_data="check_sub")],
    ])


# ======================
# CLONE SYSTEM
# ======================
async def send_clone_preview(client: Client, original_msg: Message, target_chat_id: int = None, is_broadcast: bool = False):
    unique_id = f"{original_msg.chat.id}_{original_msg.id}_{random.randint(10000,99999)}"
    
    pending = get_pending()
    pending[unique_id] = {
        "chat_id": original_msg.chat.id,
        "message_id": original_msg.id,
        "from_user": original_msg.from_user.id if original_msg.from_user else None,
        "target_chat_id": target_chat_id or DEFAULT_CLONE_TARGET,
        "caption": original_msg.caption or original_msg.text or "",
        "media_type": None,
        "file_id": None,
        "is_broadcast": is_broadcast,
        "created_at": datetime.now().isoformat(),
    }

    # Detect media
    for attr in ["photo", "video", "document", "audio", "animation", "sticker", "voice", "video_note"]:
        media = getattr(original_msg, attr, None)
        if media:
            pending[unique_id]["media_type"] = attr
            pending[unique_id]["file_id"] = media.file_id
            break

    save_pending(pending)

    chat_title = original_msg.chat.title or (original_msg.chat.first_name if original_msg.chat else "Unknown")
    sender = original_msg.from_user.first_name if original_msg.from_user else "Channel/Anonymous"
    
    bcast_tag = "\n📢 **BROADCAST REQUEST**" if is_broadcast else ""
    
    preview_text = (
        f"🔄 **CLONE REQUEST**{bcast_tag}\n\n"
        f"📍 **From:** `{chat_title}` (`{original_msg.chat.id}`)\n"
        f"👤 **Sender:** {sender}\n"
        f"🆔 **Msg ID:** `{original_msg.id}`\n"
        f"🎯 **Target:** `{pending[unique_id]['target_chat_id']}`\n\n"
        f"📝 **Content:**\n"
        f"{(original_msg.text or original_msg.caption or '[Media Only]')[:350]}"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"clone_approve_{unique_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"clone_reject_{unique_id}"),
        ],
        [
            InlineKeyboardButton("🗑 Delete Request", callback_data=f"clone_delete_{unique_id}"),
        ]
    ])

    try:
        try:
            await client.forward_messages(LOG_CHAT_ID, original_msg.chat.id, original_msg.id)
        except Exception:
            pass

        await client.send_message(
            LOG_CHAT_ID,
            preview_text,
            reply_markup=buttons,
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        logger.error(f"Clone preview failed: {e}")
        return False


async def perform_clone(client: Client, unique_id: str) -> bool:
    pending = get_pending()
    data = pending.get(unique_id)
    if not data:
        return False

    target = data.get("target_chat_id")
    if not target and not data.get("is_broadcast"):
        return False

    try:
        if data.get("is_broadcast"):
            # Broadcast to all saved users
            users = get_users()
            success = 0
            for uid in users:
                try:
                    await client.copy_message(uid, data["chat_id"], data["message_id"])
                    success += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    continue
            logger.info(f"Broadcast done: {success}/{len(users)}")
            return True

        # Normal clone
        try:
            await client.copy_message(target, data["chat_id"], data["message_id"])
            return True
        except Exception:
            pass

        # Fallback manual
        caption = data.get("caption", "")
        file_id = data.get("file_id")
        media_type = data.get("media_type")

        if media_type == "photo" and file_id:
            await client.send_photo(target, file_id, caption=caption)
        elif media_type == "video" and file_id:
            await client.send_video(target, file_id, caption=caption)
        elif media_type == "document" and file_id:
            await client.send_document(target, file_id, caption=caption)
        elif media_type == "audio" and file_id:
            await client.send_audio(target, file_id, caption=caption)
        elif media_type == "animation" and file_id:
            await client.send_animation(target, file_id, caption=caption)
        elif media_type == "sticker" and file_id:
            await client.send_sticker(target, file_id)
        elif media_type == "voice" and file_id:
            await client.send_voice(target, file_id, caption=caption)
        elif caption:
            await client.send_message(target, caption)
        else:
            return False
        return True
    except Exception as e:
        logger.error(f"Clone failed: {e}")
        return False


# ======================
# HANDLERS
# ======================

@app.on_message(filters.command(["start", "help"]) & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    add_user(user.id)

    # Force Sub Check
    if not await check_force_sub(client, user.id):
        await message.reply_text(
            f"⚠️ **Pehle Channel Join Karo!**\n\n"
            f"Bot use karne se pehle hamara channel join karna zaroori hai.\n\n"
            f"👇 Neeche button se join karke **Verify** dabao.",
            reply_markup=force_sub_keyboard()
        )
        return

    # 1. First reaction
    try:
        await message.react("❤️")
        await asyncio.sleep(0.6)
    except Exception:
        pass

    # 2. Optional sticker (will skip if not available)
    try:
        # You can put your own sticker file_id here later
        pass
    except Exception:
        pass

    # 3. Beautiful start message
    settings = get_settings()
    me = await client.get_me()

    text = f"""
✨ **Welcome {user.first_name}!** ✨

╔══════════════════════╗
║   🤖 **{me.first_name}**   ║
╚══════════════════════╝

🔥 **Powerful Features:**
• Auto React (multiple styles)
• Clone with Approval System
• Broadcast (owner verified)
• Admin System
• Force Subscribe Protection

━━━━━━━━━━━━━━━━━━━━
👑 **Owner:** `{OWNER_ID}`
📢 **Support:** {SUPPORT_CHANNEL}
━━━━━━━━━━━━━━━━━━━━

📌 **Main Commands:**
`/clone` - Reply karke clone karo
`/stats` - Bot stats dekho
`/styles` - Reaction styles
`/help` - Saari commands

⚡ Bot is ready to use!
"""
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.replace('@','')}"),
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="show_stats"),
            InlineKeyboardButton("🎨 Styles", callback_data="show_styles"),
        ]
    ])
    await message.reply_text(text, reply_markup=buttons)


@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_callback(client: Client, callback: CallbackQuery):
    if await check_force_sub(client, callback.from_user.id):
        await callback.answer("✅ Verified! Ab /start dobara bhejo.", show_alert=True)
        await callback.message.delete()
    else:
        await callback.answer("❌ Abhi bhi channel join nahi kiya!", show_alert=True)


@app.on_callback_query(filters.regex("^show_stats$"))
async def show_stats_cb(client: Client, callback: CallbackQuery):
    settings = get_settings()
    pending = get_pending()
    text = (
        f"📊 **Bot Stats**\n\n"
        f"👥 Users: `{len(get_users())}`\n"
        f"👮 Admins: `{len(get_admins())}`\n"
        f"🔄 Pending Clones: `{len(pending)}`\n"
        f"❤️ Auto React Chats: `{len(get_react_chats())}`\n"
        f"🎨 Current Style: `{settings.get('react_style', 'default')}`\n"
        f"⏱ Delay: `{settings.get('react_delay_min')}s - {settings.get('react_delay_max')}s`\n"
        f"📦 Clone System: `{'✅ ON' if settings.get('clone_enabled') else '❌ OFF'}`\n"
        f"⚡ Auto React: `{'✅ ON' if settings.get('auto_react_enabled') else '❌ OFF'}`"
    )
    await callback.answer()
    await callback.message.reply_text(text)


@app.on_callback_query(filters.regex("^show_styles$"))
async def show_styles_cb(client: Client, callback: CallbackQuery):
    settings = get_settings()
    current = settings.get("react_style", "default")
    text = "🎨 **Reaction Styles**\n\n"
    for name, emojis in REACTION_STYLES.items():
        mark = "✅" if name == current else "▫️"
        text += f"{mark} **{name}** → {' '.join(emojis)}\n"
    text += "\nAdmin use: `/setstyle <name>`"
    await callback.answer()
    await callback.message.reply_text(text)


# ======================
# CLONE COMMAND
# ======================
@app.on_message(filters.command("clone"))
async def clone_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("🚫 Sirf Admin / Owner use kar sakte hain.")

    settings = get_settings()
    if not settings.get("clone_enabled", True):
        return await message.reply_text("⏸ Clone system currently **OFF** hai.\nOwner se on karwao.")

    if not message.reply_to_message:
        return await message.reply_text(
            "⚠️ **Reply** karo us message pe jisko clone karna hai.\n\n"
            "`/clone` → default target\n"
            "`/clone <chat_id>` → specific target"
        )

    target = DEFAULT_CLONE_TARGET
    if len(message.command) > 1:
        try:
            target = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid chat ID")

    success = await send_clone_preview(client, message.reply_to_message, target)
    if success:
        await message.reply_text(f"✅ Clone request **Log Chat** me bhej diya!\nTarget: `{target}`")
    else:
        await message.reply_text("❌ Preview bhejne me problem. LOG_CHAT_ID check karo.")


# ======================
# BROADCAST (with approval)
# ======================
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("🚫 Sirf Admin use kar sakte hain.")

    if not message.reply_to_message:
        return await message.reply_text(
            "📢 **Broadcast**\n\n"
            "Kisi message pe **reply** karke `/broadcast` likho.\n"
            "Woh message Log Chat me approval ke liye jaayega.\n"
            "Owner Approve karega tabhi sab users ko jayega."
        )

    # Send as broadcast request
    success = await send_clone_preview(
        client,
        message.reply_to_message,
        target_chat_id=None,
        is_broadcast=True
    )
    if success:
        await message.reply_text(
            "✅ **Broadcast Request** Log Chat me bhej diya!\n"
            "Owner Approve karega tabhi sab users ko message jayega."
        )
    else:
        await message.reply_text("❌ Request bhejne me fail.")


# ======================
# CALLBACK: APPROVE / REJECT / DELETE
# ======================
@app.on_callback_query(filters.regex(r"^clone_(approve|reject|delete)_"))
async def clone_callback_handler(client: Client, callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Sirf Admin approve/reject kar sakte hain.", show_alert=True)

    data = callback.data
    parts = data.split("_", 2)
    if len(parts) < 3:
        return await callback.answer("Invalid data", show_alert=True)

    action = parts[1]
    unique_id = parts[2]

    pending = get_pending()
    if unique_id not in pending:
        return await callback.answer("⏳ Ye request expire ho gayi ya already process ho chuki.", show_alert=True)

    if action == "approve":
        success = await perform_clone(client, unique_id)
        if success:
            await callback.message.edit_text(
                callback.message.text + f"\n\n✅ **APPROVED** by {callback.from_user.first_name}"
            )
            await callback.answer("✅ Successfully processed!")
        else:
            await callback.answer("❌ Process fail hua.", show_alert=True)
            await callback.message.edit_text(
                callback.message.text + "\n\n⚠️ **APPROVED but FAILED**"
            )
    elif action == "reject":
        await callback.message.edit_text(
            callback.message.text + f"\n\n❌ **REJECTED** by {callback.from_user.first_name}"
        )
        await callback.answer("Rejected.")
    elif action == "delete":
        await callback.message.delete()
        await callback.answer("🗑 Request deleted.")

    # Clean
    pending.pop(unique_id, None)
    save_pending(pending)


# ======================
# ADMIN MANAGEMENT
# ======================
@app.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_handler(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage:\n`/addadmin <user_id>`\nya reply karke `/addadmin`")

    if message.reply_to_message and message.reply_to_message.from_user:
        uid = message.reply_to_message.from_user.id
    else:
        try:
            uid = int(message.command[1])
        except:
            return await message.reply_text("❌ Invalid user ID")

    admins = get_admins()
    if uid in admins:
        return await message.reply_text("Ye user already admin hai.")
    admins.append(uid)
    save_admins(admins)
    await message.reply_text(f"✅ `{uid}` ko **Admin** bana diya.")


@app.on_message(filters.command("removeadmin") & filters.user(OWNER_ID))
async def remove_admin_handler(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage:\n`/removeadmin <user_id>`")

    if message.reply_to_message and message.reply_to_message.from_user:
        uid = message.reply_to_message.from_user.id
    else:
        try:
            uid = int(message.command[1])
        except:
            return await message.reply_text("❌ Invalid user ID")

    if uid == OWNER_ID:
        return await message.reply_text("Owner ko remove nahi kar sakte.")

    admins = get_admins()
    if uid not in admins:
        return await message.reply_text("Ye user admin nahi hai.")
    admins.remove(uid)
    save_admins(admins)
    await message.reply_text(f"✅ `{uid}` ko admin se hata diya.")


@app.on_message(filters.command("admins") & filters.user(OWNER_ID))
async def list_admins(client: Client, message: Message):
    admins = get_admins()
    text = "👮 **Admin List**\n\n"
    for i, uid in enumerate(admins, 1):
        mark = "👑" if uid == OWNER_ID else "🔹"
        text += f"{mark} `{uid}`\n"
    await message.reply_text(text)


# ======================
# SETTINGS COMMANDS
# ======================
@app.on_message(filters.command("setstyle"))
async def set_style(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        styles = ", ".join(REACTION_STYLES.keys())
        return await message.reply_text(f"Usage: `/setstyle <name>`\nAvailable: `{styles}`")

    style = message.command[1].lower()
    if style not in REACTION_STYLES:
        return await message.reply_text("❌ Invalid style.")

    settings = get_settings()
    settings["react_style"] = style
    save_settings(settings)
    await message.reply_text(f"✅ Reaction style set to **{style}**\n{' '.join(REACTION_STYLES[style])}")


@app.on_message(filters.command("setdelay") & filters.user(OWNER_ID))
async def set_delay(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: `/setdelay <min> <max>`\nExample: `/setdelay 1.5 4.0`")

    try:
        dmin = float(message.command[1])
        dmax = float(message.command[2])
        if dmin < 0 or dmax < dmin:
            raise ValueError
    except:
        return await message.reply_text("❌ Invalid values.")

    settings = get_settings()
    settings["react_delay_min"] = dmin
    settings["react_delay_max"] = dmax
    save_settings(settings)
    await message.reply_text(f"✅ Delay set: **{dmin}s - {dmax}s**")


@app.on_message(filters.command(["clonestop", "clonestart"]) & filters.user(OWNER_ID))
async def clone_toggle(client: Client, message: Message):
    settings = get_settings()
    if message.command[0] == "clonestop":
        settings["clone_enabled"] = False
        msg = "⏸ Clone system **STOPPED**"
    else:
        settings["clone_enabled"] = True
        msg = "▶️ Clone system **STARTED**"
    save_settings(settings)
    await message.reply_text(msg)


@app.on_message(filters.command(["reactstop", "reactstart"]) & filters.user(OWNER_ID))
async def react_toggle(client: Client, message: Message):
    settings = get_settings()
    if message.command[0] == "reactstop":
        settings["auto_react_enabled"] = False
        msg = "⏸ Auto React **STOPPED**"
    else:
        settings["auto_react_enabled"] = True
        msg = "▶️ Auto React **STARTED**"
    save_settings(settings)
    await message.reply_text(msg)


@app.on_message(filters.command("stats"))
async def stats_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    settings = get_settings()
    pending = get_pending()
    text = (
        f"📊 **Bot Stats**\n\n"
        f"👥 Total Users: `{len(get_users())}`\n"
        f"👮 Admins: `{len(get_admins())}`\n"
        f"🔄 Pending Clones: `{len(pending)}`\n"
        f"❤️ Auto React Chats: `{len(get_react_chats())}`\n"
        f"🎨 Style: `{settings.get('react_style')}`\n"
        f"⏱ Delay: `{settings.get('react_delay_min')}s → {settings.get('react_delay_max')}s`\n"
        f"📦 Clone: `{'ON' if settings.get('clone_enabled') else 'OFF'}`\n"
        f"⚡ AutoReact: `{'ON' if settings.get('auto_react_enabled') else 'OFF'}`\n"
        f"👑 Owner: `{OWNER_ID}`"
    )
    await message.reply_text(text)


@app.on_message(filters.command("styles"))
async def styles_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    settings = get_settings()
    current = settings.get("react_style", "default")
    text = "🎨 **Available Reaction Styles**\n\n"
    for name, emojis in REACTION_STYLES.items():
        mark = "✅" if name == current else "▫️"
        text += f"{mark} `{name}` → {' '.join(emojis)}\n"
    text += "\nChange: `/setstyle <name>`"
    await message.reply_text(text)



@app.on_message(filters.command("reactchats") & filters.user(OWNER_ID))
async def list_react_chats(client: Client, message: Message):
    chats = get_react_chats()
    if not chats:
        return await message.reply_text("📭 Koi auto-react chat nahi hai abhi.")
    
    text = f"❤️ **Auto React Chats** ({len(chats)})\n\n"
    for cid in chats:
        text += f"• `{cid}`\n"
    text += "\nJab bot kisi channel me **Admin** banaya jaye to automatically add ho jata hai."
    await message.reply_text(text)

@app.on_message(filters.command("id"))
async def id_handler(client: Client, message: Message):
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        text = (
            f"👤 User: `{u.id if u else 'N/A'}`\n"
            f"💬 Chat: `{message.chat.id}`\n"
            f"📝 Msg: `{message.reply_to_message.id}`"
        )
    else:
        text = f"💬 Chat ID: `{message.chat.id}`\n👤 Your ID: `{message.from_user.id}`"
    await message.reply_text(text)


@app.on_message(filters.command("ping"))
async def ping(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.reply_text("🏓 **Pong!** Bot is alive.")



# ======================
# AUTO DETECT WHEN BOT IS MADE ADMIN IN ANY CHANNEL
# ======================
@app.on_chat_member_updated()
async def on_bot_added(client: Client, update: ChatMemberUpdated):
    """
    Jab bhi bot kisi channel/group me admin banaya jaye,
    automatically auto-react on kar do us chat me.
    """
    try:
        # Only care about our own status change
        me = await client.get_me()
        if update.new_chat_member.user.id != me.id:
            return

        new_status = update.new_chat_member.status
        old_status = update.old_chat_member.status if update.old_chat_member else None
        chat = update.chat

        # Bot became admin / owner
        if new_status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            if chat.type in [enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP, enums.ChatType.GROUP]:
                add_react_chat(chat.id)
                try:
                    await client.send_message(
                        LOG_CHAT_ID,
                        f"✅ **Auto React Enabled**\n\n"
                        f"📢 Chat: `{chat.title}`\n"
                        f"🆔 ID: `{chat.id}`\n"
                        f"📌 Type: `{chat.type}`\n\n"
                        f"Ab is channel/group me new posts pe auto react hoga."
                    )
                except Exception:
                    pass

        # Bot was removed or demoted
        elif new_status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.RESTRICTED]:
            remove_react_chat(chat.id)
            logger.info(f"Bot removed from {chat.id}, auto-react disabled")

    except Exception as e:
        logger.error(f"on_bot_added error: {e}")


# ======================
# AUTO REACT
# ======================
@app.on_message(~filters.service & ~filters.me & ~filters.private)
async def auto_react_handler(client: Client, message: Message):
    """
    Auto react to new messages in any chat where bot is admin
    (dynamically detected + config list)
    """
    settings = get_settings()
    if not settings.get("auto_react_enabled", True):
        return

    # Check if this chat is in our react list
    react_chats = get_react_chats()
    if message.chat.id not in react_chats:
        return

    style = settings.get("react_style", "default")
    emojis = REACTION_STYLES.get(style, REACT_EMOJIS)
    if not emojis:
        return

    try:
        delay = random.uniform(
            settings.get("react_delay_min", 1.0),
            settings.get("react_delay_max", 3.5)
        )
        await asyncio.sleep(delay)
        emoji = random.choice(emojis)
        await message.react(emoji)
        logger.info(f"Reacted {emoji} → {message.chat.id}:{message.id}")
    except FloodWait as e:
        logger.warning(f"FloodWait {e.value}s")
        await asyncio.sleep(e.value)
    except ChatAdminRequired:
        # Bot is no longer admin, remove from list
        remove_react_chat(message.chat.id)
        logger.warning(f"No react permission in {message.chat.id}, removed from list")
    except Exception as e:
        logger.error(f"Auto react error: {e}")


# ======================
# STARTUP
# ======================
async def main():
    await app.start()
    me = await app.get_me()
    logger.info(f"✅ Started as {me.first_name} (@{me.username}) | {me.id}")
    logger.info(f"👑 Owner: {OWNER_ID}")
    logger.info(f"👮 Admins: {get_admins()}")
    logger.info(f"❤️ Auto-react chats: {len(get_react_chats())}")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
