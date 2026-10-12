import os
import time
import threading
import re
import requests
import json
import yt_dlp
from zlapi.models import Message, Mention, MultiMsgStyle, MessageStyle, ThreadType
from config import PREFIX, HEADER_STYLE

# ================= CẤU HÌNH =================
CACHE_DIR = "modules/cache/autodl_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

# Thumbnail dự phòng
FALLBACK_THUMB = "https://i.imgur.com/Ld1D5bA.jpeg"

des = {
    'version': "2.3.0",
    'credits': "Quocbaoo (Fixed by AI)",
    'description': "Tải video (Fix lỗi thiếu FFmpeg)",
    'power': "Thành viên"
}

def reply_msg(client, message_object, thread_id, thread_type, author_id, text_content, ttl=15000):
    """Gửi tin nhắn có HEADER_STYLE - header màu đỏ/đậm, không áp style cho nội dung"""
    header = str(HEADER_STYLE) if HEADER_STYLE else ""

    if thread_type == ThreadType.USER:
        full_msg = f"{header}\n{text_content}" if header else text_content
        mention = None
        style_list = []

        if header:
            style_list.extend([
                MessageStyle(offset=0, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="font", size=18, auto_format=False)
            ])

        styles = MultiMsgStyle(style_list) if style_list else None
    else:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and hasattr(user_info, 'changed_profiles') else {}
        name = author_info.get('zaloName', 'Thành viên')

        tag_text = f"@{name}"
        full_msg = f"{tag_text}\n{header}\n{text_content}" if header else f"{tag_text}\n{text_content}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))

        style_list = []
        offset_header = len(tag_text) + 1

        if header:
            style_list.extend([
                MessageStyle(offset=offset_header, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="font", size=18, auto_format=False)
            ])

        styles = MultiMsgStyle(style_list) if style_list else None

    try:
        client.replyMessage(
            Message(text=full_msg, style=styles, mention=mention),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=ttl
        )
    except Exception:
        try:
            client.sendMessage(
                Message(text=full_msg, style=styles, mention=mention),
                thread_id, thread_type
            )
        except Exception:
            pass

def clean_cache(file_paths):
    """Xóa file tạm sau 60s"""
    try:
        time.sleep(60)
        for path in file_paths:
            if path and os.path.exists(path):
                os.remove(path)
    except Exception:
        pass

def upload_to_catbox(file_path):
    """Upload file lên Catbox.moe"""
    try:
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload", "userhash": ""}
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            response = requests.post(url, data=data, files=files, timeout=600)
            if response.status_code == 200:
                return response.text.strip()
            return None
    except Exception as e:
        print(f"⚠️ Lỗi upload Catbox: {e}")
        return None

def send_video_custom(client, thread_id, thread_type, video_url, thumb_url, duration, width, height, file_size, message_text=""):
    try:
        if not thumb_url or "http" not in thumb_url:
            thumb_url = FALLBACK_THUMB

        width = int(width) if width and width > 0 else 1280
        height = int(height) if height and height > 0 else 720
        duration = int(duration) if duration and duration > 0 else 60000
        file_size = int(file_size) if file_size else 0

        msg_info = {
            "videoUrl": str(video_url),
            "thumbUrl": str(thumb_url),
            "duration": duration,
            "width": width,
            "height": height,
            "fileSize": file_size,
            "properties": {
                "color": -1,
                "size": -1,
                "type": 1003,
                "subType": 0,
                "ext": "{\"sSrcType\":-1,\"sSrcStr\":\"\",\"msg_warning_type\":0}"
            },
            "title": message_text,
            "type": 5
        }

        params = {
            "zpw_ver": 647,
            "zpw_type": 30,
            "nretry": 0
        }

        body = {
            "params": {
                "clientId": str(int(time.time() * 1000)),
                "ttl": 0,
                "zsource": 704,
                "msgType": 5,
                "msgInfo": json.dumps(msg_info)
            }
        }

        if thread_type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/forward"
            body["params"]["toId"] = str(thread_id)
            body["params"]["imei"] = client._imei
        else:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/forward"
            body["params"]["visibility"] = 0
            body["params"]["grid"] = str(thread_id)

        body["params"] = client._encode(body["params"])
        response = client._post(url, params=params, data=body)
        return response
    except Exception as e:
        print(f"Lỗi send_video_custom: {e}")
        return None

def processing_task(url, client, message_object, thread_id, thread_type, author_id):
    print(f"🔄 [AutoDL] Đang xử lý URL: {url}")

    timestamp = int(time.time())
    video_path = os.path.join(CACHE_DIR, f"vid_{timestamp}.mp4")
    thumb_path = os.path.join(CACHE_DIR, f"thumb_{timestamp}.jpg")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': video_path,
        'writethumbnail': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if not os.path.exists(video_path):
                video_path = ydl.prepare_filename(info)

            # Xử lý thumbnail
            potential_thumb = video_path.rsplit('.', 1)[0] + ".jpg"
            if not os.path.exists(potential_thumb):
                potential_thumb = video_path.rsplit('.', 1)[0] + ".webp"

            if os.path.exists(potential_thumb):
                try:
                    img = Image.open(potential_thumb).convert("RGB")
                    img.save(thumb_path, "JPEG")
                except Exception:
                    pass
            else:
                thumb_url_src = info.get('thumbnail')
                if thumb_url_src:
                    try:
                        with open(thumb_path, 'wb') as f:
                            f.write(requests.get(thumb_url_src).content)
                    except Exception:
                        pass

            if not os.path.exists(video_path):
                reply_msg(client, message_object, thread_id, thread_type, author_id,
                          "❌ Lỗi: File không tồn tại.", ttl=15000)
                return

            file_size_bytes = os.path.getsize(video_path)
            file_size_mb = file_size_bytes / (1024 * 1024)

            if file_size_mb > 199:
                reply_msg(client, message_object, thread_id, thread_type, author_id,
                          f"❌ Video quá nặng ({file_size_mb:.2f} MB)!", ttl=15000)
                clean_cache([video_path, thumb_path])
                return

            # --- UPLOAD ---
            client.sendReaction(message_object, "☁️", thread_id, thread_type)

            uploaded_video_url = upload_to_catbox(video_path)

            uploaded_thumb_url = ""
            if os.path.exists(thumb_path):
                uploaded_thumb_url = upload_to_catbox(thumb_path)

            if not uploaded_thumb_url:
                uploaded_thumb_url = info.get('thumbnail') or FALLBACK_THUMB

            if uploaded_video_url:
                print(f"🚀 Video URL: {uploaded_video_url}")

                # --- CAPTION ---
                title = info.get('title', '')
                uploader = info.get('uploader', 'Unknown')
                description = info.get('description', '')

                caption_parts = []
                if title: caption_parts.append(f"🎥 {title}")
                if uploader: caption_parts.append(f"👤 {uploader}")
                if description:
                    if len(description) > 1000:
                        description = description[:1000] + "..."
                    caption_parts.append(f"\n📝 {description}")

                full_caption = "\n".join(caption_parts)

                video_duration = int(info.get('duration', 0) * 1000)
                video_width = info.get('width', 1280)
                video_height = info.get('height', 720)

                send_video_custom(
                    client=client,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    video_url=uploaded_video_url,
                    thumb_url=uploaded_thumb_url,
                    duration=video_duration,
                    width=video_width,
                    height=video_height,
                    file_size=file_size_bytes,
                    message_text=full_caption
                )

                client.sendReaction(message_object, "✅", thread_id, thread_type)
            else:
                reply_msg(client, message_object, thread_id, thread_type, author_id,
                          "❌ Lỗi upload server Catbox.", ttl=15000)

            threading.Thread(target=clean_cache, args=([video_path, thumb_path, potential_thumb],)).start()

    except Exception as e:
        print(f"❌ [AutoDL] Lỗi: {e}")
        err_msg = str(e)
        if "ffmpeg" in err_msg.lower():
            err_msg = "Lỗi hệ thống: Server thiếu FFmpeg, đã thử chế độ tương thích nhưng thất bại."

        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  f"❌ Lỗi: {err_msg[:100]}...", ttl=15000)
        if 'video_path' in locals():
            clean_cache([video_path])

def extract_url_from_message(message, message_object):
    if hasattr(message_object, 'href') and message_object.href:
        if "http" in message_object.href:
            return message_object.href
    urls = re.findall(r'(https?://[^\s]+)', message)
    if urls:
        return urls[0]
    if hasattr(message_object, 'title') and message_object.title:
        urls = re.findall(r'(https?://[^\s]+)', message_object.title)
        if urls:
            return urls[0]
    if message_object.quote:
        if hasattr(message_object.quote, 'content') and "http" in message_object.quote.content:
            urls = re.findall(r'(https?://[^\s]+)', message_object.quote.content)
            if urls:
                return urls[0]
        if hasattr(message_object.quote, 'href') and message_object.quote.href:
            return message_object.quote.href
    return ""

def handle_autodl(message, message_object, thread_id, thread_type, author_id, client):
    url = extract_url_from_message(message, message_object)
    if not url:
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  f"⚠️ Không tìm thấy link!\nHDSD: {PREFIX}dl <link>", ttl=15000)
        return

    client.sendReaction(message_object, "⬇️", thread_id, thread_type)

    task_thread = threading.Thread(
        target=processing_task,
        args=(url, client, message_object, thread_id, thread_type, author_id)
    )
    task_thread.daemon = True
    task_thread.start()

def PTA():
    return {
        'autodl': handle_autodl,
        'dl': handle_autodl,
        'tik': handle_autodl
    }
