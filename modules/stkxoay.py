import requests
import subprocess
import json
import urllib.parse
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from zlapi._threads import ThreadType
import time
import random
import math

des = {
    'version': "2.0.1",
    'credits': "Hoàng Khánh Primen Cte",
    'description': "Tạo sticker xoay",
    'power': "Thành viên"
}

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

def create_rotating_sticker(image_path, output_path, direction="phải", fps=24, duration=3):
    """
    Tạo sticker xoay vòng tròn
    direction: "trái" hoặc "phải" - hướng xoay
    fps: số khung hình mỗi giây (mặc định 24fps)
    duration: thời lượng animation (giây)
    """
    try:
        # Mở ảnh gốc
        with Image.open(image_path).convert("RGBA") as img:
            # Resize ảnh về kích thước chuẩn
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # Tạo hình tròn cho ảnh
            width, height = img.size
            mask = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, width, height), fill=255)
            img.putalpha(mask)
            
            # Tính toán số frame
            num_frames = fps * duration
            frames = []
            
            # Xác định chiều xoay
            direction_multiplier = 1 if direction.lower() == "phải" else -1
            
            # Tạo các frame xoay
            for i in range(num_frames):
                # Tính góc xoay (0 đến 360 độ)
                # Phải: 0 → 360, Trái: 360 → 0
                angle = (i / num_frames) * 360 * direction_multiplier
                
                # Xoay ảnh
                rotated_img = img.rotate(angle, expand=False, resample=Image.BICUBIC)
                
                # Đảm bảo kích thước không đổi
                if rotated_img.size != (512, 512):
                    rotated_img = rotated_img.resize((512, 512), Image.Resampling.LANCZOS)
                
                frames.append(rotated_img)
            
            # Lưu thành file WebP animated
            if len(frames) > 0:
                frames[0].save(
                    output_path,
                    format="WEBP",
                    save_all=True,
                    append_images=frames[1:],
                    duration=int(1000 / fps),  # milliseconds per frame
                    loop=0,  # 0 = loop forever
                    quality=85,
                    lossless=False
                )
                return True
            else:
                return False
                
    except Exception as e:
        print(f"Lỗi khi tạo sticker xoay: {e}")
        return False

def parse_direction_from_message(message_text):
    """Phân tích hướng xoay từ tin nhắn"""
    message_lower = message_text.lower()
    
    if "trái" in message_lower:
        return "trái"
    elif "phải" in message_lower:
        return "phải"
    else:
        # Mặc định xoay phải
        return "phải"

def convert_media_and_upload(media_url, unique_id, direction, client):
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'cache', 'temp')
    
    os.makedirs(temp_dir, exist_ok=True)

    temp_input = os.path.join(temp_dir, f"xoay_input_{unique_id}")
    temp_webp = os.path.join(temp_dir, f"stickerxoay_{unique_id}.webp")
    
    files_to_cleanup = [temp_input, temp_webp]

    try:
        # Tải ảnh từ URL
        response = requests.get(media_url, stream=True, timeout=15)
        response.raise_for_status()
        
        with open(temp_input, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        # Tạo sticker xoay
        success = create_rotating_sticker(temp_input, temp_webp, direction=direction, fps=24, duration=3)
        
        if not success:
            raise Exception("Không thể tạo sticker xoay.")
        
        # Upload lên Catbox
        return upload_to_catbox(temp_webp)

    except Exception as e:
        print(f"Lỗi khi chuyển đổi media: {e}")
        raise e
    finally:
        for f in files_to_cleanup:
            if os.path.exists(f):
                os.remove(f)

def handle_stkxoay_command(message, message_object, thread_id, thread_type, author_id, client):
    if not check_ffmpeg_webp_support():
        client.replyMessage(
            Message(text="➜ Lỗi: FFmpeg không hỗ trợ codec libwebp/libwebp_anim."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    if not message_object.quote or not message_object.quote.attach:
        client.replyMessage(
            Message(text="➜ Vui lòng reply vào ảnh để tạo sticker xoay vòng tròn.\n"
                       "🎯 Cú pháp:\n"
                       "• stkxoay trái - Xoay từ phải Hoàng Khánh Primen trái\n"
                       "• stkxoay phải - Xoay từ trái Hoàng Khánh Primen phải\n"
                       "• stkxoay - Mặc định xoay phải\n"
                       "📊 Thông số: 24fps, 3 giây, hình tròn"),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    try:
        attach_data = json.loads(message_object.quote.attach)
    except (json.JSONDecodeError, TypeError):
        client.replyMessage(Message(text="➜ Dữ liệu đính kèm không hợp lệ."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = attach_data.get('hdUrl') or attach_data.get('href')
    if not media_url:
        client.replyMessage(Message(text="➜ Không tìm thấy URL của ảnh."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))

    if "jxl" in media_url:
        media_url = media_url.replace("jxl", "jpg")

    file_type = get_file_type(media_url)
    if file_type != "image":
        client.replyMessage(Message(text="➜ Chỉ hỗ trợ file ảnh (JPG, PNG, GIF)."), message_object, thread_id, thread_type, ttl=60000)
        return

    # Phân tích hướng xoay từ tin nhắn
    direction = parse_direction_from_message(message)
    
    processing_msg = Message(text=f"➜ ⏳ Đang tạo sticker xoay {direction} vòng tròn...\n"
                                f"↳ 24fps • 3 giây • Hình tròn")
    client.replyMessage(processing_msg, message_object, thread_id, thread_type, ttl=120000)

    try:
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        webp_url = convert_media_and_upload(media_url, unique_id, direction, client)
        
        if not webp_url:
            raise Exception("Không thể tạo hoặc tải lên sticker xoay.")

        client.sendCustomSticker(
            animationImgUrl=webp_url,
            staticImgUrl=webp_url,
            thread_id=thread_id,
            thread_type=thread_type,
            width=512,
            height=512
        )
        
        # Xác định icon hướng
        direction_icon = "↪️" if direction == "phải" else "↩️"
        
        client.sendMessage(
            Message(text=f"➜ ✅ Đã tạo sticker xoay thành công!\n"
                       f"{direction_icon} Hướng xoay: {direction.capitalize()}\n"
                       f"🎞️ FPS: 24\n"
                       f"⏱️ Thời lượng: 3 giây\n"
                       f"🔁 Loop: Vô hạn"),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=30000
        )
        
    except Exception as e:
        client.replyMessage(
            Message(text=f"➜ Lỗi khi tạo sticker xoay: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'stkxoay': handle_stkxoay_command,
        'stickerxoay': handle_stkxoay_command  # Thêm alias
    }