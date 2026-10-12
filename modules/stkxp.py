import requests
import subprocess
import json
import urllib.parse
import os
from io import BytesIO
from PIL import Image, ImageDraw
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from zlapi._threads import ThreadType
import time
import random

des = {
    'version': "2.1.0",
    'credits': "Hoàng Khánh Primen",
    'description': "Tạo sticker xóa nền từ ảnh.",
    'power': "Thành viên"
}

from removebg import RemoveBg

class BackgroundRemover:
    def __init__(self, api_key):
        self.rmbg = RemoveBg(api_key, "error.log")

    def remove_background_from_url(self, img_url):
        try:
            output_file_name = 'no-bg.png'
            self.rmbg.remove_background_from_img_url(img_url, new_file_name=output_file_name)
            return output_file_name
        except Exception as e:
            print(f"Loi khi xoa nen tu URL: {e}")
            return None

def check_ffmpeg_webp_support():
    try:
        result = subprocess.run(["ffmpeg", "-codecs"], capture_output=True, text=True, check=True)
        return "libwebp_anim" in result.stdout or "libwebp" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_file_type(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get("Content-Type", "").lower()
        if "image" in content_type:
            return "image"
        elif "video" in content_type:
            return "video"
        return "unknown"
    except requests.RequestException:
        return "unknown"

def upload_to_catbox(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {'fileToUpload': ('sticker.webp', f, 'image/webp')}
            response = requests.post("https://catbox.moe/user/api.php", files=files, data={"reqtype": "fileupload"})
        return response.text.strip() if response.status_code == 200 else None
    except Exception as e:
        print(f"Lỗi khi upload lên Catbox: {e}")
        return None

def upload_to_uguu(file_path):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with open(file_path, 'rb') as file:
            files = {'files[]': file}
            response = requests.post("https://uguu.se/upload", files=files, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result["files"][0]["url"]
    except Exception as e:
        print(f"Loi khi upload file len Uguu: {e}")
    return None

def is_valid_image_url(url):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(url.lower().endswith(ext) for ext in valid_extensions)

def convert_media_and_upload(media_url, file_type, unique_id, client):
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'cache', 'temp')
    
    os.makedirs(temp_dir, exist_ok=True)

    temp_input = os.path.join(temp_dir, f"pro_input_{unique_id}")
    temp_webp = os.path.join(temp_dir, f"tranquan_{unique_id}.webp")
    
    files_to_cleanup = [temp_input, temp_webp]

    try:
        response = requests.get(media_url, stream=True, timeout=15)
        response.raise_for_status()
        
        with open(temp_input, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        if file_type == "image":
            with Image.open(temp_input).convert("RGBA") as img:
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                
                width, height = img.size
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, width, height), radius=50, fill=255)
                img.putalpha(mask)
                img.save(temp_webp, format="WEBP", quality=80, lossless=False)
        else: # video
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_input,
                "-vf", "scale=512:-2",
                "-c:v", "libwebp_anim",
                "-loop", "0",
                "-r", "15",
                "-an",
                "-lossless", "0",
                "-q:v", "80",
                "-loglevel", "error",
                temp_webp
            ], check=True, capture_output=True, text=True)

        return upload_to_catbox(temp_webp)

    except subprocess.CalledProcessError as e:
        print(f"Lỗi FFmpeg: {e.stderr}")
        raise Exception(f"Lỗi FFmpeg: {e.stderr}")
    except Exception as e:
        print(f"Lỗi khi chuyển đổi media: {e}")
        raise e
    finally:
        for f in files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)

def handle_stkxp_command(message, message_object, thread_id, thread_type, author_id, client):
    if not check_ffmpeg_webp_support():
        client.replyMessage(
            Message(text="➜ Lỗi: FFmpeg không hỗ trợ codec libwebp/libwebp_anim."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    if not message_object.quote:
        client.replyMessage(
            Message(text="➜ Hãy reply vào ảnh cần tạo sticker xóa nền."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    attach = message_object.quote.attach
    if not attach:
        client.replyMessage(
            Message(text="➜ Không có ảnh nào được reply."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    try:
        attach_data = json.loads(attach)
    except json.JSONDecodeError:
        client.replyMessage(
            Message(text="➜ Dữ liệu ảnh không hợp lệ."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    image_url = attach_data.get('hdUrl') or attach_data.get('href')
    if not image_url:
        client.replyMessage(
            Message(text="➜ Không tìm thấy URL ảnh."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    # Xử lý URL
    image_url = image_url.replace('/jxl', '/jpg').replace('.jxl', '.jpg')
    image_url = urllib.parse.unquote(image_url)

    if not is_valid_image_url(image_url):
        client.replyMessage(
            Message(text="➜ URL không phải là ảnh hợp lệ."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    # Gửi thông báo xử lý
    processing_msg = Message(text="➜ ⏳ Đang xóa nền và tạo sticker, vui lòng chờ...")
    client.replyMessage(processing_msg, message_object, thread_id, thread_type, ttl=120000)

    try:
        # Xóa nền
        remover = BackgroundRemover("DjYwh19heAXUpcGTPCkkq1Z5")
        output_file_name = remover.remove_background_from_url(image_url)
        
        if not output_file_name:
            raise Exception("Không thể xóa nền từ ảnh.")
        
        # Upload lên Uguu
        uploaded_url = upload_to_uguu(output_file_name)
        
        if not uploaded_url:
            raise Exception("Không thể tải ảnh lên.")
        
        # Gửi sticker
        client.sendCustomSticker(
            staticImgUrl=uploaded_url,
            animationImgUrl=None,
            thread_id=thread_id,
            thread_type=thread_type
        )
        
        # Xóa file tạm
        if os.path.exists(output_file_name):
            os.remove(output_file_name)
            
    except Exception as e:
        client.replyMessage(
            Message(text=f"➜ Lỗi khi tạo sticker xóa nền: {str(e)}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'stkxp': handle_stkxp_command
    }