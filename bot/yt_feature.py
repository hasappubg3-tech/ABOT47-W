from .shared import *
import asyncio
import uuid
import os

YT_TMP = "/tmp"

def format_duration(secs):
    if not secs:
        return ""
    try:
        secs = int(secs)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except Exception:
        return ""

def yt_search_sync(query: str, limit: int = 10):
    import yt_dlp
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        entries = results.get("entries", []) or []
        out = []
        for e in entries:
            if not e:
                continue
            out.append({
                "id": e.get("id") or e.get("url", ""),
                "title": e.get("title", "بدون عنوان"),
                "duration": e.get("duration"),
                "channel": e.get("channel") or e.get("uploader", ""),
            })
        return out

async def yt_search(query: str, limit: int = 10):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, yt_search_sync, query, limit)
    except Exception as e:
        logging.warning(f"yt_search error: {e}")
        return []

def _download_video_sync(video_id: str):
    import yt_dlp
    uid_str = uuid.uuid4().hex
    out_tmpl = f"{YT_TMP}/ytvid_{uid_str}.%(ext)s"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
        "max_filesize": 49 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        title = info.get("title", "فيديو")
        duration = info.get("duration")
        for ext in ("mp4", "mkv", "webm", "avi", "mov"):
            path = f"{YT_TMP}/ytvid_{uid_str}.{ext}"
            if os.path.exists(path):
                return path, title, duration
    return None, None, None

def _download_audio_sync(video_id: str):
    import yt_dlp
    uid_str = uuid.uuid4().hex
    out_tmpl = f"{YT_TMP}/ytaud_{uid_str}.%(ext)s"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_tmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "max_filesize": 49 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        title = info.get("title", "صوت")
        duration = info.get("duration")
        mp3_path = f"{YT_TMP}/ytaud_{uid_str}.mp3"
        if os.path.exists(mp3_path):
            return mp3_path, title, duration
        for ext in ("m4a", "webm", "ogg", "opus"):
            path = f"{YT_TMP}/ytaud_{uid_str}.{ext}"
            if os.path.exists(path):
                return path, title, duration
    return None, None, None

async def download_yt_video(video_id: str):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _download_video_sync, video_id)
    except Exception as e:
        logging.warning(f"download_yt_video error: {e}")
        return None, None, None

async def download_yt_audio(video_id: str):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _download_audio_sync, video_id)
    except Exception as e:
        logging.warning(f"download_yt_audio error: {e}")
        return None, None, None

def cleanup_tmp(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def default_yt_prompt():
    return (
        "🎬 *بحث يوتيوب*\n\n"
        "أرسل عنوان الفيديو أو الأغنية التي تريد البحث عنها:"
    )
