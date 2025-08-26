from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from config import ADMINS
from database.db import dump_collection

# Helper: admin check
def is_admin(user_id):
    admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS
    return user_id in admins

# Helper: get current dump channel (returns int or None)
def get_dump_channel():
    dump = dump_collection.find_one({})
    return int(dump["channel_id"]) if dump else None

# Helper: main settings menu
async def settings_menu(client, msg, show_as_callback=False):
    dump_channel = get_dump_channel()
    dest = f"<code>{dump_channel}</code>" if dump_channel else "Not Set"
    text = (
        "⚙️ 𝗛𝗲𝗿𝗲 𝗜𝘀 𝗬𝗼𝘂𝗿 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:\n"
        f"Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}"
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", callback_data="settings:destination")]]
    )
    if show_as_callback:
        await msg.edit_message_text(text, reply_markup=keyboard)
    else:
        await msg.reply(text, reply_markup=keyboard)

# FSM memory: {user_id: {"state": ..., "message_id": ...}}
USER_STATE = {}

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("Only admins can use settings.")
        return
    # Reset any state for this user
    USER_STATE.pop(message.from_user.id, None)
    sent = await message.reply(
        "⚙️ 𝗛𝗲𝗿𝗲 𝗜𝘀 𝗬𝗼𝘂𝗿 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:\n"
        f"Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {get_dump_channel() if get_dump_channel() else 'Not Set'}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", callback_data="settings:destination")]]
        )
    )
    # Remember message to always edit
    USER_STATE[message.from_user.id] = {
        "state": "main_menu",
        "message_id": sent.id
    }

@Client.on_callback_query(filters.regex(r"^settings:destination$"))
async def destination_settings(client: Client, call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Only admins!", show_alert=True)
        return
    # Save state, so bot expects next message as chat_id, and knows which msg to edit
    USER_STATE[call.from_user.id] = {
        "state": "awaiting_destination",
        "message_id": call.message.id
    }
    dump_channel = get_dump_channel()
    dest = f"<code>{dump_channel}</code>" if dump_channel else "PM"
    text = (
        f"Cᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}\n\n"
        "Sᴇɴᴅ ᴍᴇ ᴀ ᴄʜᴀᴛ ID ғᴏʀ ᴜᴘʟᴏᴀᴅ ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ ᴏʀ /cancel.\n"
        "(Mᴀᴋᴇ Sᴜʀᴇ I'm Aᴅᴅᴇᴅ Aꜱ Aᴅᴍɪɴ)\n\n"
        "Or click below to remove destination."
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏪ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="settings:main")],
            [InlineKeyboardButton("❌ Remove Destination", callback_data="settings:remove_dest")]
        ]
    )
    await call.edit_message_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^settings:remove_dest$"))
async def remove_destination(client: Client, call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Only admins!", show_alert=True)
        return
    dump_collection.delete_many({})
    await call.answer("Destination removed!", show_alert=True)
    # Reset state and edit message to main menu
    USER_STATE[call.from_user.id] = {
        "state": "main_menu",
        "message_id": call.message.id
    }
    await settings_menu(client, call, show_as_callback=True)

@Client.on_callback_query(filters.regex(r"^settings:main$"))
async def back_to_main_settings(client: Client, call: CallbackQuery):
    # Reset state and edit message to main menu
    USER_STATE[call.from_user.id] = {
        "state": "main_menu",
        "message_id": call.message.id
    }
    await settings_menu(client, call, show_as_callback=True)

@Client.on_message(filters.private & filters.text)
async def handle_destination_input(client: Client, message: Message):
    state_data = USER_STATE.get(message.from_user.id)
    # Only process if expecting destination and message is not a command
    if not state_data or state_data.get("state") != "awaiting_destination":
        return
    # Only accept text, ignore forwarded etc.
    input_text = message.text.strip()
    # /cancel handling
    if input_text.lower() == "/cancel":
        # Reset state to main menu and edit original message
        USER_STATE[message.from_user.id] = {
            "state": "main_menu",
            "message_id": state_data["message_id"]
        }
        # Edit original settings message to main menu
        try:
            orig_msg = await client.get_messages(message.chat.id, state_data["message_id"])
            await settings_menu(client, orig_msg, show_as_callback=True)
        except Exception:
            pass
        return

    # Try to parse chat id
    try:
        channel_id = int(input_text)
        dump_collection.delete_many({})
        dump_collection.insert_one({"channel_id": channel_id})
        # Reset state to main menu
        USER_STATE[message.from_user.id] = {
            "state": "main_menu",
            "message_id": state_data["message_id"]
        }
        # Edit original settings message to show new destination
        orig_msg = await client.get_messages(message.chat.id, state_data["message_id"])
        await orig_msg.edit_text(
            f"✅ Destination set to <code>{channel_id}</code>\n\n"
            "⚙️ 𝗛𝗲𝗿𝗲 𝗜𝘀 𝗬𝗼𝘂𝗿 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:\n"
            f"Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: <code>{channel_id}</code>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", callback_data="settings:destination")]]
            )
        )
        if message.id != state_data["message_id"]:
            await message.delete()
    except Exception:
        # Invalid input, re-edit original message with error
        try:
            orig_msg = await client.get_messages(message.chat.id, state_data["message_id"])
            dump_channel = get_dump_channel()
            dest = f"<code>{dump_channel}</code>" if dump_channel else "PM"
            await orig_msg.edit_text(
                f"Cᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: {dest}\n\n"
                "❌ Invalid chat ID. Please enter a valid one (e.g., -1001234567890) or /cancel.\n"
                "(Mᴀᴋᴇ Sᴜʀᴇ I'm Aᴅᴅᴇᴅ Aꜱ Aᴅᴍɪɴ)\n\n"
                "Or click below to remove destination.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("⏪ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="settings:main")],
                        [InlineKeyboardButton("❌ Remove Destination", callback_data="settings:remove_dest")]
                    ]
                )
            )
        except Exception:
            pass
