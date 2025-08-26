from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import dump_collection

def get_dump_channel():
    data = dump_collection.find_one({})
    return int(data["channel_id"]) if data else None

def settings_text():
    channel = get_dump_channel()
    dest = f"<code>{channel}</code>" if channel else "Not Set"
    return f"⚙️ <b>Settings Menu</b>\n\n<b>Current Destination:</b> {dest}"

def settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Destination", callback_data="set_dest")],
        [InlineKeyboardButton("Remove Destination", callback_data="remove_dest")],
        [InlineKeyboardButton("Close", callback_data="close_dest")]
    ])

@Client.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client: Client, message: Message):
    await message.reply(
        settings_text(),
        reply_markup=settings_keyboard()
    )

@Client.on_callback_query(filters.regex(r"^(set_dest|remove_dest|close_dest)$"))
async def callback_settings(client: Client, cq: CallbackQuery):
    if cq.data == "set_dest":
        await cq.message.edit_text(
            "Send the channel/chat ID for destination (e.g. <code>-1001234567890</code>) or /cancel.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="back_dest")]]
            )
        )
    elif cq.data == "remove_dest":
        dump_collection.delete_many({})
        await cq.answer("Destination removed!", show_alert=True)
        await cq.message.edit_text(settings_text(), reply_markup=settings_keyboard())
    elif cq.data == "close_dest":
        await cq.message.delete()
    elif cq.data == "back_dest":
        await cq.message.edit_text(settings_text(), reply_markup=settings_keyboard())

@Client.on_callback_query(filters.regex(r"^back_dest$"))
async def back_dest(client: Client, cq: CallbackQuery):
    await cq.message.edit_text(settings_text(), reply_markup=settings_keyboard())

@Client.on_message(filters.private & filters.text)
async def set_dest_chatid(client: Client, message: Message):
    # Only handle if last message was "Send the channel/chat ID..." (for simplicity)
    async for msg in client.get_chat_history(message.chat.id, limit=2):
        if (
            msg.from_user and msg.from_user.is_self and
            "Send the channel/chat ID" in (msg.text or "")
        ):
            if message.text.lower() == "/cancel":
                await message.reply("❌ Cancelled.", reply_markup=settings_keyboard())
                return
            try:
                channel_id = int(message.text.strip())
                dump_collection.delete_many({})
                dump_collection.insert_one({"channel_id": channel_id})
                await message.reply(
                    f"✅ Destination set to <code>{channel_id}</code>\n\n" + settings_text(),
                    reply_markup=settings_keyboard()
                )
            except Exception:
                await message.reply(
                    "❌ Invalid chat ID! Please send a valid chat/channel ID (e.g. <code>-1001234567890</code>) or /cancel.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Back", callback_data="back_dest")]]
                    )
                )
            break
