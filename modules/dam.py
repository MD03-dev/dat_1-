import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import random
import time
import concurrent.futures
from datetime import datetime

# --- CONFIG ---
from config import PREFIX

des = {
    'version': "1.5.5",
    'credits': "Hoàng Khánh Prime",
    'description': "Check độ dâm",
    'power': "Thành viên"
}

# Đường dẫn cache
CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

if not os.path.exists(FONT_DIR):
    os.makedirs(FONT_DIR)

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try: 
        return ImageFont.truetype(FONT_PATH, size)
    except:
        try: 
            return ImageFont.truetype("arial.ttf", size)
        except: 
            return ImageFont.load_default()

def get_emoji_font(size):
    try: 
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: 
        return ImageFont.load_default()

def fetch_image(url):
    if not url: 
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: 
        return None

def fit_text_font(text, max_width, initial_size, min_size=15):
    current_size = initial_size
    font = get_font(current_size)
    text_str = str(text)
    
    while font.getlength(text_str) > max_width and current_size > min_size:
        current_size -= 2
        font = get_font(current_size)
    
    if font.getlength(text_str) > max_width:
        while font.getlength(text_str + "...") > max_width and len(text_str) > 3:
            text_str = text_str[:-1]
        text_str += "..."
    
    return font, text_str

def wrap_text(text, font, max_width, max_lines=None):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            
            if max_lines and len(lines) >= max_lines:
                if current_line:
                    lines.append(current_line + "...")
                break
    
    if current_line and (not max_lines or len(lines) < max_lines):
        lines.append(current_line)
    
    return lines

def create_progress_bar_single(draw, x, y, width, height, value, color_theme="bi"):
    """Tạo thanh tiến trình đơn với hiệu ứng đẹp - ĐÃ FIX LỖI"""
    radius = height // 2
    
    # Xác định màu sắc theo theme
    if color_theme == "bi":
        bar_colors = [(180, 100, 220), (150, 70, 190)]  # Tím
        bg_color = (60, 40, 80, 200)
    else:
        bar_colors = [(100, 220, 100), (60, 180, 60)]  # Xanh lá
        bg_color = (40, 60, 40, 200)
    
    # Nền thanh
    draw.rounded_rectangle((x, y, x+width, y+height), 
                          radius=radius, fill=bg_color)
    
    # Tính chiều rộng thanh giá trị
    bar_width = max(radius * 2, int((value / 100) * (width - radius * 2)))
    
    if bar_width > 0:
        # Vẽ phần thanh chính trước
        draw.rounded_rectangle((x, y, x + bar_width, y+height), 
                              radius=radius, fill=bar_colors[0])
        
        # Gradient thủ công (FIX: không dùng rectangle loop gây lỗi)
        if bar_width > radius * 2:
            # Tạo hiệu ứng gradient bằng cách vẽ các dải màu
            for i in range(0, bar_width - radius * 2, 3):
                ratio = i / (bar_width - radius * 2)
                r = int(bar_colors[0][0] * (1 - ratio) + bar_colors[1][0] * ratio)
                g = int(bar_colors[0][1] * (1 - ratio) + bar_colors[1][1] * ratio)
                b = int(bar_colors[0][2] * (1 - ratio) + bar_colors[1][2] * ratio)
                draw.rectangle([x + radius + i, y, x + radius + i + 3, y + height], 
                              fill=(r, g, b))
    
    return bar_width

def create_glass_box(draw, x, y, w, h, radius=20, alpha=200):
    """Tạo box với hiệu ứng kính"""
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          fill=(45, 35, 55, alpha))
    
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          outline=(255, 255, 255, 40), width=2)

# ================= PHÂN TÍCH DÂM =================

def detect_gender_simple(profile_data):
    gender_value = profile_data.get('gender', -1)
    gender_map = {0: "NAM", 1: "NỮ"}
    return gender_map.get(gender_value, "KHÔNG RÕ")

def analyze_dam_only(profile_data, gender):
    """Phân tích chỉ xu hướng dâm"""
    name = profile_data.get('name', 'Người dùng')
    avatar_url = profile_data.get('avatar', '')
    
    seed_str = f"{name}{avatar_url}{gender}"
    seed = sum(ord(c) for c in seed_str) + int(time.time()) % 1000
    random.seed(seed)
    
    dam_score = 40  # Điểm mặc định
    
    if avatar_url:
        dam_score += random.randint(-10, 20)
    else:
        dam_score += random.randint(-5, 10)
    
    # Điều chỉnh nhẹ dựa trên giới tính
    if gender == "NAM":
        dam_score += random.randint(-5, 15)
    elif gender == "NỮ":
        dam_score += random.randint(0, 20)
    
    dam_score = max(0, min(100, dam_score))
    
    # Xác định xu hướng
    if dam_score >= 70:
        orientation = "SIÊU DÂM DÂNG 🥵"
        confidence = "88%"
        description = "Phân tích cho thấy mức độ dâm rất cao, nhu cầu tình dục mạnh mẽ."
    elif dam_score >= 55:
        orientation = "DÂM RÕ RÀNG 🔥"
        confidence = "75%"
        description = "Mức độ dâm khá cao, có thể có nhu cầu tình dục lớn."
    elif dam_score >= 40:
        orientation = "CÓ THIÊN HƯỚNG DÂM 💫"
        confidence = "65%"
        description = "Có dấu hiệu của xu hướng dâm nhưng chưa thực sự mạnh mẽ."
    elif dam_score >= 25:
        orientation = "BÌNH THƯỜNG MỘT CHÚT 🌟"
        confidence = "55%"
        description = "Mức độ dâm ở mức bình thường, không quá đặc biệt."
    else:
        orientation = "TRONG SÁNG 👼"
        confidence = "80%"
        description = "Mức độ dâm rất thấp, có thể là người trong sáng."
    
    return {
        'gender': gender,
        'dam_score': dam_score,
        'orientation': orientation,
        'confidence': confidence,
        'description': description,
        'emoji': "🔥",
        'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

# ================= TẠO ẢNH KẾT QUẢ DAM =================

def create_dam_banner_simple(profile_data, analysis_result):
    width, height = 1000, 600
    bg = Image.new("RGBA", (width, height), (40, 30, 50))
    
    draw = ImageDraw.Draw(bg)
    
    # Gradient nền tím
    for i in range(height):
        r = int(40 + i * 0.03)
        g = int(30 + i * 0.04)
        b = int(50 + i * 0.05)
        draw.line((0, i, width, i), fill=(r, g, b, 255))
    
    # ====== PHẦN AVATAR ======
    avatar_url = profile_data.get('avatar', '')
    avt_size = 150
    avt_x, avt_y = 50, 50
    
    avatar_img = fetch_image(avatar_url)
    if not avatar_img:
        avatar_img = Image.new("RGBA", (avt_size, avt_size), (180, 100, 220))
    
    mask = Image.new("L", (avt_size, avt_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avt_size, avt_size), fill=255)
    
    avatar_resized = avatar_img.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    avatar_circle = Image.new("RGBA", (avt_size, avt_size))
    avatar_circle.paste(avatar_resized, mask=mask)
    
    border_width = 5
    draw.ellipse((avt_x-border_width, avt_y-border_width, 
                  avt_x+avt_size+border_width, avt_y+avt_size+border_width), 
                outline=(200, 120, 220), width=border_width)
    
    bg.paste(avatar_circle, (avt_x, avt_y), avatar_circle)
    
    # ====== THÔNG TIN CHÍNH ======
    text_x, text_y = 230, 60
    
    name = profile_data.get('name', 'Người dùng')
    name_font, name_text = fit_text_font(name, 700, 48, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, 
             fill=(255, 255, 255))
    
    gender_text = f"Giới tính: {analysis_result['gender']}"
    draw.text((text_x, text_y + 60), gender_text, 
             font=get_font(26), fill=(220, 200, 240))
    
    # ====== BOX XU HƯỚNG ======
    box_x, box_y = 50, 230
    box_width, box_height = 900, 320
    
    create_glass_box(draw, box_x, box_y, box_width, box_height, radius=20)
    
    # Tiêu đề - ĐÃ ĐƯA LÊN CAO HƠN
    draw.text((box_x + 30, box_y + 15), "🔥 PHÂN TÍCH XU HƯỚNG DÂM", 
              font=get_font(28), fill=(255, 255, 255))
    
    # ====== THANH % DUY NHẤT ======
    bar_x, bar_y = box_x + 50, box_y + 75  # ĐÃ NÂNG LÊN
    bar_width_total = 800
    bar_height = 50
    
    draw.text((bar_x, bar_y - 35), "MỨC ĐỘ DÂM:", 
              font=get_font(28), fill=(240, 220, 255))
    
    dam_score = analysis_result['dam_score']
    bar_width = create_progress_bar_single(draw, bar_x, bar_y, bar_width_total, 
                                          bar_height, dam_score, "bi")
    
    value_text = f"{dam_score}%"
    value_font = get_font(42)
    value_width = value_font.getlength(value_text)
    value_x = bar_x + bar_width_total + 20
    
    if value_x + value_width > box_x + box_width - 20:
        value_x = bar_x + bar_width_total - value_width - 10
    
    # ĐẶT SỐ % Ở GIỮA CHIỀU CAO THANH
    value_y = bar_y + (bar_height - value_font.size) // 2 + 2
    draw.text((value_x, value_y), value_text, 
              font=value_font, fill=(255, 255, 200))
    
    # ====== THÔNG TIN XU HƯỚNG ======
    info_y = bar_y + bar_height + 25  # Giảm khoảng cách
    
    orient_text = f"Xu hướng: {analysis_result['orientation']}"
    draw.text((box_x + 50, info_y), orient_text, 
              font=get_font(26), fill=(240, 200, 255))
    
    conf_y = info_y + 40
    conf_text = f"Độ tin cậy: {analysis_result['confidence']}"
    draw.text((box_x + 50, conf_y), conf_text, 
              font=get_font(24), fill=(220, 180, 240))
    
    # ====== MÔ TẢ ======
    desc_start_y = conf_y + 45
    desc_font = get_font(22)
    max_desc_width = 800
    
    desc_lines = wrap_text(analysis_result['description'], desc_font, max_desc_width, 2)
    
    for i, line in enumerate(desc_lines):
        line_y = desc_start_y + i * 30
        draw.text((box_x + 50, line_y), line, 
                 font=desc_font, fill=(240, 240, 240))
    
    # ====== FOOTER (ĐÃ XOÁ NGÀY PHÂN TÍCH) ======
    footer_y = box_y + box_height - 30
    
    watermark_text = "Dam Analysis v1.5.5"
    watermark_font = get_font(16)
    watermark_width = watermark_font.getlength(watermark_text)
    draw.text((width - watermark_width - 20, height - 25), watermark_text, 
              font=watermark_font, fill=(150, 100, 180))
    
    return bg.convert("RGB")

# ================= XỬ LÝ LỆNH DAM =================

def handle_dam_command(message, message_object, thread_id, thread_type, author_id, client):
    from zlapi.models import Message
    
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "🔍", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        if not user_info or not hasattr(user_info, 'changed_profiles'):
            client.replyMessage(Message(text="❌ Không thể lấy thông tin người dùng."), 
                              message_object, thread_id, thread_type)
            return

        profile = user_info.changed_profiles.get(str(target_id), {})
        
        profile_data = {
            'name': profile.get('zaloName', 'Người dùng'),
            'avatar': profile.get('avatar', ''),
            'gender': profile.get('gender', -1),
            'dob': profile.get('dob', 0),
            'cover': profile.get('cover', ''),
            'globalId': profile.get('globalId', '')
        }
        
        detected_gender = detect_gender_simple(profile_data)
        analysis_result = analyze_dam_only(profile_data, detected_gender)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_dam_banner_simple, profile_data, analysis_result)
            image = future.result()

        timestamp = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"dam_{timestamp}.jpg")
        
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
            
        image.save(img_path, quality=95)
        
        result_text = f"🔥 KẾT QUẢ PHÂN TÍCH ĐỘ DÂM:\n"
        result_text += f"👤 Tên: {profile_data['name']}\n"
        result_text += f"⚧️ Giới tính: {analysis_result['gender']}\n"
        result_text += f"🎯 Xu hướng: {analysis_result['orientation']}\n"
        result_text += f"📊 Mức độ Dâm: {analysis_result['dam_score']}%\n"
        result_text += f"💭 {analysis_result['description']}"
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=600,
            message=Message(text=result_text),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        try: 
            os.remove(img_path)
        except: 
            pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi phân tích: {str(e)}"), 
                          message_object, thread_id, thread_type)

def PTA():
    return {
        'dam': handle_dam_command,
        'dâm': handle_dam_command,
        'checkdam': handle_dam_command,
        'damcheck': handle_dam_command
    }