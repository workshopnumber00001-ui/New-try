import os
import sys
import asyncio
import datetime
import logging
import time
import re
import shutil
import io
import zipfile
import aiohttp
import requests
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import FloodWait

import auth
import thanos as helper
from extractors import fetch_generic_batch_links, fetch_cw_batch_links, fetch_careerwill_batch_links
from html_handler import html_handler
from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *
from db import db
from pyromod import listen

bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

register_clean_handler(bot)

# ---------- SETTINGS ----------
DEFAULT_SETTINGS = {
    "auto_upload": True,
    "batch_upload": True,
    "resume": False,
    "downloader_name": "🥀°𓏲кяιѕнηα⋆🌿",
    "show_extension": True,
    "caption_style": "default",
    "show_title": True,
    "quality": "480",
    "thumbnail": "default",
    "pdf_watermark": False,
    "pdf_watermark_text": "",
    "auto_grouping": False,
    "video_player_link": True,
    "pw_token": "your_token_here",
    "proxy": "",
    "sticker_responses": True,
    "watermark": "/d",
}

def get_user_settings(user_id: int, bot_username: str = None):
    if bot_username is None:
        bot_username = bot.me.username
    settings = db.get_user_settings(user_id, bot_username)
    final = DEFAULT_SETTINGS.copy()
    final.update(settings)
    return final

def update_setting(user_id: int, key: str, value, bot_username: str = None):
    if bot_username is None:
        bot_username = bot.me.username
    db.update_user_setting(user_id, bot_username, key, value)

# ---------- PROGRESS BAR (alias) ----------
async def progress(current, total, reply, start):
    await progress_bar(current, total, reply, start)

# ---------- MAIN PROCESSOR ----------
async def process_link_list(client: Client, links: list, b_name: str, user_id: int, channel_id: int, settings: dict = None):
    if settings is None:
        settings = get_user_settings(user_id, client.me.username)
    
    quality = settings.get('quality', '480')
    watermark_text = settings.get('watermark', '/d')
    credit = settings.get('downloader_name', CREDIT)
    thumb_setting = settings.get('thumbnail', 'default')
    pw_token = settings.get('pw_token', '')
    proxy = settings.get('proxy', '')
    caption_style = settings.get('caption_style', 'default')
    
    proxy_flag = f"--proxy {proxy}" if proxy else ""
    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    current_ist = datetime.datetime.now(IST)
    date_str = current_ist.strftime('%d-%m-%Y')
    time_str = current_ist.strftime('%A, %d %B %Y • %I:%M %p')
    batch_blockquote = f'<blockquote>{b_name}</blockquote>'

    count = 1
    failed_count = 0
    total = len(links)

    for name, url in links:
        try:
            # --- URL Transformations (example, include your full logic) ---
            # यहाँ आप अपने txt_handler के सभी transformations डालें
            # ...

            # Simplified download command
            cmd = f'yt-dlp -f "b[height<={quality}]" {proxy_flag} "{url}" -o "{name}.mp4"'
            res_file = await helper.download_video(url, cmd, name)
            if not os.path.exists(res_file):
                raise Exception("Download failed")

            # Thumbnail
            if thumb_setting == "default" or not os.path.exists(thumb_setting):
                temp_thumb = f"downloads/thumb_{name}.jpg"
                subprocess.run(f'ffmpeg -i "{res_file}" -ss 00:00:10 -vframes 1 -q:v 2 -y "{temp_thumb}"', shell=True)
                thumb_path = temp_thumb if os.path.exists(temp_thumb) else None
            else:
                thumb_path = thumb_setting

            # Caption
            ext = os.path.splitext(res_file)[1].lstrip('.')
            if caption_style == "minimal":
                cc = f"<b>{name}</b>\n{credit}"
            elif caption_style == "detailed":
                size = os.path.getsize(res_file)
                cc = f"<b>{name}</b>\nSize: {helper.human_readable_size(size)}\nResolution: {quality}p\n{credit}"
            else:
                cc = f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n<b>📎 Batch:</b> {batch_blockquote}\n\n<b>📥 Title:</b> {name}\n\n[{date_str}]\n\n<b>📤 Extension:</b> {credit} .{ext}\n<b>🧩 Resolution:</b> {quality}p\n\n<b>🍁 Uploaded By:</b> {credit}\n\n{time_str}"

            # Send
            prog = await client.send_message(channel_id, f"📤 Uploading {name}...")
            await helper.send_vid(client, None, cc, res_file, thumb_path, name, prog, channel_id, watermark=watermark_text)
            count += 1
        except Exception as e:
            logging.error(f"Error processing {name}: {e}")
            failed_count += 1
            await client.send_message(channel_id, f"❌ Failed: {name}\nError: {str(e)}")

    success = total - failed_count
    summary = f"✅ **Batch Completed**\n📚 {b_name}\nTotal: {total}\n✅ Success: {success}\n❌ Failed: {failed_count}"
    await client.send_message(channel_id, summary)

# ---------- FETCH COMMANDS ----------
@bot.on_message(filters.command("fetch") & filters.private)
async def fetch_generic(client: Client, m: Message):
    if not db.is_user_authorized(m.from_user.id, client.me.username):
        await m.reply("❌ Not authorized.")
        return
    args = m.text.split()
    if len(args) < 2:
        await m.reply("Usage: /fetch <batch_id>")
        return
    batch_id = args[1]
    status = await m.reply(f"⏳ Fetching batch {batch_id}...")
    links = await fetch_generic_batch_links(batch_id)
    if not links:
        await status.edit("❌ No links found.")
        return
    await status.edit(f"✅ {len(links)} items found. Starting upload...")
    settings = get_user_settings(m.from_user.id, client.me.username)
    await process_link_list(client, links, f"Batch_{batch_id}", m.from_user.id, m.chat.id, settings)

@bot.on_message(filters.command("fetchcw") & filters.private)
async def fetch_cw(client: Client, m: Message):
    if not db.is_user_authorized(m.from_user.id, client.me.username):
        await m.reply("❌ Not authorized.")
        return
    args = m.text.split()
    if len(args) < 2:
        await m.reply("Usage: /fetchcw <batch_id>")
        return
    batch_id = args[1]
    status = await m.reply(f"⏳ Fetching CW batch {batch_id}...")
    links = await fetch_cw_batch_links(batch_id)
    if not links:
        await status.edit("❌ No links found.")
        return
    await status.edit(f"✅ {len(links)} items found. Starting upload...")
    settings = get_user_settings(m.from_user.id, client.me.username)
    await process_link_list(client, links, f"CW_{batch_id}", m.from_user.id, m.chat.id, settings)

@bot.on_message(filters.command("fetchcareerwill") & filters.private)
async def fetch_careerwill(client: Client, m: Message):
    if not db.is_user_authorized(m.from_user.id, client.me.username):
        await m.reply("❌ Not authorized.")
        return
    args = m.text.split()
    if len(args) < 2:
        await m.reply("Usage: /fetchcareerwill <batch_id>")
        return
    batch_id = args[1]
    status = await m.reply(f"⏳ Fetching Careerwill batch {batch_id}...")
    links = await fetch_careerwill_batch_links(batch_id)
    if not links:
        await status.edit("❌ No links found.")
        return
    await status.edit(f"✅ {len(links)} items found. Starting upload...")
    settings = get_user_settings(m.from_user.id, client.me.username)
    await process_link_list(client, links, f"Careerwill_{batch_id}", m.from_user.id, m.chat.id, settings)

# ---------- SCHEDULE COMMANDS ----------
@bot.on_message(filters.command("schedulefetch") & filters.private)
async def schedule_fetch_cmd(client: Client, m: Message):
    if not db.is_admin(m.from_user.id):
        await m.reply("⚠️ Not authorized.")
        return
    args = m.text.split()
    if len(args) < 4:
        await m.reply("Usage: /schedulefetch <batch_id> <HH:MM> <source> [channel_id]\nsource: generic, cw, careerwill")
        return
    batch_id = args[1]
    time_str = args[2]
    source = args[3]
    channel_id = int(args[4]) if len(args) > 4 else m.chat.id
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except:
        await m.reply("❌ Invalid time. Use HH:MM (24h).")
        return
    db.add_schedule(m.from_user.id, client.me.username, batch_id, time_str, source, channel_id)
    await m.reply(f"✅ Scheduled fetch for batch `{batch_id}` daily at `{time_str}` (source: {source}). Will upload to channel {channel_id}.")

@bot.on_message(filters.command("removeschedule") & filters.private)
async def remove_schedule_cmd(client: Client, m: Message):
    if not db.is_admin(m.from_user.id):
        await m.reply("⚠️ Not authorized.")
        return
    args = m.text.split()
    if len(args) < 2:
        await m.reply("Usage: /removeschedule <batch_id>")
        return
    batch_id = args[1]
    db.remove_schedule(m.from_user.id, client.me.username, batch_id)
    await m.reply(f"✅ Removed schedule for batch `{batch_id}`.")

@bot.on_message(filters.command("viewschedules") & filters.private)
async def view_schedules_cmd(client: Client, m: Message):
    if not db.is_admin(m.from_user.id):
        await m.reply("⚠️ Not authorized.")
        return
    schedules = db.get_schedules(client.me.username)
    if not schedules:
        await m.reply("No active schedules.")
        return
    text = "📋 **Active Schedules**\n\n"
    for s in schedules:
        text += f"• Batch: `{s['batch_id']}` | Time: {s['time']} | Source: {s['source']} | Channel: {s.get('channel_id', 'N/A')}\n"
    await m.reply(text)

# ---------- SCHEDULER LOOP ----------
async def scheduler_loop():
    while True:
        await asyncio.sleep(60)
        try:
            bot_username = bot.me.username
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
            time_str = now.strftime("%H:%M")
            date_str = now.strftime("%Y-%m-%d")
            schedules = db.get_due_schedules(bot_username, time_str, date_str)
            for sched in schedules:
                user_id = sched['user_id']
                batch_id = sched['batch_id']
                source = sched.get('source', 'generic')
                channel_id = sched.get('channel_id', OWNER_ID)
                if source == 'generic':
                    links = await fetch_generic_batch_links(batch_id)
                elif source == 'cw':
                    links = await fetch_cw_batch_links(batch_id)
                elif source == 'careerwill':
                    links = await fetch_careerwill_batch_links(batch_id)
                else:
                    continue
                if links:
                    settings = get_user_settings(user_id, bot_username)
                    await process_link_list(bot, links, f"Scheduled_{batch_id}", user_id, channel_id, settings)
                else:
                    await bot.send_message(OWNER_ID, f"⚠️ No links for scheduled batch {batch_id}")
                db.update_last_run(user_id, bot_username, batch_id, date_str)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")

# ---------- START COMMAND ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, m: Message):
    await m.reply(
        "**🚀 Auto Uploader Bot**\n\n"
        "Commands:\n"
        "/fetch <batch_id> - Fetch & upload batch\n"
        "/fetchcw <batch_id> - CW batch\n"
        "/fetchcareerwill <batch_id> - Careerwill batch\n"
        "/schedulefetch <batch_id> HH:MM source - Schedule daily\n"
        "/viewschedules - List schedules\n"
        "/removeschedule <batch_id> - Remove schedule\n"
        "/setting - Configure settings\n"
        "/drm - Upload from TXT file\n"
        "/add, /remove, /users - Admin commands"
    )

# ---------- SETTINGS CALLBACK (short version) ----------
@bot.on_message(filters.command("setting") & filters.private)
async def settings_cmd(client: Client, m: Message):
    # यहाँ आप अपनी पूरी settings मेन्यू लॉजिक डालें
    await m.reply("⚙️ Settings command - implement as per your need.")

# ---------- OTHER COMMANDS ----------
@bot.on_message(filters.command("drm") & filters.private)
async def drm_txt_handler(client: Client, m: Message):
    await m.reply("📤 Please upload a .txt file with Name: URL format. (Full implementation not shown here for brevity)")

# ---------- MAIN ----------
async def main():
    await bot.start()
    asyncio.create_task(scheduler_loop())
    await idle()
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
