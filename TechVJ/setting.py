import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database.db import dump_collection
from config import ADMINS
from Helpers.Keyboards import ButtonMaker

SETTING_TIMEOUT_SECONDS = 60

# FSM memory: {user_id: {"state": ..., "message_id": ...}}
USER_STATE = {}

def is_admin(user_id):
    admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS
    return user_id in admins

def get_dump_channel():
    dump = dump_collection.find_one({})
    return int(dump["channel_id"]) if dump else None

def main_settings_text():
    dump_channel = get_dump_channel()
    dest = f"<code>{dump_channel}</code>" if dump_channel else "Not Set"
    return (
        "⚙️ 𝗛𝗲𝗿𝗲 𝗜𝘀 𝗬𝗼𝘂𝗿 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:\n"
        f"Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}"
    )

def destination_text(error=None):
    dump_channel = get_dump_channel()
    dest = f"<code>{dump_channel}</code>" if dump_channel else "PM"
    txt = (
        f"Cᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}\n\n"
        "Sᴇɴᴅ ᴍᴇ ᴀ ᴄʜᴀᴛ ID ғᴏʀ ᴜᴘʟᴏᴀᴅ ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ ᴏʀ /cancel.\n"
        "(Mᴀᴋᴇ Sᴜʀᴇ I'm Aᴅᴅᴇᴅ Aꜱ Aᴅᴍɪɴ)"
    )
    if error:
        txt += f"\n\n❌ {error}"
    txt += f"\n\nTIMEOUT: {SETTING_TIMEOUT_SECONDS}s"
    return txt

def main_settings_kb():
    bm = ButtonMaker()
    bm.data_button("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", "dumpset destination")
    bm.new_row()
    bm.data_button("CLOSE", "dumpset close", position="footer")
    return bm.build_menu(2)

def destination_kb():
    bm = ButtonMaker()
    bm.data_button("⏪ ᴍᴀɪɴ ᴍᴇɴᴜ", "dumpset main")
    bm.data_button("❌ Remove Destination", "dumpset remove_dest")
    bm.new_row()
    bm.data_button("CLOSE", "dumpset close", position="footer")
    return bm.build_menu(2)

# Timeout utility
def start_timeout_task(client, user_id, msg, state):
    s = USER_STATE[user_id]
    if "timeout_task" in s and s["timeout_task"]:
        s["timeout_task"].cancel()
    loop = asyncio.get_event_loop()
    task = loop.create_task(timeout_settings(client, user_id, msg, state))
    s["timeout_task"] = task

async def timeout_settings(client, user_id, msg, state):
    await asyncio.sleep(SETTING_TIMEOUT_SECONDS)
    s = USER_STATE.get(user_id)
    if not s or s.get("state") != state:
        return
    # Timeout: back to main menu
    await msg.edit_text(
        main_settings_text(),
        reply_markup=main_settings_kb()
    )
    s.clear()

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("Only admins can use settings.")
        return
    USER_STATE.pop(message.from_user.id, None)
    sent = await message.reply(
        main_settings_text(),
        reply_markup=main_settings_kb()
    )
    USER_STATE[message.from_user.id] = {
        "state": "main_menu",
        "message_id": sent.id,
        "timeout_task": None
    }

@Client.on_callback_query(filters.regex(r"^dumpset (\w+)$"))
async def handle_buttons(client: Client, call: CallbackQuery):
    user_id = call.from_user.id
    if not is_admin(user_id):
        await call.answer("Only admins!", show_alert=True)
        return
    action = call.matches[0].group(1)
    s = USER_STATE.setdefault(user_id, {})
    if "timeout_task" in s and s["timeout_task"]:
        s["timeout_task"].cancel()
        s["timeout_task"] = None

    if action == "main":
        s.clear()
        s["state"] = "main_menu"
        s["message_id"] = call.message.id
        s["timeout_task"] = None
        await call.edit_message_text(
            main_settings_text(),
            reply_markup=main_settings_kb()
        )
    elif action == "destination":
        s.clear()
        s["state"] = "awaiting_destination"
        s["message_id"] = call.message.id
        s["timeout_task"] = None
        await call.edit_message_text(
            destination_text(),
            reply_markup=destination_kb()
        )
        start_timeout_task(client, user_id, call.message, "awaiting_destination")
    elif action == "remove_dest":
        dump_collection.delete_many({})
        s.clear()
        s["state"] = "main_menu"
        s["message_id"] = call.message.id
        s["timeout_task"] = None
        await call.answer("Destination removed!", show_alert=True)
        await call.edit_message_text(
            main_settings_text(),
            reply_markup=main_settings_kb()
        )
    elif action == "close":
        await call.message.delete()
        s.clear()

@Client.on_message(filters.private & filters.text)
async def handle_destination_input(client: Client, message: Message):
    user_id = message.from_user.id
    s = USER_STATE.get(user_id)
    if not s or s.get("state") != "awaiting_destination":
        return
    if "timeout_task" in s and s["timeout_task"]:
        s["timeout_task"].cancel()
        s["timeout_task"] = None

    # Get the message_id to edit
    msg_id = s.get("message_id")
    if not msg_id:
        return
    try:
        msg = await client.get_messages(message.chat.id, msg_id)
    except Exception:
        return

    # Handle /cancel
    if message.text.strip().lower() == "/cancel":
        s.clear()
        s["state"] = "main_menu"
        s["message_id"] = msg_id
        await msg.edit_text(
            main_settings_text(),
            reply_markup=main_settings_kb()
        )
        if message.id != msg_id:
            await message.delete()
        return

    # Try chat id
    try:
        channel_id = int(message.text.strip())
        dump_collection.delete_many({})
        dump_collection.insert_one({"channel_id": channel_id})
        s.clear()
        s["state"] = "main_menu"
        s["message_id"] = msg_id
        await msg.edit_text(
            f"✅ Destination set to <code>{channel_id}</code>\n\n" +
            main_settings_text().replace("Not Set", f"<code>{channel_id}</code>"),
            reply_markup=main_settings_kb()
        )
        if message.id != msg_id:
            await message.delete()
    except Exception:
        # Invalid
        await msg.edit_text(
            destination_text(error="Invalid chat ID. Please enter a valid one (e.g., -1001234567890) or /cancel."),
            reply_markup=destination_kb()
        )
        start_timeout_task(client, user_id, msg, "awaiting_destination")
