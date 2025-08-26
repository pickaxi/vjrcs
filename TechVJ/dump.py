from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMINS
from database.db import dump_collection

def is_admin(user_id):
    admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS
    return user_id in admins

def get_dump_channel():
    dump = dump_collection.find_one({})
    return int(dump["channel_id"]) if dump else None

async def settings_menu(client, message_or_call, chat_id, show_as_callback=False):
    # Get current dump destination
    dump_channel = get_dump_channel()
    if dump_channel:
        dest = f"<code>{dump_channel}</code>"
    else:
        dest = "Not Set"
    text = (
        "⚙️ 𝗛𝗲𝗿𝗲 𝗜𝘀 𝗬𝗼𝘂𝗿 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:\n"
        f"Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}"
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", callback_data="settings:destination")]]
    )
    if show_as_callback:
        await message_or_call.edit_message_text(text, reply_markup=keyboard)
    else:
        await message_or_call.reply(text, reply_markup=keyboard)

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("Only admins can use settings.")
        return
    await settings_menu(client, message, message.chat.id, show_as_callback=False)

@Client.on_callback_query(filters.regex(r"^settings:destination$"))
async def destination_settings(client: Client, call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Only admins!", show_alert=True)
        return
    dump_channel = get_dump_channel()
    if dump_channel:
        dest = f"<code>{dump_channel}</code>"
    else:
        dest = "PM"
    text = (
        f"Cᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}\n\n"
        "Sᴇɴᴅ Mᴇ A Cʜᴀᴛ ID Fᴏʀ Uᴘʟᴏᴀᴅ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ. (Mᴀᴋᴇ Sᴜʀᴇ I'm Aʟʀᴇᴀᴅʏ Aᴅᴅᴇᴅ Aꜱ Aᴅᴍɪɴ)\n\n"
        "Or click below to remove destination."
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏪ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="settings:main")],
            [InlineKeyboardButton("❌ Remove Destination", callback_data="settings:remove_dest")]
        ]
    )
    await call.edit_message_text(text, reply_markup=keyboard)
    # Wait for admin to send chat id
    try:
        response: Message = await client.ask(call.message.chat.id, "Please send channel/chat ID or /cancel to cancel.", timeout=60)
    except Exception:
        return
    if response.text == "/cancel":
        await settings_menu(client, call, call.message.chat.id, show_as_callback=True)
        return
    try:
        channel_id = int(response.text)
        dump_collection.delete_many({})
        dump_collection.insert_one({"channel_id": channel_id})
        await response.reply(f"✅ Destination set to <code>{channel_id}</code>")
        # Update settings menu
        await settings_menu(client, call, call.message.chat.id, show_as_callback=True)
    except Exception:
        await response.reply("❌ Invalid chat ID. Please enter a valid one (e.g., -1001234567890).")
        await settings_menu(client, call, call.message.chat.id, show_as_callback=True)

@Client.on_callback_query(filters.regex(r"^settings:remove_dest$"))
async def remove_destination(client: Client, call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Only admins!", show_alert=True)
        return
    dump_collection.delete_many({})
    await call.answer("Destination removed!", show_alert=True)
    await settings_menu(client, call, call.message.chat.id, show_as_callback=True)

@Client.on_callback_query(filters.regex(r"^settings:main$"))
async def back_to_main_settings(client: Client, call: CallbackQuery):
    await settings_menu(client, call, call.message.chat.id, show_as_callback=True)
