from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
from database.db import dump_collection

def is_admin(user_id):
    admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS
    return user_id in admins

@Client.on_message(filters.command(["add"]) & filters.private)
async def add_dump(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("Only admins can set DUMP channel.")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /add <channel_id>")
        return
    channel_id = args[1]
    dump_collection.delete_many({})  # Only one DUMP channel at a time
    dump_collection.insert_one({"channel_id": channel_id})
    await message.reply(f"DUMP channel set to `{channel_id}`.")

@Client.on_message(filters.command(["dl"]) & filters.private)
async def delete_dump(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("Only admins can delete DUMP channel.")
        return
    dump_collection.delete_many({})
    await message.reply("DUMP channel removed.")

def get_dump_channel():
    dump = dump_collection.find_one({})
    return int(dump["channel_id"]) if dump else None

# NEW /dump command to show current dump channel info
from pyrogram.errors import ChannelInvalid, ChannelPrivate

@Client.on_message(filters.command(["dump"]) & filters.private)
async def show_dump_channel(client: Client, message: Message):
    dump_channel = get_dump_channel()
    if not dump_channel:
        await message.reply("❌ Dump channel not set!")
        return

    try:
        chat_info = await client.get_chat(dump_channel)
        channel_name = chat_info.title
        channel_id = chat_info.id
        await message.reply(
            f"✅ <b>Current Dump Channel:</b>\n"
            f"<b>Channel Name:</b> <code>{channel_name}</code>\n"
            f"<b>Channel ID:</b> <code>{channel_id}</code>"
        )
    except (ChannelInvalid, ChannelPrivate):
        await message.reply("❌ Dump channel not found or is private!")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")
