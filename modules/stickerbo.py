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
    'version': "2.0.2",
    'credits': "Hoàng Khánh Primen",
    'description': "Tạo sticker từ ảnh, GIF, video với góc bo tùy chỉnh (0-50%).",
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

def parse_radius_percentage(message_text):
    """Phân tích phần trăm bo góc từ tin nhắn"""
    # Tìm số phần trăm trong tin nhắn
    import re
    
    # Tìm các số trong tin nhắn
    numbers = re.findall(r'\d+', message_text)
    
    if not numbers:
        return 20  # Mặc định 20% nếu không có số
    
    # Lấy số đầu tiên và giới hạn trong khoảng 0-50
    radius_percent = int(numbers[0])
    radius_percent = max(0, min(radius_percent, 50))  # Giới hạn 0-50%
    
    return radius_percent

def convert_media_and_upload(media_url, file_type, unique_id, radius_percent, client):
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'cache', 'temp')
    
    os.makedirs(temp_dir, exist_ok=True)

    temp_input = os.path.join(temp_dir, f"pro_input_{unique_id}")
    temp_webp = os.path.join(temp_dir, f"stickerbo_{unique_id}.webp")
    
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
                
                # Tính toán radius dựa trên phần trăm
                # Lấy kích thước nhỏ hơn để tính radius
                min_dimension = min(width, height)
                radius_pixels = int((radius_percent / 100) * min_dimension)
                
                # Đảm bảo radius không quá lớn
                radius_pixels = min(radius_pixels, min_dimension // 2)
                
                # Tạo mask với góc bo
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                
                if radius_pixels > 0:
                    # Vẽ hình chữ nhật bo góc
                    draw.rounded_rectangle(
                        (0, 0, width, height), 
                        radius=radius_pixels, 
                        fill=255
                    )
                else:
                    # Nếu radius = 0, vẽ hình chữ nhật không bo góc
                    draw.rectangle((0, 0, width, height), fill=255)
                
                img.putalpha(mask)
                img.save(temp_webp, format="WEBP", quality=80, lossless=False)
        else:  # video
            # Video không hỗ trợ bo góc trong ffmpeg đơn giản
            # Có thể xử lý phức tạp hơn nếu cần
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

def handle_stkbo_command(message, message_object, thread_id, thread_type, author_id, client):
    if not check_ffmpeg_webp_support():
        client.replyMessage(
            Message(text="➜ Lỗi: FFmpeg không hỗ trợ codec libwebp/libwebp_anim."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    if not message_object.quote or not message_object.quote.attach:
        client.replyMessage(
            Message(text="➜ Vui lòng reply vào ảnh, GIF hoặc video để tạo sticker.\n"
                       "Cú pháp: stkbo [phần trăm] hoặc stk bo [phần trăm]\n"
                       "Ví dụ: stkbo 30 (bo góc 30%)"),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    # Phân tích phần trăm bo góc từ tin nhắn
    radius_percent = parse_radius_percentage(message)
    
    try:
        attach_data = json.loads(message_object.quote.attach)
    except (json.JSONDecodeError, TypeError):
        client.replyMessage(Message(text="➜ Dữ liệu đính kèm không hợp lệ."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = attach_data.get('hdUrl') or attach_data.get('href')
    if not media_url:
        client.replyMessage(Message(text="➜ Không tìm thấy URL của media."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))

    if "jxl" in media_url:
        media_url = media_url.replace("jxl", "jpg")

    file_type = get_file_type(media_url)
    if file_type not in ["image", "video"]:
        client.replyMessage(Message(text="➜ Loại file không được hỗ trợ."), message_object, thread_id, thread_type, ttl=60000)
        return

    processing_msg = Message(text=f"➜ ⏳ Đang xử lý sticker (bo {radius_percent}%), vui lòng chờ...")
    client.replyMessage(processing_msg, message_object, thread_id, thread_type, ttl=120000)

    try:
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        webp_url = convert_media_and_upload(media_url, file_type, unique_id, radius_percent, client)
        
        if not webp_url:
            raise Exception("Không thể tạo hoặc tải lên sticker.")

        client.sendCustomSticker(
            animationImgUrl=webp_url,
            staticImgUrl=webp_url,
            thread_id=thread_id,
            thread_type=thread_type,
            width=512,
            height=512
        )
        
        # Thông báo thành công với thông tin phần trăm
        if radius_percent == 0:
            success_msg = "➜ ✅ Đã tạo sticker thành công (không bo góc)!"
        else:
            success_msg = f"➜ ✅ Đã tạo sticker thành công (bo góc {radius_percent}%)!"
        
        client.sendMessage(
            Message(text=success_msg),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=30000
        )
        
    except Exception as e:
        client.replyMessage(
            Message(text=f"➜ Lỗi khi tạo sticker: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'stkbo': handle_stkbo_command,
        'stk bo': handle_stkbo_command  # Hỗ trợ cả 2 cách gõ
    }