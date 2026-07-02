# main.py - Thanos Auto Uploader Bot (Complete)
import os
import sys
import asyncio
import datetime
import logging
import time
import re
import subprocess
import shutil
import aiohttp
import requests
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import FloodWait

# ---------- IMPORT ALL MODULES ----------
try:
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
except ImportError as e:
    logging.error(f"❌ Import error: {e}")
    sys.exit(1)

# ---------- BOT INITIALIZATION ----------
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

# ---------- REGISTER CLEAN HANDLER ----------
register_clean_handler(bot)

# ---------- DEFAULT SETTINGS ----------
DEFAULT_SETTINGS = {
    "auto_upload": True,
    "batch_upload": True,
    "resume": False,
    "downloader_name": "⚡ THANOS ⚡",
    "show_extension": True,
    "caption_style": "default",
    "show_title": True,
    "quality": "480",
    "thumbnail": "default",
    "pdf_watermark": False,
    "pdf_watermark_text": "",
    "auto_grouping": False,
    "video_player_link": True,
    "pw_token": "",
    "proxy": "",
    "sticker_responses": True,
    "watermark": "/d",
}

# ---------- SETTINGS FUNCTIONS ----------
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

# ---------- SETTINGS MENU ----------
def settings_menu_markup(user_id: int) -> InlineKeyboardMarkup:
    settings = get_user_settings(user_id)
    buttons = []
    status = lambda key: "✅" if settings.get(key) else "❌"
    buttons.append([InlineKeyboardButton(f"Auto Upload {status('auto_upload')}", callback_data="set_auto_upload_toggle")])
    buttons.append([InlineKeyboardButton(f"Batch Upload {status('batch_upload')}", callback_data="set_batch_upload_toggle")])
    buttons.append([InlineKeyboardButton(f"Quality: {settings['quality']}p", callback_data="set_quality")])
    buttons.append([InlineKeyboardButton(f"Caption Style: {settings['caption_style']}", callback_data="set_caption_style")])
    buttons.append([InlineKeyboardButton(f"Watermark: {'On' if settings['watermark']!='/d' else 'Off'}", callback_data="set_watermark")])
    buttons.append([InlineKeyboardButton(f"PDF Watermark {status('pdf_watermark')}", callback_data="set_pdf_watermark_toggle")])
    buttons.append([InlineKeyboardButton(f"Auto Grouping {status('auto_grouping')}", callback_data="set_auto_grouping_toggle")])
    buttons.append([InlineKeyboardButton(f"Proxy: {'Set' if settings['proxy'] else 'Not Set'}", callback_data="set_proxy")])
    buttons.append([InlineKeyboardButton("📋 View Schedules", callback_data="view_schedules")])
    buttons.append([InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ---------- SETTINGS COMMAND ----------
@bot.on_message(filters.command("setting") & filters.private)
async def settings_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(
        "⚙️ **Settings Menu**\n\nChoose an option to modify:",
        reply_markup=settings_menu_markup(user_id)
    )

# ---------- SETTINGS CALLBACK ----------
@bot.on_callback_query()
async def settings_callback(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    bot_username = client.me.username
    settings = get_user_settings(user_id, bot_username)

    if data.endswith("_toggle"):
        key = data.replace("set_", "").replace("_toggle", "")
        current = settings.get(key, False)
        update_setting(user_id, key, not current, bot_username)
        await query.answer(f"✅ {key.replace('_',' ').title()} set to {not current}")
        await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_quality":
        qualities = ["144", "240", "360", "480", "720", "1080"]
        buttons = []
        for q in qualities:
            check = " ✅" if settings.get("quality") == q else ""
            buttons.append([InlineKeyboardButton(f"{q}p{check}", callback_data=f"set_quality_{q}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text(
            "📐 **Select Upload Quality:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("set_quality_"):
        q = data.replace("set_quality_", "")
        update_setting(user_id, "quality", q, bot_username)
        await query.answer(f"Quality set to {q}p")
        await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_caption_style":
        styles = ["default", "minimal", "detailed"]
        buttons = []
        for style in styles:
            check = " ✅" if settings.get("caption_style") == style else ""
            buttons.append([InlineKeyboardButton(f"{style}{check}", callback_data=f"set_caption_style_{style}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text(
            "🎨 **Select Caption Style:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("set_caption_style_"):
        style = data.replace("set_caption_style_", "")
        update_setting(user_id, "caption_style", style, bot_username)
        await query.answer(f"Caption style set to {style}")
        await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_watermark":
        await query.answer()
        msg = await query.message.reply_text("✏️ Send watermark text or /d for none:")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.text:
                update_setting(user_id, "watermark", input_msg.text.strip(), bot_username)
                await input_msg.delete()
                await msg.edit_text("✅ Watermark updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "set_proxy":
        await query.answer()
        msg = await query.message.reply_text("🌐 Send proxy URL (or /cancel):")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.text and input_msg.text != "/cancel":
                update_setting(user_id, "proxy", input_msg.text.strip(), bot_username)
                await msg.edit_text("✅ Proxy updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            else:
                await msg.edit_text("❌ Cancelled.")
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "view_schedules":
        schedules = db.get_schedules(bot_username)
        if not schedules:
            await query.answer("No active schedules.")
            return
        text = "📋 **Active Schedules**\n\n"
        for s in schedules:
            text += f"• Batch: `{s['batch_id']}` | Time: {s['time']} | Source: {s['source']}\n"
        await query.message.reply_text(text)
        return

    if data == "main_menu":
        await query.message.edit_text(
            "⚙️ **Settings Menu**\n\nChoose an option:",
            reply_markup=settings_menu_markup(user_id)
        )
        return

    await query.answer("Unknown option")

# ---------- MAIN PROCESSOR (CORE ENGINE) ----------
async def process_link_list(client: Client, links: list, b_name: str, user_id: int, channel_id: int, settings: dict = None):
    if settings is None:
        settings = get_user_settings(user_id, client.me.username)
    
    quality = settings.get('quality', '480')
    watermark_text = settings.get('watermark', '/d')
    credit = settings.get('downloader_name', CREDIT)
    thumb_setting = settings.get('thumbnail', 'default')
    caption_style = settings.get('caption_style', 'default')
    proxy = settings.get('proxy', '')
    pw_token = settings.get('pw_token', '')
    
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
            # ----- URL TRANSFORMATIONS -----
            if "visionias" in url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as resp:
                        text = await resp.text()
                        match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                        if match:
                            url = match.group(1)
            
            if "classplusapp" in url or "media-cdn.classplusapp.com" in url:
                if pw_token:
                    url = f"{url}?token={pw_token}"
            
            if ".pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"
            
            if 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]
            
            # ----- PREPARE DOWNLOAD -----
            if "youtu" in url or "youtube.com" in url:
                ytf = f"bv*[height<={quality}][ext=mp4]+ba[ext=m4a]/b[height<=?{quality}]"
            else:
                ytf = f"b[height<={quality}]/bv[height<={quality}]+ba/b/bv+ba"

            cmd = f'yt-dlp -f "{ytf}" {proxy_flag} "{url}" -o "{name}.mp4" --no-check-certificate'
            
            # ----- HANDLE PDF -----
            if ".pdf" in url:
                await helper.pdf_download(url, f"{name}.pdf")
                ext_actual = "pdf"
                cc = (
                    f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                    f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                    f"<b>📥 Title:</b> {name}\n\n"
                    f"[{date_str}]\n\n"
                    f"<b>📤 Extension:</b> {credit} .{ext_actual}\n"
                    f"<b>🍁 Uploaded By:</b> {credit}\n\n"
                    f"{time_str}"
                )
                await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc)
                os.remove(f'{name}.pdf')
                count += 1
                continue
            
            # ----- HANDLE IMAGES -----
            if any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png"]):
                ext_actual = url.split('.')[-1]
                cmd = f'yt-dlp -o "{name}.{ext_actual}" "{url}"'
                os.system(cmd)
                cc = f"<b>📎 Batch:</b> {batch_blockquote}\n<b>📥 Title:</b> {name}\n<b>🍁 By:</b> {credit}"
                await bot.send_photo(chat_id=channel_id, photo=f'{name}.{ext_actual}', caption=cc)
                os.remove(f'{name}.{ext_actual}')
                count += 1
                continue
            
            # ----- HANDLE VIDEOS -----
            Show = f"<i><b>📥 Downloading:</b></i>\n<blockquote>{name}</blockquote>"
            prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
            
            res_file = await helper.download_video(url, cmd, name)
            await prog.delete(True)
            
            if os.path.exists(res_file):
                # ----- GENERATE THUMBNAIL -----
                if thumb_setting == "default" or not os.path.exists(thumb_setting):
                    temp_thumb = f"downloads/thumb_{name}.jpg"
                    os.makedirs("downloads", exist_ok=True)
                    subprocess.run(
                        f'ffmpeg -i "{res_file}" -ss 00:00:10 -vframes 1 -q:v 2 -y "{temp_thumb}"',
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    thumb_path = temp_thumb if os.path.exists(temp_thumb) else None
                else:
                    thumb_path = thumb_setting
                
                # ----- CAPTION -----
                ext = os.path.splitext(res_file)[1].lstrip('.')
                if caption_style == "minimal":
                    cc = f"<b>{name}</b>\n{credit}"
                elif caption_style == "detailed":
                    size = os.path.getsize(res_file)
                    cc = f"<b>{name}</b>\nSize: {helper.human_readable_size(size)}\nQuality: {quality}p\n{credit}"
                else:
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {credit} .{ext}\n"
                        f"<b>🧩 Resolution:</b> {quality}p\n\n"
                        f"<b>🍁 Uploaded By:</b> {credit}\n\n"
                        f"{time_str}"
                    )
                
                # ----- SEND VIDEO -----
                await helper.send_vid(
                    client, None, cc, res_file, thumb_path, name, 
                    None, channel_id, watermark=watermark_text
                )
                count += 1
            else:
                await bot.send_message(channel_id, f"❌ Failed: {name}")
                failed_count += 1
                count += 1
                
        except Exception as e:
            logging.error(f"Error processing {name}: {e}")
            failed_count += 1
            count += 1
            await bot.send_message(channel_id, f"❌ Failed: {name}\nError: {str(e)[:100]}")
    
    # ----- SUMMARY -----
    success = total - failed_count
    summary = (
        f"✅ **Batch Completed**\n\n"
        f"📚 Batch: {b_name}\n"
        f"Total: {total}\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed_count}\n\n"
        f"⚡ THANOS AUTO UPLOADER"
    )
    await bot.send_message(channel_id, summary)

# ---------- FETCH COMMANDS ----------
@bot.on_message(filters.command("fetch") & filters.private)
async def fetch_generic(client: Client, message: Message):
    if not db.is_user_authorized(message.from_user.id, client.me.username):
        await message.reply("❌ Not authorized. Contact admin.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /fetch <batch_id>")
        return
    
    batch_id = args[1]
    status_msg = await message.reply(f"⏳ Fetching batch {batch_id}...")
    
    try:
        links = await fetch_generic_batch_links(batch_id)
        if not links:
            await status_msg.edit("❌ No links found or API error.")
            return
        
        await status_msg.edit(f"✅ Found {len(links)} items. Starting upload...")
        settings = get_user_settings(message.from_user.id, client.me.username)
        await process_link_list(
            client, links, f"Batch_{batch_id}", 
            message.from_user.id, message.chat.id, settings
        )
    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)[:200]}")

@bot.on_message(filters.command("fetchcw") & filters.private)
async def fetch_cw(client: Client, message: Message):
    if not db.is_user_authorized(message.from_user.id, client.me.username):
        await message.reply("❌ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /fetchcw <batch_id>")
        return
    
    batch_id = args[1]
    status_msg = await message.reply(f"⏳ Fetching CW batch {batch_id}...")
    
    try:
        links = await fetch_cw_batch_links(batch_id)
        if not links:
            await status_msg.edit("❌ No links found.")
            return
        
        await status_msg.edit(f"✅ Found {len(links)} items. Starting upload...")
        settings = get_user_settings(message.from_user.id, client.me.username)
        await process_link_list(
            client, links, f"CW_{batch_id}", 
            message.from_user.id, message.chat.id, settings
        )
    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)[:200]}")

@bot.on_message(filters.command("fetchcareerwill") & filters.private)
async def fetch_careerwill(client: Client, message: Message):
    if not db.is_user_authorized(message.from_user.id, client.me.username):
        await message.reply("❌ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /fetchcareerwill <batch_id>")
        return
    
    batch_id = args[1]
    status_msg = await message.reply(f"⏳ Fetching Careerwill batch {batch_id}...")
    
    try:
        links = await fetch_careerwill_batch_links(batch_id)
        if not links:
            await status_msg.edit("❌ No links found.")
            return
        
        await status_msg.edit(f"✅ Found {len(links)} items. Starting upload...")
        settings = get_user_settings(message.from_user.id, client.me.username)
        await process_link_list(
            client, links, f"Careerwill_{batch_id}", 
            message.from_user.id, message.chat.id, settings
        )
    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)[:200]}")

# ---------- SCHEDULE COMMANDS ----------
@bot.on_message(filters.command("schedulefetch") & filters.private)
async def schedule_fetch_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.reply("Usage: /schedulefetch <batch_id> <HH:MM> <source> [channel_id]\nsource: generic, cw, careerwill")
        return
    
    batch_id = args[1]
    time_str = args[2]
    source = args[3]
    channel_id = int(args[4]) if len(args) > 4 else message.chat.id
    
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except:
        await message.reply("❌ Invalid time. Use HH:MM (24h).")
        return
    
    db.add_schedule(message.from_user.id, client.me.username, batch_id, time_str, source, channel_id)
    await message.reply(f"✅ Scheduled fetch for batch `{batch_id}` daily at `{time_str}`")

@bot.on_message(filters.command("removeschedule") & filters.private)
async def remove_schedule_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /removeschedule <batch_id>")
        return
    
    batch_id = args[1]
    db.remove_schedule(message.from_user.id, client.me.username, batch_id)
    await message.reply(f"✅ Removed schedule for batch `{batch_id}`.")

@bot.on_message(filters.command("viewschedules") & filters.private)
async def view_schedules_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    schedules = db.get_schedules(client.me.username)
    if not schedules:
        await message.reply("No active schedules.")
        return
    
    text = "📋 **Active Schedules**\n\n"
    for s in schedules:
        text += f"• Batch: `{s['batch_id']}` | Time: {s['time']} | Source: {s['source']}\n"
    await message.reply(text)

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
                
                # Fetch links based on source
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
                    await process_link_list(
                        bot, links, f"Scheduled_{batch_id}", 
                        user_id, channel_id, settings
                    )
                else:
                    await bot.send_message(OWNER_ID, f"⚠️ No links for scheduled batch {batch_id}")
                
                db.update_last_run(user_id, bot_username, batch_id, date_str)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")

# ---------- START COMMAND ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply(
        "**⚡ THANOS AUTO UPLOADER ⚡**\n\n"
        "🚀 **Bot is Live!**\n\n"
        "📌 **Commands:**\n"
        "• /fetch <batch_id> - Fetch & upload batch\n"
        "• /fetchcw <batch_id> - CW batch\n"
        "• /fetchcareerwill <batch_id> - Careerwill batch\n"
        "• /schedulefetch <batch_id> HH:MM source - Schedule daily\n"
        "• /viewschedules - List all schedules\n"
        "• /removeschedule <batch_id> - Remove schedule\n"
        "• /setting - Configure settings\n"
        "• /drm - Upload from TXT file\n\n"
        "👑 **Admin Commands:**\n"
        "• /add <user_id> <days> - Add user\n"
        "• /remove <user_id> - Remove user\n"
        "• /users - List all users\n"
        "• /clean - Clean files\n\n"
        f"✨ **Powered By:** ⚡ THANOS ⚡"
    )

# ---------- DRM COMMAND ----------
@bot.on_message(filters.command("drm") & filters.private)
async def drm_handler(client: Client, message: Message):
    if not db.is_user_authorized(message.from_user.id, client.me.username):
        await message.reply("❌ Not authorized.")
        return
    
    await message.reply(
        "📤 **Upload TXT File**\n\n"
        "Send a .txt file with format:\n"
        "`Name: URL`\n\n"
        "Example:\n"
        "`Mathematics: https://example.com/video.mp4`"
    )
    
    try:
        input_msg: Message = await client.listen(message.chat.id, timeout=60)
        if not input_msg.document or not input_msg.document.file_name.endswith('.txt'):
            await message.reply("❌ Please send a valid .txt file.")
            return
        
        file_path = await input_msg.download()
        links = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' in line and 'http' in line:
                    name, url = line.split(':', 1)
                    links.append((name.strip(), url.strip()))
        
        if not links:
            await message.reply("❌ No valid links found.")
            os.remove(file_path)
            return
        
        b_name = os.path.splitext(os.path.basename(file_path))[0]
        await message.reply(f"✅ Found {len(links)} links. Starting upload...")
        
        settings = get_user_settings(message.from_user.id, client.me.username)
        await process_link_list(
            client, links, b_name, 
            message.from_user.id, message.chat.id, settings
        )
        os.remove(file_path)
    except asyncio.TimeoutError:
        await message.reply("⏰ Timeout. Please try again.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)[:200]}")

# ---------- AUTH COMMANDS ----------
@bot.on_message(filters.command("add") & filters.private)
async def add_user_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /add <user_id> <days>")
        return
    
    try:
        user_id = int(args[1])
        days = int(args[2])
        
        try:
            user = await client.get_users(user_id)
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
        except:
            name = f"User_{user_id}"
        
        success, expiry_date = db.add_user(user_id, name, days, client.me.username)
        if success:
            await message.reply(f"✅ User added!\nName: {name}\nID: {user_id}\nExpiry: {expiry_date.strftime('%d-%m-%Y')}")
        else:
            await message.reply("❌ Failed to add user.")
    except ValueError:
        await message.reply("❌ Invalid user ID or days.")

@bot.on_message(filters.command("remove") & filters.private)
async def remove_user_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /remove <user_id>")
        return
    
    try:
        user_id = int(args[1])
        if db.remove_user(user_id, client.me.username):
            await message.reply(f"✅ User {user_id} removed.")
        else:
            await message.reply(f"❌ User {user_id} not found.")
    except ValueError:
        await message.reply("❌ Invalid user ID.")

@bot.on_message(filters.command("users") & filters.private)
async def list_users_cmd(client: Client, message: Message):
    if not db.is_admin(message.from_user.id):
        await message.reply("⚠️ Not authorized.")
        return
    
    users = db.list_users(client.me.username)
    if not users:
        await message.reply("📝 No users found.")
        return
    
    text = "📝 **Users List**\n\n"
    for user in users:
        expiry = user['expiry_date']
        if isinstance(expiry, str):
            expiry = datetime.datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
        days_left = (expiry - datetime.datetime.now()).days
        text += f"• {user['name']} (`{user['user_id']}`) - {days_left} days left\n"
    
    await message.reply(text)

@bot.on_message(filters.command("plan") & filters.private)
async def my_plan_cmd(client: Client, message: Message):
    user = db.get_user(message.from_user.id, client.me.username)
    if not user:
        await message.reply("❌ No active plan.")
        return
    
    expiry = user['expiry_date']
    if isinstance(expiry, str):
        expiry = datetime.datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
    days_left = (expiry - datetime.datetime.now()).days
    
    await message.reply(
        f"**📱 Plan Details**\n\n"
        f"• Name: {user['name']}\n"
        f"• Days Left: {days_left}\n"
        f"• Expires: {expiry.strftime('%d-%m-%Y')}"
    )

# ---------- MAIN ----------
async def main():
    try:
        print("🚀 Starting Thanos Auto Uploader Bot...")
        await bot.start()
        print("✅ Bot started successfully!")
        print("📌 Bot Username: @", bot.me.username)
        
        # Start scheduler
        asyncio.create_task(scheduler_loop())
        print("✅ Scheduler started!")
        
        await idle()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        raise
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
