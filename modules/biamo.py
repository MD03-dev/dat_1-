# biamo.py
import os
import random
import re
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import requests
import base64
from zlapi.models import *

des = {'version': "5.0.0", 'credits': "Hoàng Khánh Prime", 'description': "Tạo ảnh bia mộ với hiệu ứng 3D", 'power': "Thành viên"}

# Đường dẫn font
FONT_DIR = "modules/cache/font/"
FONT_TITLE = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_NAME = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_NORMAL = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
FONT_EPITAPH = os.path.join(FONT_DIR, "BeVietnamPro-Italic.ttf")
FONT_SCRIPT = os.path.join(FONT_DIR, "DancingScript-Bold.ttf")

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

def create_cemetery_background():
    """Tạo nền nghĩa trang với hiệu ứng 3D"""
    width, height = 800, 600
    # Nền xanh lá tối cho nghĩa trang
    img = Image.new('RGB', (width, height), (30, 40, 25))
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Tạo gradient nền (tối dần từ trên xuống)
    for y in range(height):
        shade = int(20 * (y / height))
        r = 30 + shade
        g = 40 + shade
        b = 25 + shade
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Thêm cỏ (texture)
    grass_color = (50, 70, 40)
    for _ in range(500):
        x = random.randint(0, width-1)
        y = random.randint(height//2, height-1)
        size = random.randint(1, 3)
        draw.ellipse([x, y, x+size, y+size], fill=grass_color)
    
    # Thêm mây nhẹ
    cloud_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    cloud_draw = ImageDraw.Draw(cloud_layer)
    
    for _ in range(5):
        cloud_x = random.randint(0, width)
        cloud_y = random.randint(20, 150)
        cloud_width = random.randint(100, 200)
        cloud_height = random.randint(30, 50)
        
        for i in range(3):
            offset = i * 15
            alpha = random.randint(20, 40)
            cloud_draw.ellipse([
                cloud_x + offset, cloud_y,
                cloud_x + cloud_width + offset, cloud_y + cloud_height
            ], fill=(200, 220, 230, alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), cloud_layer)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    return img

def create_3d_gravestone():
    """Tạo bia mộ 3D chi tiết"""
    stone_width, stone_height = 350, 450
    stone = Image.new('RGBA', (stone_width, stone_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stone)
    
    # Màu đá granite
    granite_dark = (80, 80, 90, 255)
    granite_medium = (100, 100, 110, 255)
    granite_light = (120, 120, 130, 255)
    granite_highlight = (140, 140, 150, 255)
    
    # Phần thân bia mộ (hình thang với bo góc)
    # Tạo hiệu ứng 3D với đổ bóng
    stone_body = [
        (50, 50),  # top-left
        (stone_width - 50, 50),  # top-right
        (stone_width - 30, stone_height - 100),  # bottom-right
        (30, stone_height - 100)  # bottom-left
    ]
    
    # Vẽ mặt trước bia mộ
    draw.polygon(stone_body, fill=granite_medium)
    
    # Thêm hiệu ứng đá granite (texture)
    for _ in range(300):
        x = random.randint(50, stone_width - 50)
        y = random.randint(50, stone_height - 100)
        
        # Kiểm tra xem điểm có nằm trong polygon không
        brightness = random.randint(-10, 10)
        dot_color = (
            max(0, min(255, granite_medium[0] + brightness)),
            max(0, min(255, granite_medium[1] + brightness)),
            max(0, min(255, granite_medium[2] + brightness)),
            random.randint(150, 200)
        )
        size = random.randint(1, 2)
        draw.ellipse([x, y, x+size, y+size], fill=dot_color)
    
    # Vẽ mặt bên phải (hiệu ứng 3D)
    stone_side = [
        (stone_width - 50, 50),  # top-right front
        (stone_width - 30, 50),  # top-right back
        (stone_width - 10, stone_height - 100),  # bottom-right back
        (stone_width - 30, stone_height - 100)  # bottom-right front
    ]
    draw.polygon(stone_side, fill=granite_dark)
    
    # Vẽ mặt trên
    stone_top = [
        (50, 50),  # top-left front
        (stone_width - 50, 50),  # top-right front
        (stone_width - 30, 30),  # top-right back
        (30, 30)  # top-left back
    ]
    draw.polygon(stone_top, fill=granite_light)
    
    # Thêm viền trang trí cho bia mộ
    border_color = (60, 60, 70, 255)
    border_width = 3
    
    # Viền mặt trước
    for i in range(len(stone_body)):
        x1, y1 = stone_body[i]
        x2, y2 = stone_body[(i + 1) % len(stone_body)]
        draw.line([(x1, y1), (x2, y2)], fill=border_color, width=border_width)
    
    # Thêm chữ thập trên đỉnh bia mộ
    cross_size = 40
    cross_x = stone_width // 2
    cross_y = 90
    
    # Thân chữ thập
    draw.rectangle([cross_x - 8, cross_y, cross_x + 8, cross_y + 40], 
                  fill=(180, 160, 120, 255))
    draw.rectangle([cross_x - 20, cross_y + 15, cross_x + 20, cross_y + 25], 
                  fill=(180, 160, 120, 255))
    
    # Thêm highlight cho chữ thập
    draw.rectangle([cross_x - 6, cross_y, cross_x - 4, cross_y + 40], 
                  fill=(210, 190, 150, 255))
    draw.rectangle([cross_x - 20, cross_y + 17, cross_x - 18, cross_y + 23], 
                  fill=(210, 190, 150, 255))
    
    return stone

def add_avatar_to_gravestone(gravestone, avatar_image):
    """Thêm avatar lên bia mộ với hiệu ứng cũ"""
    stone = gravestone.copy()
    
    # Tạo khung oval cho ảnh
    oval_width, oval_height = 180, 180
    oval_x = (stone.width - oval_width) // 2
    oval_y = 120
    
    # Resize avatar
    avatar_resized = avatar_image.copy()
    avatar_resized.thumbnail((oval_width - 20, oval_height - 20), Image.Resampling.LANCZOS)
    
    # Tạo mask hình oval
    mask = Image.new('L', (oval_width, oval_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, oval_width, oval_height], fill=255)
    
    # Áp dụng hiệu ứng sepia và làm mờ cho avatar
    avatar_sepia = avatar_resized.convert('RGB')
    width, height = avatar_sepia.size
    pixels = avatar_sepia.load()
    
    for py in range(height):
        for px in range(width):
            r, g, b = pixels[px, py]
            # Công thức sepia nặng hơn
            tr = int(0.393 * r + 0.769 * g + 0.189 * b) * 0.9
            tg = int(0.349 * r + 0.686 * g + 0.168 * b) * 0.9
            tb = int(0.272 * r + 0.534 * g + 0.131 * b) * 0.9
            
            pixels[px, py] = (
                min(255, int(tr)),
                min(255, int(tg)),
                min(255, int(tb))
            )
    
    avatar_sepia = avatar_sepia.filter(ImageFilter.GaussianBlur(1))
    avatar_sepia = avatar_sepia.convert('RGBA')
    
    # Áp dụng mask
    avatar_sepia.putalpha(mask)
    
    # Tạo khung cho ảnh
    draw = ImageDraw.Draw(stone, 'RGBA')
    frame_thickness = 5
    frame_color = (100, 80, 60, 255)
    
    # Vẽ khung ngoài
    draw.ellipse([oval_x - frame_thickness, oval_y - frame_thickness,
                  oval_x + oval_width + frame_thickness, oval_y + oval_height + frame_thickness],
                 fill=frame_color)
    
    # Vẽ highlight cho khung
    draw.ellipse([oval_x - frame_thickness + 2, oval_y - frame_thickness + 2,
                  oval_x + oval_width + frame_thickness - 2, oval_y + oval_height + frame_thickness - 2],
                 outline=(150, 130, 100, 255), width=1)
    
    # Đặt avatar vào bia mộ
    avatar_x = oval_x + (oval_width - avatar_sepia.width) // 2
    avatar_y = oval_y + (oval_height - avatar_sepia.height) // 2
    stone.paste(avatar_sepia, (avatar_x, avatar_y), avatar_sepia)
    
    return stone

def generate_random_death_reasons():
    """Tạo hàng nghìn lý do chết nhảm (lấy ngẫu nhiên một số)"""
    reasons = [
        "Cười quá đà khi xem hài kịch",
        "Thử nghiệm bay từ tầng 3",
        "Ăn mì tôm 30 ngày không ngừng",
        "Tự sướng quá độ trước gương",
        "Đá bóng vào đầu mình",
        "Nuốt bàn chải điện thông minh",
        "Uống nước hoa thay nước lọc",
        "Thử làm phù thủy với công thức TikTok",
        "Nhảy cầu vì trend",
        "Ăn cục pin để thử sạc nhanh",
        "Đua xe đạp xuống cầu thang",
        "Cố chứng minh Trái Đất phẳng",
        "Tự cắt tóc bằng dao cạo",
        "Thử nếm nước rửa chén vì mùi thơm",
        "Ngủ quên trong tủ lạnh",
        "Tắm mưa giữa mùa đông",
        "Ăn 10 bát mì cay để livestream",
        "Nhịn thở 5 phút thử sức",
        "Đi xe đạp xuống dốc không phanh",
        "Tự sạc điện thoại bằng dây sạc tự chế",
        "Uống 5 lít nước một lúc",
        "Ngã từ cây khi cố selfie",
        "Tự nhuộm tóc bằng thuốc tẩy",
        "Thử nhảy lầu vì bạn bè thách đố",
        "Ăn cát để chứng minh không sao",
        "Tự tiêm nước lã vào tay",
        "Chạy marathon không nghỉ",
        "Nhảy từ mái nhà xuống bể bơi cạn",
        "Tự đấm vào mặt vì tức giận",
        "Ăn xà phòng để tạo bong bóng trong miệng",
        "Thử luyện ngón tay vào ổ điện",
        "Chơi đùa với ong vò vẽ",
        "Tự cắt móng tay bằng kéo lớn",
        "Nhịn ăn 1 tuần để giảm cân",
        "Uống rượu pha nước ngọt quá liều",
        "Tự nhổ răng bằng kìm",
        "Chạy xe máy vào tường thử airbag",
        "Tắm nước sôi để thử độ chịu đựng",
        "Ăn thức ăn ôi thiu 1 tuần",
        "Tự chích thuốc không rõ nguồn gốc",
        "Nhảy múa trên lan can ban công",
        "Thử lửa với xăng",
        "Tự đốt tóc để làm kiểu",
        "Ăn đá lạnh cả ngày",
        "Chơi đùa với rắn độc",
        "Tự đóng đinh vào tay",
        "Nhảy từ cầu xuống sông cạn",
        "Thử độ sắc của dao mổ",
        "Tự cạo lông mày bằng dao cạo",
        "Ăn kim loại để livestream"
    ]
    
    # Chọn ngẫu nhiên 3-5 lý do
    num_reasons = random.randint(3, 5)
    selected_reasons = random.sample(reasons, num_reasons)
    
    return selected_reasons

def generate_random_dates():
    """Tạo ngày sinh và ngày mất ngẫu nhiên"""
    birth_year = random.randint(1950, 2020)
    death_year = random.randint(2024, 2100)
    
    birth_month = random.randint(1, 12)
    death_month = random.randint(1, 12)
    
    # Sinh nhật
    if birth_month == 2:
        birth_day = random.randint(1, 29) if (birth_year % 4 == 0) else random.randint(1, 28)
    elif birth_month in [4, 6, 9, 11]:
        birth_day = random.randint(1, 30)
    else:
        birth_day = random.randint(1, 31)
    
    # Ngày mất
    if death_month == 2:
        death_day = random.randint(1, 29) if (death_year % 4 == 0) else random.randint(1, 28)
    elif death_month in [4, 6, 9, 11]:
        death_day = random.randint(1, 30)
    else:
        death_day = random.randint(1, 31)
    
    return (
        f"{birth_day:02d}/{birth_month:02d}/{birth_year}",
        f"{death_day:02d}/{death_month:02d}/{death_year}"
    )

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

def add_grass_and_flowers(img, grave_x, grave_y, grave_width, grave_height):
    """Thêm cỏ và hoa xung quanh bia mộ"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Thêm cỏ phía trước bia mộ
    grass_start_y = grave_y + grave_height - 50
    grass_end_y = grave_y + grave_height + 30
    
    for y in range(grass_start_y, grass_end_y, 3):
        for x in range(grave_x - 20, grave_x + grave_width + 20, 5):
            if random.random() > 0.7:
                grass_height = random.randint(5, 15)
                grass_width = random.randint(1, 2)
                grass_color = random.choice([
                    (60, 90, 50, 200),
                    (70, 100, 60, 200),
                    (50, 80, 40, 200)
                ])
                
                # Vẽ cọng cỏ
                offset_x = random.randint(-1, 1)
                draw.line([(x, y), (x + offset_x, y - grass_height)], 
                         fill=grass_color, width=grass_width)
    
    # Thêm hoa nhỏ
    flower_colors = [
        (255, 200, 200, 200),  # Hồng nhạt
        (200, 200, 255, 200),  # Xanh nhạt
        (255, 255, 200, 200),  # Vàng nhạt
        (255, 220, 180, 200),  # Cam nhạt
    ]
    
    for _ in range(15):
        flower_x = random.randint(grave_x - 30, grave_x + grave_width + 30)
        flower_y = random.randint(grass_start_y - 20, grass_end_y)
        
        if flower_x < grave_x or flower_x > grave_x + grave_width or flower_y < grass_start_y:
            flower_color = random.choice(flower_colors)
            flower_size = random.randint(3, 6)
            
            # Vẽ cánh hoa
            for i in range(5):
                angle = math.radians(i * 72)
                petal_x = flower_x + int(flower_size * math.cos(angle))
                petal_y = flower_y + int(flower_size * math.sin(angle))
                draw.ellipse([petal_x-2, petal_y-2, petal_x+2, petal_y+2], 
                            fill=flower_color)
            
            # Vẽ nhụy hoa
            draw.ellipse([flower_x-1, flower_y-1, flower_x+1, flower_y+1], 
                        fill=(240, 200, 50, 220))
    
    return img

def biamo(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Xác định người dùng mục tiêu
        mentions = message_object.mentions
        if mentions:
            target_id = mentions[0]['uid']
        else:
            # Nếu không tag ai thì dùng chính người gửi
            target_id = author_id
        
        # Lấy thông tin người dùng
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
            avatar_image = Image.new('RGBA', (500, 500), (100, 100, 100, 255))
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
        
        # Tạo ngày sinh và ngày mất
        birth_date, death_date = generate_random_dates()
        
        # Tạo các lý do chết
        death_reasons = generate_random_death_reasons()
        
        # ========== TẠO ẢNH BIA MỘ ==========
        
        # Tạo nền nghĩa trang
        background = create_cemetery_background()
        draw = ImageDraw.Draw(background, 'RGBA')
        
        # Tạo bia mộ 3D
        gravestone = create_3d_gravestone()
        
        # Thêm avatar lên bia mộ
        gravestone_with_avatar = add_avatar_to_gravestone(gravestone, avatar_image)
        
        # Đặt bia mộ vào giữa ảnh
        grave_width, grave_height = gravestone_with_avatar.size
        grave_x = (background.width - grave_width) // 2
        grave_y = (background.height - grave_height) // 2 - 50
        
        background.paste(gravestone_with_avatar, (grave_x, grave_y), gravestone_with_avatar)
        
        # Thêm cỏ và hoa xung quanh bia mộ
        background = add_grass_and_flowers(background, grave_x, grave_y, grave_width, grave_height)
        
        # Tải font
        font_title = get_safe_font(FONT_TITLE, 36)
        font_name = get_safe_font(FONT_NAME, 32)
        font_dates = get_safe_font(FONT_NORMAL, 24)
        font_reason = get_safe_font(FONT_EPITAPH, 18)
        font_script = get_safe_font(FONT_SCRIPT, 28)
        
        # Màu sắc cho text
        title_color = (220, 220, 220, 255)  # Trắng xám
        name_color = (240, 240, 220, 255)   # Vàng nhạt
        dates_color = (200, 200, 200, 255)  # Xám nhạt
        reason_color = (180, 180, 160, 255) # Xám vàng
        script_color = (220, 200, 180, 255) # Vàng nâu
        
        # Vẽ tiêu đề phía trên bia mộ
        title = "NƠI AN NGHỈ NGÀN THU"
        title_y = grave_y - 60
        
        draw_text_with_shadow(
            draw, title, (background.width // 2, title_y),
            font_title, title_color, shadow_color=(0, 0, 0, 150),
            shadow_offset=(3, 3), stroke_width=2, stroke_color=(0, 0, 0, 100)
        )
        
        # Vẽ tên người trên bia mộ (dưới avatar)
        name_text = user.displayName.upper() if hasattr(user, 'displayName') else "NGƯỜI DÙNG"
        name_y = grave_y + 320
        
        draw_text_with_shadow(
            draw, name_text, (background.width // 2, name_y),
            font_name, name_color, shadow_color=(0, 0, 0, 150),
            shadow_offset=(2, 2), stroke_width=1, stroke_color=(50, 50, 50, 150)
        )
        
        # Vẽ ngày sinh và ngày mất
        dates_text = f"⏳ {birth_date}  –  ✞ {death_date} ✞"
        dates_y = name_y + 40
        
        draw_text_with_shadow(
            draw, dates_text, (background.width // 2, dates_y),
            font_dates, dates_color, shadow_color=(0, 0, 0, 120),
            shadow_offset=(2, 2)
        )
        
        # Vẽ dòng chữ trang trí
        decor_text = "◈ ĐÃ RA ĐI NHƯNG KHÔNG BAO GIỜ QUÊN ◈"
        decor_y = grave_y + grave_height + 30
        
        draw_text_with_shadow(
            draw, decor_text, (background.width // 2, decor_y),
            font_script, script_color, shadow_color=(0, 0, 0, 100),
            shadow_offset=(1, 1)
        )
        
        # Vẽ các lý do chết phía dưới bia mộ
        reasons_start_y = decor_y + 50
        max_reason_width = background.width - 100
        
        # Tiêu đề phần lý do
        reason_title = "✞ NGUYÊN NHÂN QUA ĐỜI ✞"
        reason_title_y = reasons_start_y
        
        draw_text_with_shadow(
            draw, reason_title, (background.width // 2, reason_title_y),
            font_reason, (200, 100, 100, 255), shadow_color=(0, 0, 0, 100),
            shadow_offset=(1, 1)
        )
        
        # Vẽ từng lý do
        for i, reason in enumerate(death_reasons):
            reason_y = reason_title_y + 30 + (i * 28)
            reason_text = f"› {reason}"
            
            draw_text_with_shadow(
                draw, reason_text, (background.width // 2, reason_y),
                font_reason, reason_color, shadow_color=(0, 0, 0, 80),
                shadow_offset=(1, 1)
            )
        
        # Thêm hiệu ứng ánh sáng cho bia mộ
        highlight_layer = Image.new('RGBA', background.size, (0, 0, 0, 0))
        highlight_draw = ImageDraw.Draw(highlight_layer)
        
        # Thêm highlight cho cạnh bia mộ
        highlight_points = [
            (grave_x + 50, grave_y + 50),
            (grave_x + grave_width - 50, grave_y + 50),
            (grave_x + grave_width - 30, grave_y + grave_height - 100),
            (grave_x + 30, grave_y + grave_height - 100)
        ]
        
        # Vẽ highlight nhẹ
        for i in range(len(highlight_points)):
            x1, y1 = highlight_points[i]
            x2, y2 = highlight_points[(i + 1) % len(highlight_points)]
            
            # Vẽ đường highlight mờ
            for j in range(3):
                offset = j
                highlight_draw.line([(x1 + offset, y1 + offset), (x2 + offset, y2 + offset)],
                                   fill=(255, 255, 255, 30), width=1)
        
        background = Image.alpha_composite(background, highlight_layer)
        
        # Thêm hiệu ứng sương mù nhẹ
        fog_layer = Image.new('RGBA', background.size, (0, 0, 0, 0))
        fog_draw = ImageDraw.Draw(fog_layer)
        
        for _ in range(20):
            fog_x = random.randint(0, background.width)
            fog_y = random.randint(grave_y - 50, background.height)
            fog_size = random.randint(50, 150)
            fog_alpha = random.randint(5, 15)
            
            fog_draw.ellipse([fog_x, fog_y, fog_x + fog_size, fog_y + fog_size // 3],
                            fill=(200, 220, 240, fog_alpha))
        
        background = Image.alpha_composite(background, fog_layer)
        
        # ========== LƯU VÀ GỬI ẢNH ==========
        
        output_path = "modules/cache/biamo_final.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        background.save(output_path, "PNG", quality=95)
        
        # Tin nhắn kèm theo
        user_display = user.displayName if hasattr(user, 'displayName') else "Người dùng"
        reasons_text = "\n".join([f"• {reason}" for reason in death_reasons])
        
        message_text = f"""🪦 BIA MỘ VĨNH HẰNG 🪦

📌 Người được tưởng niệm: {user_display}
📅 Sinh nhật: {birth_date}
✟ Ngày mất: {death_date}

📖 Các nguyên nhân qua đời:
{reasons_text}

✨ Bia mộ 3D đã được tạo với đầy đủ chi tiết"""

        client.sendLocalImage(
            imagePath=output_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=message_text)
        )
        
        print(f"✅ Đã tạo ảnh bia mộ cho {user_display}")
        
    except Exception as e:
        print(f"❌ Lỗi trong lệnh biamo: {e}")
        import traceback
        traceback.print_exc()
        client.send(
            Message(text=f"❌ Đã xảy ra lỗi khi tạo ảnh bia mộ:\n{str(e)}"),
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
        'biamo': biamo
    }