import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import dump_collection

USER_STATE = {}
SETTING_TIMEOUT = 60

def get_dump_channel():
    data = dump_collection.find_one({})
    return int(data["channel_id"]) if data else None

def main_settings_text():
    channel = get_dump_channel()
    dest = f"<code>{channel}</code>" if channel else "Not Set"
    return f"⚙️ <b>Here Are Your Settings</b>\n\n<b>Destination:</b> {dest}"

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Destination", callback_data="set_dest")],
        [InlineKeyboardButton("Remove Destination", callback_data="rem_dest")],
        [InlineKeyboardButton("Close", callback_data="close_set")]
    ])

def ask_dest_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_set")],
        [InlineKeyboardButton("Close", callback_data="close_set")]
    ])

async def settings_timeout(client, user_id, msg, state):
    await asyncio.sleep(SETTING_TIMEOUT)
    s = USER_STATE.get(user_id)
    if s and s.get("state") == state:
        await msg.edit_text(main_settings_text(), reply_markup=main_keyboard())
        USER_STATE.pop(user_id, None)

@Client.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client: Client, message: Message):
    m = await message.reply(main_settings_text(), reply_markup=main_keyboard())
    USER_STATE[message.from_user.id] = {"state": "main", "msg_id": m.id, "timeout": None}

@Client.on_callback_query(filters.regex(r"^(set_dest|rem_dest|main_set|close_set)$"))
async def settings_callback(client: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    data = cq.data
    s = USER_STATE.get(user_id, {})
    if s.get("timeout"):
        s["timeout"].cancel()
        s["timeout"] = None

    if data == "main_set":
        await cq.message.edit_text(main_settings_text(), reply_markup=main_keyboard())
        USER_STATE[user_id] = {"state": "main", "msg_id": cq.message.id, "timeout": None}
    elif data == "set_dest":
        await cq.message.edit_text(
            "Send me a channel/chat ID (like <code>-1001234567890</code>) for destination, or /cancel.",
            reply_markup=ask_dest_keyboard()
        )
        task = asyncio.create_task(settings_timeout(client, user_id, cq.message, "dest"))
        USER_STATE[user_id] = {"state": "dest", "msg_id": cq.message.id, "timeout": task}
    elif data == "rem_dest":
        dump_collection.delete_many({})
        await cq.answer("Destination removed!", show_alert=True)
        await cq.message.edit_text(main_settings_text(), reply_markup=main_keyboard())
        USER_STATE[user_id] = {"state": "main", "msg_id": cq.message.id, "timeout": None}
    elif data == "close_set":
        await cq.message.delete()
        USER_STATE.pop(user_id, None)

@Client.on_message(filters.private & filters.text)
async def set_dest_value(client: Client, message: Message):
    user_id = message.from_user.id
    s = USER_STATE.get(user_id)
    if not s or s.get("state") != "dest":
        return
    if s.get("timeout"):
        s["timeout"].cancel()
        s["timeout"] = None

    if message.text.lower() == "/cancel":
        msg = await client.get_messages(message.chat.id, s["msg_id"])
        await msg.edit_text(main_settings_text(), reply_markup=main_keyboard())
        USER_STATE[user_id] = {"state": "main", "msg_id": msg.id, "timeout": None}
        if message.id != msg.id:
            await message.delete()
        return

    try:
        channel_id = int(message.text.strip())
        dump_collection.delete_many({})
        dump_collection.insert_one({"channel_id": channel_id})
        msg = await client.get_messages(message.chat.id, s["msg_id"])
        await msg.edit_text(
            f"✅ Destination set to <code>{channel_id}</code>\n\n" + main_settings_text(),
            reply_markup=main_keyboard()
        )
        USER_STATE[user_id] = {"state": "main", "msg_id": msg.id, "timeout": None}
        if message.id != msg.id:
            await message.delete()
    except Exception:
        msg = await client.get_messages(message.chat.id, s["msg_id"])
        await msg.edit_text(
            "❌ Invalid chat ID! Please send a valid chat/channel ID (e.g., <code>-1001234567890</code>) or /cancel.",
            reply_markup=ask_dest_keyboard()
        )
        task = asyncio.create_task(settings_timeout(client, user_id, msg, "dest"))
        USER_STATE[user_id] = {"state": "dest", "msg_id": msg.id, "timeout": task}
