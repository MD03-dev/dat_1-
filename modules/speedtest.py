from zlapi.models import *
import time
import datetime
import os
import threading
import random
import textwrap

# Cấu hình đường dẫn font
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CJK_FONT_PATH = "modules/cache/font/Noto Sans CJK Regular.otf"

# Kỹ thuật Safe Load: Kiểm tra thư viện ngay khi khởi động
HAS_LIBS = True
try:
    import requests
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    import speedtest
    import emoji as emoji_mod
except ImportError as e:
    HAS_LIBS = False
    print(f"\n[CẢNH BÁO] Lệnh speedtest.py không thể vẽ ảnh do thiếu thư viện: {e}")
    print(">> Vui lòng chạy lệnh: pip install Pillow speedtest-cli requests emoji\n")

des = {
    'version': "2.3.4",
    'credits': "Van Chien Dev",
    'description': "Kiểm tra tốc độ mạng và ping bằng hình ảnh (Hiển thị avatar bot, text lớn, màu sắc tuỳ chỉnh)",
    'power': "Thành viên"
}

# ================= CÁC HÀM ĐÁNH GIÁ TỐC ĐỘ ================= #
def evaluate_speed(speed):
    if speed < 1.25: return "Rất chậm 🐌"
    if speed < 3.75: return "Chậm 😢"
    if speed < 6.25: return "Trung bình 🙂"
    if speed < 12.5: return "Khá tốt 👍"
    if speed < 25: return "Tốt 🚀"
    if speed < 62.5: return "Rất tốt 🏃‍♂️"
    if speed < 125: return "Cực mạnh ⚡"
    return "Siêu tốc 🌪️"

# ================= CÁC HÀM XỬ LÝ FONT ================= #
def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: return ImageFont.load_default()

def get_cjk_font(size):
    try: return ImageFont.truetype(CJK_FONT_PATH, size)
    except: return get_font(size)

def get_font_for_char(char, font, emoji_font, cjk_font):
    if emoji_mod.emoji_count(char):
        return emoji_font
    
    o = ord(char)
    if (0x4E00 <= o <= 0x9FFF) or \
       (0x3400 <= o <= 0x4DBF) or \
       (0x20000 <= o <= 0x2A6DF) or \
       (0x3040 <= o <= 0x309F) or \
       (0x30A0 <= o <= 0x30FF) or \
       (0xFF00 <= o <= 0xFFEF) or \
       o == 0x76ca: 
        return cjk_font
    return font

def draw_mixed_text(draw, x, y, text, font, emoji_font, cjk_font, fill):
    cur_x = x
    for char in text:
        f2use = get_font_for_char(char, font, emoji_font, cjk_font)
        draw.text((cur_x, y), char, font=f2use, fill=fill)
        try:
            cur_x += f2use.getlength(char)
        except AttributeError:
            cur_x += f2use.getsize(char)[0]

def get_mixed_text_width(text, font, emoji_font, cjk_font):
    width = 0
    for char in text:
        f2use = get_font_for_char(char, font, emoji_font, cjk_font)
        try:
            width += f2use.getlength(char)
        except AttributeError:
            width += f2use.getsize(char)[0]
    return width

# ================= CÁC HÀM VẼ GRADIENT ================= #
def create_gradient_bg(width, height, color1, color2):
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        ratio = y / float(height)
        mask_data.extend([int(255 * ratio)] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def create_rainbow_gradient(width, height):
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
    random.shuffle(colors) 
    
    section_height = height / float(len(colors) - 1)
    for y in range(height):
        idx = int(y / section_height)
        if idx >= len(colors) - 1:
            idx = len(colors) - 2
        
        c1 = colors[idx]
        c2 = colors[idx+1]
        ratio = (y - (idx * section_height)) / section_height
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img

# ================= HÀM TẠO ẢNH CHÍNH ================= #
def create_speedtest_image(client=None):
    st = speedtest.Speedtest(secure=True)
    st.get_best_server()
    download = st.download() / 1_000_000
    upload = st.upload() / 1_000_000
    ping = st.results.ping
    sponsor_name = st.results.server.get('sponsor', 'Unknown ISP')
    server_location = f"{st.results.server.get('name', 'Unknown')} ({st.results.server.get('country', 'Unknown')})"
    time_str = datetime.datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")

    # Mở rộng canvas để chứa font chữ to hơn
    width, height = 1050, 500
    
    # 1. Vẽ nền Gradient 
    img = create_gradient_bg(width, height, (59, 130, 246), (17, 24, 39))
    draw = ImageDraw.Draw(img)

    # 2. Lấy Avatar của Bot bằng fetchAccountInfo
    avatar_url = None
    fallback_url = "https://i.imgur.com/RoC7gZg.png" # Đổi link ảnh dự phòng tại đây nếu muốn
    
    try:
        if client:
            account_info = client.fetchAccountInfo()
            # Xử lý an toàn giống event.py (hỗ trợ cả dict và object)
            if isinstance(account_info, dict):
                avatar_url = account_info.get('avatar') or account_info.get('avt')
            elif account_info and hasattr(account_info, 'avatar'):
                avatar_url = account_info.avatar
    except Exception as e:
        print(f"Lỗi lấy info bot: {e}")

    # Xử lý tải avatar với headers và fallback
    avatar_loaded = False
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        "Referer": "https://imgur.com/"
    }

    # Thử tải avatar thật của bot
    if avatar_url:
        try:
            r = requests.get(avatar_url, headers=headers, timeout=5)
            if r.status_code == 200:
                avatar = Image.open(BytesIO(r.content)).convert("RGBA")
                avatar_loaded = True
        except Exception as e:
            print(f"Lỗi tải avatar bot: {e}")

    # Nếu tải thất bại hoặc không có avatar_url -> dùng Fallback
    if not avatar_loaded:
        try:
            r_fallback = requests.get(fallback_url, headers=headers, timeout=5)
            if r_fallback.status_code == 200:
                avatar = Image.open(BytesIO(r_fallback.content)).convert("RGBA")
                avatar_loaded = True
            else:
                print(f"Lỗi tải fallback avatar (Status Code: {r_fallback.status_code})")
        except Exception as e:
            print(f"Lỗi tải fallback avatar: {e}")

    # Backup cuối cùng nếu rớt luôn cả kết nối mạng tới ảnh fallback
    if not avatar_loaded:
        avatar = Image.new("RGBA", (180, 180), (100, 100, 100, 255))

    size = (180, 180)
    avatar = avatar.resize(size, Image.LANCZOS)
    mask = Image.new('L', size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0) + size, fill=255)
    avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
    avatar.putalpha(mask)

    # === DỊCH AVATAR XUỐNG THẤP HƠN ===
    # Trước: avatar_y = 120 → Sau: avatar_y = 155 (xuống thêm 35px)
    avatar_x, avatar_y = 90, 155

    # Vẽ viền Avatar Gradient Rainbow
    border_width = 10
    border_size = (size[0] + border_width * 2, size[1] + border_width * 2)
    rainbow_bg = create_rainbow_gradient(border_size[0], border_size[1])
    
    border_mask_circle = Image.new('L', border_size, 0)
    border_draw_circle = ImageDraw.Draw(border_mask_circle)
    border_draw_circle.ellipse((0, 0) + border_size, fill=255)
    rainbow_bg.putalpha(border_mask_circle)
    
    border_x = avatar_x - border_width
    border_y = avatar_y - border_width
    img.paste(rainbow_bg, (border_x, border_y), rainbow_bg)
    img.paste(avatar, (avatar_x, avatar_y), avatar)

    # Khởi tạo Font chữ to hơn
    font_title = get_font(52)  
    emoji_title = get_emoji_font(52)
    cjk_title = get_cjk_font(52)

    font_text = get_font(32)  
    emoji_text = get_emoji_font(32)
    cjk_text = get_cjk_font(32)
    
    font_sponsor = get_font(26)
    emoji_sponsor = get_emoji_font(26)
    cjk_sponsor = get_cjk_font(26)

    # Vẽ Title màu Cyan sáng
    title_text = "Kết Quả SpeedTest"
    title_width = get_mixed_text_width(title_text, font_title, emoji_title, cjk_title)
    title_x = (width - title_width) // 2
    title_y = 30
    draw_mixed_text(draw, title_x, title_y, title_text, font_title, emoji_title, cjk_title, "#A5F3FC")

    # === VẼ CHỮ TÊN NHÀ MẠNG BÊN DƯỚI AVATAR (đã dịch xuống theo avatar) ===
    sponsor_lines = textwrap.wrap(sponsor_name, width=18)
    sponsor_y = avatar_y + size[1] + 20  # Tự động tính theo vị trí avatar mới
    for s_line in sponsor_lines:
        s_width = get_mixed_text_width(s_line, font_sponsor, emoji_sponsor, cjk_sponsor)
        s_x = avatar_x + (size[0] // 2) - (s_width // 2)
        draw_mixed_text(draw, s_x, sponsor_y, s_line, font_sponsor, emoji_sponsor, cjk_sponsor, "#FFFFFF")
        sponsor_y += 35

    # Đánh giá tốc độ
    dl_status = evaluate_speed(download)
    ul_status = evaluate_speed(upload)

    # Danh sách các dòng kèm màu sắc riêng
    lines = [
        (f"📥 Download: {download:.2f} MB/s ({dl_status})", "#D1FAE5"), # Xanh nhạt
        (f"📤 Upload: {upload:.2f} MB/s ({ul_status})", "#FEF08A"),   # Vàng nhạt
        (f"🏓 Ping: {int(ping)}ms", "#FEF08A"),                        # Vàng nhạt
        (f"🌍 Server: {server_location}", "#BAE6FD"),                  # Xanh dương nhạt
        (f"🖥️ VPN: Mạng Không thuộc VPN", "#86EFAC"),                  # Xanh lá
        (f"🕰️ Thời gian: {time_str}", "#A7F3D0")                       # Xanh lá nhạt
    ]

    text_x = 360  
    current_y = 120  
    line_spacing = 52  

    for line_text, color in lines:
        draw_mixed_text(draw, text_x, current_y, line_text, font_text, emoji_text, cjk_text, color)
        current_y += line_spacing

    output_path = "speedtest_result.jpg"
    img.save(output_path, quality=100)
    
    return output_path, width, height

# ================= XỬ LÝ LỆNH BOT ================= #
def process_speedtest(message, message_object, thread_id, thread_type, client, wait_msg):
    try:
        # Truyền client vào để lấy ảnh avatar bot
        image_path, img_width, img_height = create_speedtest_image(client)
        
        client.sendLocalImage(
            imagePath=image_path,
            message=Message(text="Kết quả kiểm tra tốc độ mạng của bot!"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=img_width,
            height=img_height,
            ttl=600000
        )
        
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        client.replyMessage(Message(f"Lỗi khi đo tốc độ mạng: {str(e)}"), message_object, thread_id, thread_type)
    finally:
        try:
            if wait_msg:
                client.undo(wait_msg) 
        except:
            pass

def handel_ping_command(message, message_object, thread_id, thread_type, author_id, client):
    if not HAS_LIBS:
        client.replyMessage(
            Message("⚠️ Bot chưa cài đủ thư viện để vẽ ảnh. Dev vui lòng vào Terminal/CMD chạy lệnh: pip install Pillow speedtest-cli requests emoji"),
            message_object, thread_id, thread_type
        )
        return

    wait_msg = client.replyMessage(
        Message("Bắt đầu kiểm tra tốc độ mạng, vui lòng chờ..."), 
        message_object, 
        thread_id, 
        thread_type
    )

    threading.Thread(
        target=process_speedtest, 
        args=(message, message_object, thread_id, thread_type, client, wait_msg)
    ).start()

def PTA():
    return {
        'spt': handel_ping_command,
        'speedtest': handel_ping_command
    }