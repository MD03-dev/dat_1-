# bantho.py
import os
import random
import re
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import requests
import base64
from zlapi.models import *

des = {'version': "5.0.0", 'credits': "Hoàng Khánh Prime", 'description': "Tạo ảnh bàn thờ với nền xám và nhang cháy", 'power': "Thành viên"}

# Đường dẫn font
FONT_DIR = "modules/cache/font/"
FONT_TITLE = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_NAME = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_NORMAL = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
FONT_DECOR = os.path.join(FONT_DIR, "BeVietnamPro-Italic.ttf")

def get_safe_font(font_path, size, fallback="arial.ttf"):
    """Lấy font an toàn"""
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        return ImageFont.truetype(fallback, size)
    except:
        return ImageFont.load_default()

def fetch_image(url):
    """Tải ảnh avatar"""
    if not url:
        return None
    try:
        if url.startswith('data:image'):
            header, encoded_data = url.split(',', 1)
            decoded_data = base64.b64decode(encoded_data)
            return Image.open(BytesIO(decoded_data)).convert("RGBA")
        
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def create_gray_background_altar():
    """Tạo ảnh bàn thờ với nền xám nhạt"""
    width, height = 800, 600
    # Nền xám nhạt (RGB: 230, 230, 230)
    img = Image.new('RGB', (width, height), (230, 230, 230))
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Thêm hiệu ứng gradient nhẹ cho nền
    for y in range(height):
        # Chuyển từ xám nhạt ở trên sang xám đậm hơn ở dưới
        shade = int(15 * (y / height))
        r = 230 - shade
        g = 230 - shade
        b = 230 - shade
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Thêm hiệu ứng texture nhẹ cho nền
    for _ in range(300):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        alpha = random.randint(5, 15)
        size = random.randint(1, 2)
        draw.ellipse([x, y, x+size, y+size], 
                    fill=(220, 220, 220, alpha))
    
    # Vẽ bóng đổ mờ cho khu vực bàn thờ
    shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    
    altar_area = (150, 80, 650, 450)
    shadow_blur = 15
    
    for i in range(shadow_blur):
        alpha = int(10 * (1 - i/shadow_blur))
        current_rect = (
            altar_area[0] - i,
            altar_area[1] - i,
            altar_area[2] + i,
            altar_area[3] + i
        )
        shadow_draw.rounded_rectangle(current_rect, radius=20, 
                                    fill=(0, 0, 0, alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), shadow_layer)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Vẽ nền cho khu vực bàn thờ (màu trắng ngà)
    altar_bg_color = (245, 240, 235, 255)
    draw.rounded_rectangle(altar_area, radius=20, fill=altar_bg_color)
    
    # Thêm viền cho khu vực bàn thờ
    border_color = (180, 160, 140, 255)
    border_width = 2
    draw.rounded_rectangle(altar_area, radius=20, 
                          outline=border_color, width=border_width)
    
    return img, altar_area

def create_small_incense_burner():
    """Tạo bát hương nhỏ với 3 cây nhang"""
    width, height = 120, 100  # Kích thước nhỏ
    burner = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(burner)
    
    # Màu đồng cổ cho bát hương
    bronze_dark = (120, 70, 30, 255)
    bronze_medium = (150, 90, 40, 255)
    bronze_light = (180, 110, 50, 255)
    
    # Vẽ bát hương (kích thước nhỏ)
    # Phần đáy
    draw.ellipse([40, 70, 80, 85], fill=bronze_dark)
    
    # Phần thân
    draw.ellipse([35, 50, 85, 75], fill=bronze_medium)
    
    # Phần miệng
    draw.ellipse([30, 40, 90, 65], fill=bronze_light)
    
    # Thêm hoa văn nhỏ trên bát hương
    pattern_color = (200, 150, 80, 180)
    for i in range(6):
        angle = math.radians(i * 60)
        x = 60 + int(20 * math.cos(angle))
        y = 57 + int(10 * math.sin(angle))
        draw.ellipse([x-2, y-2, x+2, y+2], fill=pattern_color)
    
    return burner

def draw_small_burning_incense(draw, burner_pos, altar_area):
    """Vẽ 3 cây nhang cháy nhỏ"""
    burner_center_x = burner_pos[0] + 60  # Tâm bát hương
    burner_top_y = burner_pos[1] + 40     # Đỉnh bát hương
    
    incense_sticks = []
    
    # Tạo 3 cây nhang
    for i in range(3):
        # Góc nghiêng khác nhau cho mỗi cây nhang
        if i == 0:
            angle = math.radians(-10)
        elif i == 1:
            angle = math.radians(0)
        else:
            angle = math.radians(10)
        
        # Vị trí gốc nhang (trong bát hương)
        base_x = burner_center_x + (i-1) * 15  # Phân bố đều
        base_y = burner_top_y
        
        incense_sticks.append({
            'base_x': base_x,
            'base_y': base_y,
            'angle': angle,
            'height': 70  # Chiều cao nhang
        })
    
    for stick in incense_sticks:
        base_x = stick['base_x']
        base_y = stick['base_y']
        angle = stick['angle']
        height = stick['height']
        
        # Tính toán tọa độ đầu nhang
        tip_x = base_x + int(height * math.sin(angle))
        tip_y = base_y - int(height * math.cos(angle))
        
        # Vẽ thân nhang (màu cam)
        stick_width = 2
        for i in range(stick_width):
            offset = i - stick_width//2
            # Thân màu cam
            draw.line([(base_x + int(offset * math.cos(angle)), base_y + int(offset * math.sin(angle))),
                      (tip_x + int(offset * math.cos(angle)), tip_y + int(offset * math.sin(angle)))],
                     fill=(255, 140, 0, 220), width=1)
        
        # Vẽ phần nhang cháy (đầu đỏ đang cháy)
        burn_length = 12
        burn_tip_x = tip_x + int(burn_length * math.sin(angle))
        burn_tip_y = tip_y - int(burn_length * math.cos(angle))
        
        # Phần than hồng (đỏ)
        for i in range(3, 0, -1):
            current_length = burn_length * i // 3
            current_x = tip_x + int(current_length * math.sin(angle))
            current_y = tip_y - int(current_length * math.cos(angle))
            
            alpha = 150 + i * 35
            if i == 3:  # Phần đỏ rực nhất
                color = (255, 50, 0, alpha)
            elif i == 2:  # Phần cam
                color = (255, 100, 0, alpha)
            else:  # Phần vàng
                color = (255, 180, 0, alpha)
            
            draw.line([(tip_x, tip_y), (current_x, current_y)],
                     fill=color, width=2)
        
        # Vẽ lửa nhỏ
        flame_size = 6
        flame_x = burn_tip_x
        flame_y = burn_tip_y
        
        # Lõi lửa (trắng vàng)
        draw.ellipse([flame_x-1, flame_y-2, flame_x+1, flame_y],
                    fill=(255, 255, 200, 220))
        
        # Vùng lửa chính (đỏ cam)
        for i in range(flame_size, 0, -2):
            alpha = int(180 * (i/flame_size))
            
            # Màu lửa thay đổi từ vàng -> cam -> đỏ
            if i > flame_size * 0.7:
                color = (255, 255, 100, alpha)
            elif i > flame_size * 0.4:
                color = (255, 150, 50, alpha)
            else:
                color = (255, 80, 0, alpha)
            
            draw.ellipse([flame_x-i, flame_y-i*1.5, 
                         flame_x+i, flame_y+i//2],
                        fill=color)
        
        # Vẽ ít khói từ nhang
        smoke_height = 15
        smoke_start_y = flame_y - flame_size//2
        
        for i in range(smoke_height):
            smoke_y = smoke_start_y - i
            smoke_radius = 2 + i//4
            smoke_alpha = int(80 * (1 - i/smoke_height) ** 0.5)
            
            # Khói loãng dần
            offset_x = random.randint(-i//3, i//3)
            
            draw.ellipse([flame_x + offset_x - smoke_radius,
                         smoke_y - smoke_radius//2,
                         flame_x + offset_x + smoke_radius,
                         smoke_y + smoke_radius//2],
                        fill=(200, 200, 200, smoke_alpha))
    
    return burner_center_x, burner_top_y

def create_photo_frame(avatar_image):
    """Tạo khung ảnh cho avatar"""
    frame_width, frame_height = 220, 280
    
    # Resize avatar vừa với khung
    avatar = avatar_image.copy()
    avatar.thumbnail((frame_width - 20, frame_height - 20), Image.LANCZOS)
    
    # Tạo khung ảnh
    frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    
    # Màu khung (nâu gỗ)
    frame_color = (101, 67, 33, 255)
    frame_inner_color = (139, 90, 43, 255)
    
    # Vẽ khung ngoài
    frame_draw.rounded_rectangle([0, 0, frame_width, frame_height], 
                                radius=10, fill=frame_color)
    
    # Vẽ khung trong
    frame_draw.rounded_rectangle([5, 5, frame_width-5, frame_height-5], 
                                radius=8, fill=frame_inner_color)
    
    # Vẽ viền vàng trang trí
    frame_draw.rounded_rectangle([2, 2, frame_width-2, frame_height-2], 
                                radius=9, outline=(255, 215, 0, 200), width=2)
    
    # Đặt avatar vào giữa khung
    avatar_x = (frame_width - avatar.width) // 2
    avatar_y = (frame_height - avatar.height) // 2
    
    # Áp dụng hiệu ứng sepia cho avatar
    avatar_sepia = avatar.convert('RGB')
    width, height = avatar_sepia.size
    pixels = avatar_sepia.load()
    
    for py in range(height):
        for px in range(width):
            r, g, b = pixels[px, py]
            
            # Công thức sepia
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            
            pixels[px, py] = (
                min(255, tr),
                min(255, tg),
                min(255, tb)
            )
    
    avatar_sepia = avatar_sepia.convert('RGBA')
    
    # Tạo mask bo góc cho avatar
    avatar_mask = Image.new('L', avatar_sepia.size, 0)
    mask_draw = ImageDraw.Draw(avatar_mask)
    mask_draw.rounded_rectangle([0, 0, avatar_sepia.width, avatar_sepia.height], 
                               radius=5, fill=255)
    
    avatar_sepia.putalpha(avatar_mask)
    
    # Đặt avatar vào khung
    frame.paste(avatar_sepia, (avatar_x, avatar_y), avatar_sepia)
    
    # Thêm hiệu ứng bóng đổ nhẹ
    shadow = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    for i in range(3):
        alpha = int(40 * (1 - i/3))
        shadow_draw.rounded_rectangle([i, i, frame_width-i, frame_height-i], 
                                     radius=10, outline=(0, 0, 0, alpha), width=1)
    
    frame = Image.alpha_composite(frame, shadow)
    
    return frame

def generate_random_death_date():
    """Tạo ngày mất ngẫu nhiên đẹp"""
    year = random.randint(2024, 2100)
    month = random.randint(1, 12)
    
    if month == 2:
        day = random.randint(1, 29) if (year % 4 == 0) else random.randint(1, 28)
    elif month in [4, 6, 9, 11]:
        day = random.randint(1, 30)
    else:
        day = random.randint(1, 31)
    
    # Định dạng đẹp
    month_names = ["01", "02", "03", "04", "05", "06",
                   "07", "08", "09", "10", "11", "12"]
    
    return f"{day:02d}/{month_names[month-1]}/{year}"

def get_random_death_reason():
    """Lấy lý do chết ngẫu nhiên (xàm)"""
    reasons = [
        "Ra đi trong giấc ngủ ngàn thu",
        "Quá đẹp trai nên bị thiên đình triệu hồi",
        "Tự sướng quá liều với gương",
        "Cười vỡ bụng khi xem hài",
        "Ăn mì tôm 30 ngày liên tục",
        "Đá bóng vào cột điện",
        "Thử làm phù thủy tập sự",
        "Nuốt bàn chải đánh răng thông minh",
        "Đu trend TikTok nhảy cầu",
        "Cố chứng minh mình có siêu năng lực",
        "Tập bay từ tầng 2",
        "Uống nước hoa thay nước lọc",
        "Đấm gương vì không đẹp bằng ảnh filter",
        "Ăn thử cục pin để xem có sạc được không",
        "Đi xe đạp xuống cầu thang"
    ]
    return random.choice(reasons)

def draw_text_with_shadow(draw, text, position, font, color, shadow_color=(0,0,0,150), 
                         shadow_offset=(2,2), align="center", stroke_width=0, stroke_color=None):
    """Vẽ text với hiệu ứng shadow và stroke đẹp"""
    x, y = position
    
    if align == "center":
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Vẽ shadow
        shadow_x = x - text_width//2 + shadow_offset[0]
        shadow_y = y + shadow_offset[1]
        draw.text((shadow_x, shadow_y), text, fill=shadow_color, font=font)
        
        # Vẽ stroke nếu có
        if stroke_width > 0 and stroke_color:
            for dx in [-stroke_width, 0, stroke_width]:
                for dy in [-stroke_width, 0, stroke_width]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x - text_width//2 + dx, y + dy), text, 
                             fill=stroke_color, font=font)
        
        # Vẽ text chính
        draw.text((x - text_width//2, y), text, fill=color, font=font)
        
        return text_height
    else:
        # Vẽ shadow
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, 
                 fill=shadow_color, font=font, align=align)
        
        # Vẽ stroke nếu có
        if stroke_width > 0 and stroke_color:
            for dx in [-stroke_width, 0, stroke_width]:
                for dy in [-stroke_width, 0, stroke_width]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), text, fill=stroke_color, font=font, align=align)
        
        # Vẽ text chính
        draw.text((x, y), text, fill=color, font=font, align=align)
        
        bbox = draw.textbbox((x, y), text, font=font, align=align)
        return bbox[3] - bbox[1]

def wrap_text_to_fit(text, font, max_width):
    """Tách text thành nhiều dòng để vừa chiều rộng"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def bantho(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Lấy người được tag
        mentions = message_object.mentions
        if not mentions:
            client.send(
                Message(text="🕯️ Vui lòng tag người cần tạo ảnh bàn thờ!\n\n📝 Cách dùng:\n• bantho @Tên\n• bantho @Tên điền lí do chết [nội dung]"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        target_id = mentions[0]['uid']
        
        # Lấy thông tin người được tag
        user_info = client.fetchUserInfo(target_id)
        user = user_info.changed_profiles.get(target_id)
        
        if not user:
            client.send(
                Message(text="❌ Không thể lấy thông tin người dùng này."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Lấy avatar
        avatar_url = getattr(user, 'avatar', None)
        avatar_image = fetch_image(avatar_url)
        
        if not avatar_image:
            # Tạo avatar mặc định với ký tự đầu tên
            avatar_image = Image.new('RGBA', (500, 500), (80, 80, 80, 255))
            draw_temp = ImageDraw.Draw(avatar_image)
            try:
                font_temp = ImageFont.truetype("arial.ttf", 200)
            except:
                font_temp = ImageFont.load_default()
            
            initial = user.displayName[0].upper() if user.displayName else "?"
            bbox = draw_temp.textbbox((250, 250), initial, font=font_temp)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw_temp.text((250 - text_width//2, 250 - text_height//2), initial, 
                          fill=(180, 180, 180), font=font_temp)
        
        # Xử lý lý do chết
        death_reason = None
        
        # Tìm "điền lí do chết" trong message
        message_lower = message.lower()
        
        if "điền lí do chết" in message_lower or "điền lý do chết" in message_lower:
            # Tìm vị trí bắt đầu của lý do
            start_patterns = ["điền lí do chết", "điền lý do chết"]
            start_pos = -1
            
            for pattern in start_patterns:
                pos = message_lower.find(pattern)
                if pos != -1:
                    start_pos = pos + len(pattern)
                    break
            
            if start_pos != -1:
                # Lấy phần sau pattern
                death_reason = message[start_pos:].strip()
                
                # Loại bỏ các tag và khoảng trắng thừa
                death_reason = re.sub(r'@\S+', '', death_reason).strip()
                
                # Nếu lý do bắt đầu bằng dấu ngoặc hoặc dấu cách đặc biệt, loại bỏ
                death_reason = re.sub(r'^[^\w\s]+', '', death_reason)
        
        # Nếu không có lý do hoặc lý do rỗng, dùng lý do xàm ngẫu nhiên
        if not death_reason or death_reason.strip() == "":
            death_reason = get_random_death_reason()
        else:
            # Giới hạn độ dài lý do
            if len(death_reason) > 120:
                death_reason = death_reason[:117] + "..."
        
        # Tạo ngày mất
        death_date = generate_random_death_date()
        
        # ========== TẠO ẢNH BÀN THỜ ==========
        
        # Tạo ảnh nền xám
        altar_img, altar_area = create_gray_background_altar()
        draw = ImageDraw.Draw(altar_img, 'RGBA')
        
        # Tạo khung ảnh với avatar
        photo_frame = create_photo_frame(avatar_image)
        frame_width, frame_height = photo_frame.size
        
        # Đặt khung ảnh ở giữa bàn thờ, phía trên
        frame_x = altar_area[0] + (altar_area[2] - altar_area[0] - frame_width) // 2
        frame_y = altar_area[1] + 50
        
        altar_img.paste(photo_frame, (frame_x, frame_y), photo_frame)
        
        # Tạo bát hương nhỏ
        incense_burner = create_small_incense_burner()
        burner_width, burner_height = incense_burner.size
        
        # Đặt bát hương ở trước khung ảnh (phía dưới, chính giữa)
        burner_x = frame_x + (frame_width - burner_width) // 2
        burner_y = frame_y + frame_height - 40  # Đặt sát dưới khung ảnh
        
        altar_img.paste(incense_burner, (burner_x, burner_y), incense_burner)
        
        # Vẽ nhang cháy
        burner_center_x, burner_top_y = draw_small_burning_incense(draw, (burner_x, burner_y), altar_area)
        
        # Tải font với kích thước phù hợp
        font_title = get_safe_font(FONT_TITLE, 32)
        font_name = get_safe_font(FONT_NAME, 28)
        font_date = get_safe_font(FONT_NORMAL, 22)
        font_reason = get_safe_font(FONT_NORMAL, 18)
        font_decor = get_safe_font(FONT_DECOR, 16)
        
        # Màu sắc cho text (tối để nổi trên nền xám)
        title_color = (160, 40, 40, 255)  # Đỏ đậm
        name_color = (50, 50, 50, 255)    # Đen xám
        date_color = (100, 60, 30, 255)   # Nâu
        reason_color = (70, 70, 70, 255)  # Xám đậm
        decor_color = (120, 120, 120, 200) # Xám nhạt
        shadow_color = (0, 0, 0, 100)     # Bóng đổ nhẹ
        
        # Vị trí viết text (phía dưới bàn thờ)
        text_area_y = altar_area[3] + 20
        center_x = (altar_area[0] + altar_area[2]) // 2
        
        # Vẽ tiêu đề - CHỈNH SỬA: "BÀN THỜ TƯỞNG NIỆM"
        title = "BÀN THỜ TƯỞNG NIỆM"
        title_y = text_area_y
        
        text_height = draw_text_with_shadow(
            draw, title, (center_x, title_y), font_title, title_color,
            shadow_color=shadow_color, shadow_offset=(2, 2),
            stroke_width=1, stroke_color=(0, 0, 0, 150)
        )
        
        # Vẽ tên người (viết hoa)
        name_text = user.displayName.upper()
        name_y = title_y + text_height + 15
        
        name_height = draw_text_with_shadow(
            draw, name_text, (center_x, name_y),
            font_name, name_color, shadow_color,
            shadow_offset=(2, 2), stroke_width=1,
            stroke_color=(255, 255, 255, 100)
        )
        
        # Vẽ ngày mất: ✟ Ngày mất ✟
        date_text = f"✟ {death_date} ✟"
        date_y = name_y + name_height + 10
        
        date_height = draw_text_with_shadow(
            draw, date_text, (center_x, date_y),
            font_date, date_color, shadow_color,
            shadow_offset=(1, 1)
        )
        
        # Vẽ lý do chết: » Lý do chết (từng dòng)
        reason_start_y = date_y + date_height + 10
        max_reason_width = altar_area[2] - altar_area[0] - 80
        
        # Tách lý do thành các dòng
        reason_lines = wrap_text_to_fit(death_reason, font_reason, max_reason_width)
        
        # Vẽ từng dòng lý do với bullet »
        for i, line in enumerate(reason_lines):
            line_y = reason_start_y + i * 24
            
            # Thêm bullet » cho mỗi dòng
            bullet_text = f"» {line}"
            draw_text_with_shadow(
                draw, bullet_text, (center_x, line_y),
                font_reason, reason_color, shadow_color,
                shadow_offset=(1, 1), align="center"
            )
        
        # Vẽ dòng chữ trang trí ở dưới cùng: "─═══ ◈ Vĩnh Biệt ◈ ═══─"
        bottom_decor = "─═══ ◈ Vĩnh Biệt ◈ ═══─"
        bottom_y = 570
        
        draw_text_with_shadow(
            draw, bottom_decor, (center_x, bottom_y),
            font_decor, decor_color, shadow_color=(0, 0, 0, 80),
            shadow_offset=(1, 1), align="center"
        )
        
        # Thêm hiệu ứng khói tỏa từ nhang
        smoke_layer = Image.new('RGBA', altar_img.size, (0, 0, 0, 0))
        smoke_draw = ImageDraw.Draw(smoke_layer)
        
        # Vị trí tâm bát hương
        burner_center_x = burner_x + 60
        burner_top_y = burner_y + 40
        
        # Vẽ ít khói (theo yêu cầu)
        smoke_height = 40
        smoke_width = 30
        
        for i in range(smoke_height):
            current_y = burner_top_y - i
            current_width = int(smoke_width * (1 - i/smoke_height))
            current_alpha = int(30 * (1 - i/smoke_height) ** 0.7)
            
            # Thêm chuyển động ngẫu nhiên nhẹ
            offset_x = random.randint(-5, 5)
            
            smoke_draw.ellipse([
                burner_center_x + offset_x - current_width//2,
                current_y - 3,
                burner_center_x + offset_x + current_width//2,
                current_y + 3
            ], fill=(200, 200, 200, current_alpha))
        
        altar_img = Image.alpha_composite(altar_img, smoke_layer)
        
        # ========== LƯU VÀ GỬI ẢNH ==========
        
        output_path = "modules/cache/bantho_final.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        altar_img.save(output_path, "PNG", quality=95)
        
        # Tin nhắn kèm theo
        user_display = user.displayName if hasattr(user, 'displayName') else "Người dùng"
        message_text = f"""🕯️ BÀN THỜ TƯỞNG NIỆM 🕯️

📌 Người được tưởng niệm: {user_display}
📅 Ngày mất: {death_date}
📖 Lý do: {death_reason}

✨ Ảnh đã được tạo với bát hương nhỏ và 3 cây nhang cháy"""
        
        client.sendLocalImage(
            imagePath=output_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=message_text)
        )
        
        print(f"✅ Đã tạo ảnh bàn thờ cho {user_display}")
        
    except Exception as e:
        print(f"❌ Lỗi trong lệnh bantho: {e}")
        import traceback
        traceback.print_exc()
        client.send(
            Message(text=f"❌ Đã xảy ra lỗi khi tạo ảnh:\n{str(e)[:100]}"),
            thread_id=thread_id,
            thread_type=thread_type
        )
    finally:
        if 'output_path' in locals() and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

def PTA():
    return {
        'bantho': bantho
    }