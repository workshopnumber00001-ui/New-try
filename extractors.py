import aiohttp
import asyncio
import re
import logging
from vars import *

logging.basicConfig(level=logging.INFO)

async def fetch_with_retry(session, url, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        await asyncio.sleep(1)
    return None

async def fetch_generic_batch_links(batch_id: str):
    """API_BASE से batch_id के सभी classes/PDF fetch करके list of (name, url) लौटाता है"""
    links = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        data = await fetch_with_retry(session, f"{API_BASE}/courses/{batch_id}/classes?populate=full")
        if not data:
            return []
        topics = data.get("data", {}).get("classes", [])
        for topic in topics:
            topic_name = topic.get('topicName', 'General')
            for cls in topic.get("classes", []):
                title = cls.get('title', 'Untitled').strip()
                v_link = cls.get('class_link')
                if v_link:
                    links.append((f"[{topic_name}] {title} (VIDEO)", v_link))
                for pdf in cls.get("classPdf", []):
                    p_url = pdf.get("url") if isinstance(pdf, dict) else str(pdf)
                    if p_url:
                        links.append((f"[{topic_name}] {title} (PDF)", p_url))
    return links

async def fetch_cw_batch_links(batch_id: str):
    links = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        topics_data = await fetch_with_retry(session, CW_BATCH_API.format(batch_id))
        if not topics_data:
            return []
        batch_details = topics_data.get('data', topics_data) if isinstance(topics_data, dict) else topics_data
        topics = batch_details.get('topics', []) if isinstance(batch_details, dict) else batch_details
        if not isinstance(topics, list):
            return []
        
        for topic in topics:
            topic_name = topic.get('topicName') or topic.get('name') or 'Unnamed Topic'
            topic_id = topic.get('topicId') or topic.get('id') or topic.get('_id')
            if not topic_id:
                continue
            content_url = CW_TOPIC_API.format(batch_id, topic_id)
            content_json = await fetch_with_retry(session, content_url)
            if not content_json:
                continue
            inner_data = content_json.get('data', content_json) if isinstance(content_json, dict) else content_json
            raw_videos = inner_data.get('classes', []) or inner_data.get('videos', []) or inner_data.get('class', [])
            raw_pdfs = inner_data.get('notes', []) or inner_data.get('pdfs', []) or inner_data.get('batch-notes', [])
            
            for vid in raw_videos:
                vid_name = vid.get('title') or vid.get('videoName') or vid.get('name') or 'Video'
                raw_token = vid.get('video_url') or vid.get('videoLink') or vid.get('url') or vid.get('link')
                if raw_token:
                    # यहाँ आप CW decryption API call कर सकते हैं (ram.py के अनुसार)
                    # हम short cut में raw_token को URL मान रहे हैं
                    links.append((f"[{topic_name}] {vid_name}", raw_token))
            for pdf in raw_pdfs:
                pdf_name = pdf.get('title') or pdf.get('pdfName') or pdf.get('name') or 'Document'
                pdf_url = pdf.get('download_url') or pdf.get('view_url') or pdf.get('pdfLink') or 'No Link'
                if pdf_url and pdf_url != 'No Link':
                    links.append((f"[{topic_name}] {pdf_name} (PDF)", pdf_url))
    return links

async def fetch_careerwill_batch_links(batch_id: str):
    links = []
    headers = CAREERWILL_HEADERS.copy()
    async with aiohttp.ClientSession(headers=headers) as session:
        build_id = CAREERWILL_BUILD_ID
        if not build_id:
            async with session.get("https://web.careerwill.com/live-classes") as resp:
                html = await resp.text()
                match = re.search(r'/_next/static/([^/]+)/_buildManifest', html)
                if match:
                    build_id = match.group(1)
        if not build_id:
            return []
        base_url = f"https://web.careerwill.com/_next/data/{build_id}"
        batch_url = f"{base_url}/live-classes/{batch_id}.json?interface_id=1"
        data = await fetch_with_retry(session, batch_url)
        if not data:
            return []
        batch_class_data = data.get("pageProps", {}).get("batchClassData", {})
        classes = batch_class_data.get("classes", [])
        for cls in classes:
            lesson_name = cls.get('lessonName', 'Untitled')
            lesson_url = cls.get('lessonUrl', '')
            if lesson_url:
                if not lesson_url.startswith('http'):
                    video_url = f"https://www.youtube.com/watch?v={lesson_url}"
                else:
                    video_url = lesson_url
                links.append((lesson_name, video_url))
    return links
