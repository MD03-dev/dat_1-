import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import textwrap
import random
import concurrent.futures
import time
import base64
from zlapi.models import Message

# Import Prefix
from config import PREFIX

des = {
    'version': "1.2.0",
    'credits': "Quocbaoo",
    'description': "Chế ảnh Fake News (Fix lỗi đè chữ)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def fetch_image(url):
    if not url: return None
    try:
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGBA")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

def draw_centered_text(draw, text, font, center_x, y, color):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
    except:
        w = font.getlength(text)
    draw.text((center_x - w / 2, y), text, font=font, fill=color)

# ================= LOGIC VẼ BẢN TIN =================

def create_breaking_news(avatar_url, headline):
    W, H = 1280, 720
    
    # 1. Xử lý ảnh nền
    bg = fetch_image(avatar_url)
    if not bg: 
        bg = Image.new("RGB", (W, H), (50, 50, 50))
    else:
        bg = bg.convert("RGB")
        img_ratio = bg.width / bg.height
        target_ratio = W / H
        
        if img_ratio > target_ratio:
            new_height = H
            new_width = int(img_ratio * H)
            bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - W) // 2
            bg = bg.crop((left, 0, left + W, H))
        else:
            new_width = W
            new_height = int(W / img_ratio)
            bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - H) // 2
            bg = bg.crop((0, top, W, top + H))

    draw = ImageDraw.Draw(bg)

    # 2. Vẽ khung giao diện (FIX LỖI LAYOUT TẠI ĐÂY)
    
    # Tăng chiều cao thanh đỏ lên 190px (Cũ là 150px) để chứa chữ thoải mái
    BAR_H = 190 
    draw.rectangle((0, H - BAR_H, W, H), fill=(180, 0, 0)) # Đỏ đậm
    
    # Thanh vàng Ticker giữ nguyên 45px
    TICKER_H = 45
    draw.rectangle((0, H - TICKER_H, W, H), fill=(255, 200, 0)) # Vàng

    # 3. Logo LIVE & Thời gian (Header)
    draw.rectangle((40, 40, 160, 90), fill=(200, 0, 0))
    draw_centered_text(draw, "LIVE ●", get_font(30), 100, 50, (255, 255, 255))
    
    current_time = time.strftime("%H:%M")
    draw.rectangle((W - 150, 40, W - 40, 90), fill=(0, 0, 0, 150))
    draw_centered_text(draw, current_time, get_font(30), W - 95, 50, (255, 255, 255))

    # 4. Nhãn "BREAKING NEWS"
    # Vẽ đè lên mép trên của thanh đỏ
    LABEL_W, LABEL_H = 350, 50
    label_y = H - BAR_H - LABEL_H + 10 # Chỉnh vị trí nhãn
    draw.rectangle((40, label_y, 40 + LABEL_W, label_y + LABEL_H), fill=(220, 0, 0))
    draw_centered_text(draw, "BREAKING NEWS", get_font(30), 40 + LABEL_W/2, label_y + 8, (255, 255, 255))

    # 5. Nội dung chính (Headline) - XỬ LÝ KHÔNG BỊ ĐÈ
    
    # Khu vực an toàn cho chữ:
    # Từ: H - BAR_H (Mép trên thanh đỏ)
    # Đến: H - TICKER_H (Mép trên thanh vàng)
    # Khoảng trống = 190 - 45 = 145px
    
    safe_zone_top = H - BAR_H
    safe_zone_bottom = H - TICKER_H
    center_y_zone = (safe_zone_top + safe_zone_bottom) / 2

    text_color = (255, 255, 255)
    headline_u = headline.upper()
    
    # Logic chọn font:
    if len(headline) < 25:
        # Ngắn: 1 dòng, font to
        font = get_font(70)
        # Căn giữa chính xác vùng an toàn
        # Lấy chiều cao font để căn (ước lượng font size)
        draw_centered_text(draw, headline_u, font, W/2, center_y_zone - 35, text_color)
        
    elif len(headline) < 50:
        # Trung bình: Font 50, max 2 dòng
        font = get_font(50)
        lines = textwrap.wrap(headline_u, width=35)
        
        # Tính tổng chiều cao khối text
        line_height = 55
        total_h = len(lines) * line_height
        start_y = center_y_zone - (total_h / 2) - 10
        
        for line in lines:
            draw_centered_text(draw, line, font, W/2, start_y, text_color)
            start_y += line_height
            
    else:
        # Dài: Font 42, max 2 dòng (cắt bớt nếu quá dài)
        font = get_font(42)
        lines = textwrap.wrap(headline_u, width=45)
        
        # Chỉ lấy tối đa 2 dòng để không bị tràn
        if len(lines) > 2:
            lines = lines[:2]
            lines[1] += "..." # Thêm dấu 3 chấm
            
        line_height = 48
        total_h = len(lines) * line_height
        start_y = center_y_zone - (total_h / 2) - 10
        
        for line in lines:
            draw_centered_text(draw, line, font, W/2, start_y, text_color)
            start_y += line_height

    # 6. Ticker (Chữ chạy bên dưới)
    tickers = [
        "Cảnh sát bó tay với độ đẹp trai của đối tượng.",
        "Người yêu cũ nhắn tin xin quay lại sau khi xem bản tin này.",
        "Giá xăng tăng, thanh niên chuyển sang đi bộ tán gái.",
        "Các nhà khoa học khẳng định: 99% người xem tin này rất cute.",
        "Dự báo thời tiết: Mưa to ở trong lòng người cô đơn."
    ]
    ticker_text = f"CẬP NHẬT: {random.choice(tickers)}   ***   TIN NÓNG: {random.choice(tickers)}"
    
    # Căn giữa theo chiều dọc của thanh vàng
    ticker_y = H - TICKER_H + 8
    draw.text((20, ticker_y), ticker_text, font=get_font(24), fill=(0, 0, 0))

    # 7. Logo TV
    LOGO_SIZE = 110
    logo_x = W - 150
    logo_y = H - BAR_H - 40
    
    draw.ellipse((logo_x, logo_y, logo_x+LOGO_SIZE, logo_y+LOGO_SIZE), fill=(255, 255, 255))
    draw.ellipse((logo_x+5, logo_y+5, logo_x+LOGO_SIZE-5, logo_y+LOGO_SIZE-5), outline=(0, 0, 150), width=4)
    draw_centered_text(draw, "TV", get_font(45), logo_x + LOGO_SIZE//2, logo_y + 30, (0, 0, 150))

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_news_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    target_id = author_id
    headline = ""

    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
        full_text = message_object.content
        parts = full_text.split()
        if len(parts) > 2:
            headline = " ".join(parts[2:])
    elif message_object.quote:
        target_id = message_object.quote.ownerId
        if len(content) > 1:
            headline = " ".join(content[1:])
    else:
        if len(content) > 1:
            headline = " ".join(content[1:])

    funny_headlines = [
        "Thanh niên bị bắt vì quá đẹp trai",
        "Phát hiện đối tượng trốn trại tâm thần",
        "Người đàn ông giàu nhất xóm vừa bị mất dép",
        "Nghi vấn hack map trong game Liên Quân",
        "Vừa trúng số độc đắc 100 tỷ (tiền âm phủ)",
        "Truy nã đặc biệt: Tội danh ăn nhiều ngủ kỹ"
    ]

    if not headline:
        headline = random.choice(funny_headlines)

    client.sendReaction(message_object, "📺", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'avatar'):
            avatar_url = user_info.avatar

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_breaking_news, avatar_url, headline)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/news_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1280,
            height=720,
            message=Message(text=f"📺 BẢN TIN NÓNG: {headline}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'news': handle_news_command,
        'thoisu': handle_news_command,
        'fakenews': handle_news_command
    }