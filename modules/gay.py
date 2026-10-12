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
    'description': "Check độ gay",
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

def create_progress_bar_single(draw, x, y, width, height, value, color_theme="gay"):
    """Tạo thanh tiến trình đơn với hiệu ứng đẹp - ĐÃ FIX LỖI"""
    radius = height // 2
    
    # Xác định màu sắc theo theme
    if color_theme == "gay":
        bar_colors = [(0, 180, 255), (0, 120, 200)]  # Xanh da trời
        bg_color = (40, 50, 80, 200)
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
    # Box chính
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          fill=(30, 35, 50, alpha))
    
    # Hiệu ứng viền sáng
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          outline=(255, 255, 255, 40), width=2)

# ================= PHÂN TÍCH GAY =================

def detect_gender_simple(profile_data):
    """Phát hiện giới tính đơn giản từ dữ liệu profile"""
    gender_value = profile_data.get('gender', -1)
    gender_map = {0: "NAM", 1: "NỮ"}
    return gender_map.get(gender_value, "KHÔNG RÕ")

def analyze_gay_only(profile_data, gender):
    """Phân tích chỉ xu hướng đồng tính nam"""
    name = profile_data.get('name', 'Người dùng')
    avatar_url = profile_data.get('avatar', '')
    
    # Tạo seed ngẫu nhiên từ dữ liệu profile
    seed_str = f"{name}{avatar_url}{gender}"
    seed = sum(ord(c) for c in seed_str) + int(time.time()) % 1000
    random.seed(seed)
    
    # Phân tích dựa trên avatar (nếu có)
    gay_score = 50  # Điểm mặc định
    
    if avatar_url:
        # Tăng điểm ngẫu nhiên nếu có avatar
        gay_score += random.randint(-20, 30)
    else:
        # Giảm điểm nếu không có avatar
        gay_score += random.randint(-10, 10)
    
    # Điều chỉnh dựa trên giới tính
    if gender == "NAM":
        gay_score += random.randint(0, 25)
    elif gender == "NỮ":
        gay_score -= random.randint(20, 40)
    
    # Đảm bảo trong khoảng 0-100
    gay_score = max(0, min(100, gay_score))
    
    # Xác định xu hướng
    if gay_score >= 80:
        orientation = "GAY CHÍNH HIỆU 🏳️‍🌈"
        confidence = "96%"
        description = "Phân tích cho thấy xu hướng đồng tính nam rất rõ ràng với độ tin cậy cao."
    elif gay_score >= 65:
        orientation = "CÓ THIÊN HƯỚNG GAY 🌈"
        confidence = "85%"
        description = "Xu hướng đồng tính nam khá rõ rệt, thể hiện qua nhiều đặc điểm phân tích."
    elif gay_score >= 50:
        orientation = "KHẢ NĂNG GAY TRUNG BÌNH 💫"
        confidence = "70%"
        description = "Có dấu hiệu của xu hướng đồng tính nam nhưng chưa thực sự rõ ràng."
    elif gay_score >= 35:
        orientation = "STRAIGHT MỞ 🌟"
        confidence = "60%"
        description = "Chủ yếu là straight nhưng có sự cởi mở với trải nghiệm đồng giới."
    else:
        orientation = "STRAIGHT RÕ RÀNG 👨‍❤️‍👨"
        confidence = "85%"
        description = "Xu hướng dị tính nam rõ ràng, ít biểu hiện đồng tính."
    
    return {
        'gender': gender,
        'gay_score': gay_score,
        'orientation': orientation,
        'confidence': confidence,
        'description': description,
        'emoji': "🏳️‍🌈",
        'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

# ================= TẠO ẢNH KẾT QUẢ GAY =================

def create_gay_banner_simple(profile_data, analysis_result):
    """Tạo banner đơn giản chỉ hiển thị 1 thanh %"""
    width, height = 1000, 600
    bg = Image.new("RGBA", (width, height), (20, 25, 40))
    
    draw = ImageDraw.Draw(bg)
    
    # Gradient nền
    for i in range(height):
        r = int(20 + i * 0.03)
        g = int(25 + i * 0.05)
        b = int(40 + i * 0.07)
        draw.line((0, i, width, i), fill=(r, g, b, 255))
    
    # ====== PHẦN AVATAR ======
    avatar_url = profile_data.get('avatar', '')
    avt_size = 150
    avt_x, avt_y = 50, 50
    
    avatar_img = fetch_image(avatar_url)
    if not avatar_img:
        # Avatar mặc định với màu xanh da trời
        avatar_img = Image.new("RGBA", (avt_size, avt_size), (0, 150, 255))
    
    # Avatar hình tròn
    mask = Image.new("L", (avt_size, avt_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avt_size, avt_size), fill=255)
    
    avatar_resized = avatar_img.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    avatar_circle = Image.new("RGBA", (avt_size, avt_size))
    avatar_circle.paste(avatar_resized, mask=mask)
    
    # Viền avatar
    border_width = 5
    draw.ellipse((avt_x-border_width, avt_y-border_width, 
                  avt_x+avt_size+border_width, avt_y+avt_size+border_width), 
                outline=(0, 180, 255), width=border_width)
    
    bg.paste(avatar_circle, (avt_x, avt_y), avatar_circle)
    
    # ====== THÔNG TIN CHÍNH ======
    text_x, text_y = 230, 60
    
    # Tên
    name = profile_data.get('name', 'Người dùng')
    name_font, name_text = fit_text_font(name, 700, 48, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, 
             fill=(255, 255, 255))
    
    # Giới tính
    gender_text = f"Giới tính: {analysis_result['gender']}"
    draw.text((text_x, text_y + 60), gender_text, 
             font=get_font(26), fill=(180, 220, 255))
    
    # ====== BOX XU HƯỚNG ======
    box_x, box_y = 50, 230
    box_width, box_height = 900, 320
    
    create_glass_box(draw, box_x, box_y, box_width, box_height, radius=20)
    
    # Tiêu đề - ĐÃ ĐƯA LÊN CAO HƠN
    draw.text((box_x + 30, box_y + 15), "🏳️‍🌈 PHÂN TÍCH XU HƯỚNG ĐỒNG TÍNH NAM", 
              font=get_font(28), fill=(255, 255, 255))
    
    # ====== THANH % DUY NHẤT ======
    bar_x, bar_y = box_x + 50, box_y + 75  # ĐÃ NÂNG LÊN
    bar_width_total = 800
    bar_height = 50
    
    # Nhãn
    draw.text((bar_x, bar_y - 35), "MỨC ĐỘ GAY:", 
              font=get_font(28), fill=(220, 240, 255))
    
    # Thanh giá trị
    gay_score = analysis_result['gay_score']
    bar_width = create_progress_bar_single(draw, bar_x, bar_y, bar_width_total, 
                                          bar_height, gay_score, "gay")
    
    # Giá trị phần trăm lớn - ĐÃ ĐƯA LÊN GIỮA
    value_text = f"{gay_score}%"
    value_font = get_font(42)
    value_width = value_font.getlength(value_text)
    value_x = bar_x + bar_width_total + 20
    
    # Đảm bảo không vượt quá box
    if value_x + value_width > box_x + box_width - 20:
        value_x = bar_x + bar_width_total - value_width - 10
    
    # ĐẶT SỐ % Ở GIỮA CHIỀU CAO THANH
    value_y = bar_y + (bar_height - value_font.size) // 2 + 2
    draw.text((value_x, value_y), value_text, 
              font=value_font, fill=(255, 255, 200))
    
    # ====== THÔNG TIN XU HƯỚNG ======
    info_y = bar_y + bar_height + 25  # Giảm khoảng cách
    
    # Xu hướng
    orient_text = f"Xu hướng: {analysis_result['orientation']}"
    draw.text((box_x + 50, info_y), orient_text, 
              font=get_font(26), fill=(255, 220, 120))
    
    # Độ tin cậy
    conf_y = info_y + 40
    conf_text = f"Độ tin cậy: {analysis_result['confidence']}"
    draw.text((box_x + 50, conf_y), conf_text, 
              font=get_font(24), fill=(180, 240, 180))
    
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
    
    # Watermark đơn giản
    watermark_text = "Gay Analysis v1.5.5"
    watermark_font = get_font(16)
    watermark_width = watermark_font.getlength(watermark_text)
    draw.text((width - watermark_width - 20, height - 25), watermark_text, 
              font=watermark_font, fill=(100, 150, 180))
    
    return bg.convert("RGB")

# ================= XỬ LÝ LỆNH GAY =================

def handle_gay_command(message, message_object, thread_id, thread_type, author_id, client):
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
        analysis_result = analyze_gay_only(profile_data, detected_gender)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_gay_banner_simple, profile_data, analysis_result)
            image = future.result()

        timestamp = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"gay_{timestamp}.jpg")
        
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
            
        image.save(img_path, quality=95)
        
        # Tin nhắn kết quả đơn giản
        result_text = f"🏳️‍🌈 KẾT QUẢ PHÂN TÍCH ĐỒNG TÍNH NAM:\n"
        result_text += f"👤 Tên: {profile_data['name']}\n"
        result_text += f"⚧️ Giới tính: {analysis_result['gender']}\n"
        result_text += f"🎯 Xu hướng: {analysis_result['orientation']}\n"
        result_text += f"📊 Mức độ Gay: {analysis_result['gay_score']}%\n"
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
        'gay': handle_gay_command,
        'checkgay': handle_gay_command,
        'gaycheck': handle_gay_command
    }