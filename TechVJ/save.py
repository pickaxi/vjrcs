import asyncio
import pyrogram
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.io.VideoFileClip import VideoFileClip
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import time
import os, sys
from config import API_ID, API_HASH, ADMINS, WATERMARK_TEXT, SPLIT_SIZE, DEFAULT_THUMB
from database.db import database, dump_collection
from TechVJ.strings import strings, HELP_TXT, BATCH_TXT

def get(obj, key, default=None):
    try:
        return obj[key]
    except Exception:
        return default

async def downstatus(client: Client, statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"📥 Downloading...\n\n{txt}")
            await asyncio.sleep(4)
        except Exception:
            await asyncio.sleep(5)

async def upstatus(client: Client, statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"📤 Uploading...\n\n{txt}")
            await asyncio.sleep(4)
        except Exception:
            await asyncio.sleep(5)

def progress(current, total, message, type, start_time):
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time
    speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1024 * 1024 else f"{speed / (1024 * 1024):.2f} MB/s"
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"⏳ Done: {current * 100 / total:.1f}%\n📶 Speed: {speed_str}\n📁 Size: {current / (1024 * 1024):.2f} MB / {total / (1024 * 1024):.2f} MB")

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("Developer", url="tg://settings")],
        [
            InlineKeyboardButton('A', url='https://google.com'),
            InlineKeyboardButton('💫 ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ', url='https://t.me/durov')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        message.chat.id,
        f"<b>👋 Hi {message.from_user.mention}, I am Slave Saver Bot, I can send you public channel's restricted contents.\n\nFor more info how to use bot press - /help</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(message.chat.id, f"{HELP_TXT}")

@Client.on_message(filters.command(["batch"]) & filters.private)
async def batch_command(client: Client, message: Message):
    # Step 1: Ask user for post link
    link_msg = await client.ask(message.chat.id, "Ek post ka link bhejein (e.g. https://t.me/channel/123):")
    datas = link_msg.text.strip().split("/")
    try:
        fromID = int(datas[-1].replace("?single", ""))
    except Exception:
        await client.send_message(message.chat.id, "❌ Link format galat hai. Please send a direct post link, e.g. https://t.me/channel/123")
        return
    username = None
    if "https://t.me/c/" in link_msg.text:  # private
        username = int("-100" + datas[4])
    else:
        username = datas[3]
    # Step 2: Ask for count
    count_msg = await client.ask(message.chat.id, "Kitni files save karni hai? (Number batao):")
    try:
        count = int(count_msg.text)
        if count < 1:
            raise ValueError
    except Exception:
        await client.send_message(message.chat.id, "❌ Number galat hai.")
        return
    toID = fromID + count - 1
    await client.send_message(message.chat.id, f"{count} files save kiye jaenge: {fromID} se {toID} tak.")

    progress_msg = None
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Updates", url="https://t.me/EchoBotz")]
        ]
    )
    progress_msg = await client.send_message(
        message.chat.id,
        f"Progress Status\nStarted\n1/{count}",
        reply_markup=markup
    )
    try:
        await client.unpin_chat_message(message.chat.id)
    except Exception:
        pass
    try:
        await client.pin_chat_message(message.chat.id, progress_msg.id, both_sides=True)
    except Exception as e:
        print(f"Pin failed: {e}")

    for idx, msgid in enumerate(range(fromID, toID + 1), start=1):
        # PRIVATE CHANNELS
        if "https://t.me/c/" in link_msg.text or "https://t.me/b/" in link_msg.text:
            user_data = database.find_one({'chat_id': message.chat.id})
            if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                await client.send_message(message.chat.id, strings['need_login'])
                return
            acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
            await acc.connect()
            try:
                await handle_private(client, acc, message, username, msgid)
            except Exception as e:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        else:
            # PUBLIC CHANNELS
            try:
                msg = await client.get_messages(username, msgid)
            except UsernameNotOccupied:
                await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                return
            try:
                sent_msg = await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                dump_channel = get_dump_channel()
                if dump_channel:
                    await client.copy_message(dump_channel, sent_msg.chat.id, sent_msg.id)
            except Exception:
                try:
                    user_data = database.find_one({"chat_id": message.chat.id})
                    if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                        await client.send_message(message.chat.id, strings['need_login'])
                        return
                    acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
                    await acc.connect()
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

        if progress_msg:
            try:
                await client.edit_message_text(
                    message.chat.id,
                    progress_msg.id,
                    f"Progress Status\nStarted\n{idx}/{count}",
                    reply_markup=markup
                )
            except Exception:
                pass
        await asyncio.sleep(3)

@Client.on_message(filters.command(["batch_old"]))
async def send_batch(client: Client, message: Message):
    await client.send_message(message.chat.id, f"{BATCH_TXT}")

@Client.on_message(filters.command('restart') & filters.private)
async def restart_command(client: Client, message: Message):
    admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS
    if message.from_user.id not in admins:
        await message.reply_text("Ohh Babe! Sorry But You Can't Restart Me 🙁")
        return
    h = await message.reply_text("🔄 Restarting...")
    paths_to_remove = ["video_path", "thumbnail_path", "output_path", "output_thumbnail_path"]
    for path in paths_to_remove:
        if os.path.exists(path):
            os.remove(path)
    await h.delete()
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except Exception:
            toID = fromID

        total = toID - fromID + 1 if toID >= fromID else 1
        progress_msg = None
        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Updates", url="https://t.me/EchoBotz")]
            ]
        )

        if total > 1:
            progress_msg = await client.send_message(
                message.chat.id,
                f"Progress Status\nStarted\n1/{total}",
                reply_markup=markup
            )
            try:
                await client.unpin_chat_message(message.chat.id)
            except Exception:
                pass
            try:
                await client.pin_chat_message(message.chat.id, progress_msg.id, both_sides=True)
            except Exception as e:
                print(f"Pin failed: {e}")

        for idx, msgid in enumerate(range(fromID, toID + 1), start=1):
            if "https://t.me/c/" in message.text:
                user_data = database.find_one({'chat_id': message.chat.id})
                if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                    await client.send_message(message.chat.id, strings['need_login'])
                    return
                acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
                await acc.connect()
                chatid = int("-100" + datas[4])
                await handle_private(client, acc, message, chatid, msgid)
            elif "https://t.me/b/" in message.text:
                user_data = database.find_one({"chat_id": message.chat.id})
                if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                    await client.send_message(message.chat.id, strings['need_login'])
                    return
                acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
                await acc.connect()
                username = datas[4]
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            else:
                username = datas[3]
                try:
                    msg = await client.get_messages(username, msgid)
                except UsernameNotOccupied:
                    await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                    return
                try:
                    sent_msg = await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                    dump_channel = get_dump_channel()
                    if dump_channel:
                        await client.copy_message(dump_channel, sent_msg.chat.id, sent_msg.id)
                except Exception:
                    try:
                        user_data = database.find_one({"chat_id": message.chat.id})
                        if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                            await client.send_message(message.chat.id, strings['need_login'])
                            return
                        acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
                        await acc.connect()
                        await handle_private(client, acc, message, username, msgid)
                    except Exception as e:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            if progress_msg:
                try:
                    await client.edit_message_text(
                        message.chat.id,
                        progress_msg.id,
                        f"Progress Status\nStarted\n{idx}/{total}",
                        reply_markup=markup
                    )
                except Exception:
                    pass
            await asyncio.sleep(3)

async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)
    chat = message.chat.id
    dump_channel = get_dump_channel()

    if "Text" == msg_type:
        try:
            sent_msg = await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id)
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            return

    smsg = await client.send_message(message.chat.id, '📥 Trying To Download', reply_to_message_id=message.id)
    dosta = asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg))

    start_time = time.time()
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down", start_time])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    upsta = asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg))

    caption = msg.caption if msg.caption else None

    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except Exception:
            ph_path = None
        file_parts = split_file(file, SPLIT_SIZE)
        for part in file_parts:
            start_time = time.time()
            try:
                sent_msg = await client.send_document(chat, part, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
                if dump_channel:
                    await client.copy_message(dump_channel, chat, sent_msg.id)
            except Exception as e:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            if part != file:
                os.remove(part)
        if ph_path is not None:
            os.remove(ph_path)

    if "Photo" == msg_type:
        file = add_watermark_to_image(file, WATERMARK_TEXT)
        start_time = time.time()
        try:
            sent_msg = await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Video" == msg_type:
        file_parts = split_file(file, SPLIT_SIZE)
        for part in file_parts:
            try:
                thumbnail_path = add_text_to_thumbnail(part, WATERMARK_TEXT, time_point=1, default_image_url=DEFAULT_THUMB)
                start_time = time.time()
                sent_msg = await client.send_video(
                    chat,
                    part,
                    thumb=thumbnail_path,
                    duration=msg.video.duration,
                    width=msg.video.width,
                    height=msg.video.height,
                    caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress,
                    progress_args=[message, "up", start_time]
                )
                if dump_channel:
                    await client.copy_message(dump_channel, chat, sent_msg.id)
            except Exception as e:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            if part != file:
                os.remove(part)

    elif "Sticker" == msg_type:
        start_time = time.time()
        try:
            sent_msg = await client.send_sticker(chat, file, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Animation" == msg_type:
        start_time = time.time()
        try:
            sent_msg = await client.send_animation(chat, file, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Voice" == msg_type:
        start_time = time.time()
        try:
            sent_msg = await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Audio" == msg_type:
        try:
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
        except Exception:
            ph_path = None
        start_time = time.time()
        try:
            sent_msg = await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up", start_time])
            if dump_channel:
                await client.copy_message(dump_channel, chat, sent_msg.id)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path is not None:
            os.remove(ph_path)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    await client.delete_messages(message.chat.id, [smsg.id])

def add_watermark_to_image(image_path, watermark_text, font_size=50):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(font_size)
    except Exception:
        font = ImageFont.load_default()
    width, height = image.size
    for _ in range(3):
        x = random.randint(0, width - 80)
        y = random.randint(0, height - 30)
        draw.text((x, y), watermark_text, font=font, fill=(255, 0, 0, 128))
    output_path = "watermarked_photo.jpg"
    image.save(output_path)
    return output_path

def add_text_to_thumbnail(video_path, text, time_point=1, font_size=70, default_image_url=None):
    try:
        video = VideoFileClip(video_path)
        thumbnail = video.get_frame(time_point)
        image = Image.fromarray(np.uint8(thumbnail))
    except Exception as e:
        print(f"Error extracting frame from video: {e}")
        if not default_image_url:
            raise ValueError("No default image URL provided.")
        try:
            response = requests.get(default_image_url, stream=True)
            response.raise_for_status()
            image = Image.open(response.raw).convert("RGB")
        except Exception as err:
            raise ValueError(f"Failed to download default image: {err}")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    if width > height:
        font_size = max(20, int(font_size * (width / 800)))
    else:
        font_size = max(20, int(font_size * (height / 800)))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    for _ in range(3):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = random.randint(0, max(0, width - text_width))
        y = random.randint(0, max(0, height - text_height))
        draw.text((x, y), text, fill="red", font=font)
    output_thumbnail_path = "edited_thumbnail.jpg"
    image.save(output_thumbnail_path)
    return output_thumbnail_path

def split_file(file_path, part_size):
    file_size = os.path.getsize(file_path)
    if file_size <= part_size:
        return [file_path]
    file_parts = []
    part_number = 1
    with open(file_path, 'rb') as f:
        while True:
            part_data = f.read(part_size)
            if not part_data:
                break
            part_file_name = f"{file_path}.part{str(part_number).zfill(3)}"
            part_file_path = os.path.join(os.path.dirname(file_path), part_file_name)
            with open(part_file_path, 'wb') as part_file:
                part_file.write(part_data)
            file_parts.append(part_file_path)
            part_number += 1
    return file_parts

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    if hasattr(msg, "document") and msg.document:
        return "Document"
    if hasattr(msg, "video") and msg.video:
        return "Video"
    if hasattr(msg, "animation") and msg.animation:
        return "Animation"
    if hasattr(msg, "sticker") and msg.sticker:
        return "Sticker"
    if hasattr(msg, "voice") and msg.voice:
        return "Voice"
    if hasattr(msg, "audio") and msg.audio:
        return "Audio"
    if hasattr(msg, "photo") and msg.photo:
        return "Photo"
    if hasattr(msg, "text") and msg.text:
        return "Text"
    return "Unknown"


# ...save.py ka pura logic upar...

# FSM state for settings menu
USER_STATE = {}

SETTING_TIMEOUT_SECONDS = 60

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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴅᴇꜱᴛɪɴᴀᴛɪᴏɴ", callback_data="dumpset_destination")],
        [InlineKeyboardButton("CLOSE", callback_data="dumpset_close")]
    ])

def destination_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏪ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="dumpset_main"),
            InlineKeyboardButton("❌ Remove Destination", callback_data="dumpset_remove_dest")
        ],
        [InlineKeyboardButton("CLOSE", callback_data="dumpset_close")]
    ])

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

@Client.on_callback_query(filters.regex(r"^dumpset_(\w+)$"))
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
        await msg.edit_text(
            destination_text(error="Invalid chat ID. Please enter a valid one (e.g., -1001234567890) or /cancel."),
            reply_markup=destination_kb()
        )
        start_timeout_task(client, user_id, msg, "awaiting_destination")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH)

if __name__ == "__main__":
    app.run()
