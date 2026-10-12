import os
import importlib
import tempfile
import json
import math
from datetime import datetime
from zlapi.models import Message
from config import PREFIX
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

# ================= CẤU HÌNH PATH =================
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

des = {
    'version': "4.4.0",
    'credits': "Hoàng Khánh Prime Cte",
    'description': "Menu help",
    'power': "Thành viên"
}

# ================= CÁC HÀM HỖ TRỢ SÁNG TẠO =================
def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def create_neon_background(size):
    """Tạo background neon với hiệu ứng gradient"""
    width, height = size
    
    # Tạo gradient nền tối
    bg = Image.new('RGB', size, (10, 10, 20))
    
    # Thêm các vòng tròn neon
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Vòng tròn neon chính
    colors = [
        (0, 100, 255, 30),    # Xanh dương
        (255, 0, 255, 20),    # Tím
        (0, 255, 255, 25),    # Xanh cyan
    ]
    
    for i, (r, g, b, a) in enumerate(colors):
        radius = width // (3 - i) + 100
        center_x = width // 2 + (i * 50 - 50)
        center_y = height // 2 + (i * 30 - 30)
        
        for r2 in range(radius, radius - 50, -5):
            alpha = int(a * (r2 / radius))
            draw.ellipse(
                [center_x - r2, center_y - r2, center_x + r2, center_y + r2],
                outline=(r, g, b, alpha),
                width=2
            )
    
    # Thêm các chấm sáng
    import random
    for _ in range(200):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 3)
        brightness = random.randint(100, 200)
        draw.ellipse(
            [x, y, x + size, y + size],
            fill=(brightness, brightness + 30, brightness + 60, 100)
        )
    
    bg = Image.alpha_composite(bg.convert('RGBA'), overlay)
    return bg

def create_glass_card(size, color=(255, 255, 255, 30)):
    """Tạo card với hiệu ứng kính mờ"""
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    # Vẽ background với hiệu ứng kính
    draw.rounded_rectangle(
        [0, 0, size[0], size[1]],
        radius=20,
        fill=color
    )
    
    # Thêm viền neon
    border_color = (100, 200, 255, 100)
    draw.rounded_rectangle(
        [2, 2, size[0]-2, size[1]-2],
        radius=18,
        outline=border_color,
        width=2
    )
    
    return card

def wrap_text_neon(text, font, max_width):
    """Wrap text với xử lý tốt hơn"""
    if not text:
        return []
    
    words = str(text).split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.getlength(test_line) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def autosave(img, quality=95):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(
            tf,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True
        )
        return tf.name

def get_all_PTA_with_info():
    """Lấy thông tin module với xử lý string an toàn"""
    PTA_info = {}
    
    if not os.path.exists('modules'):
        return PTA_info
    
    for module_name in os.listdir('modules'):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, 'PTA'):
                    commands = module.PTA()
                    if commands and isinstance(commands, dict):
                        command_names = list(commands.keys())
                        if command_names:
                            _des = getattr(module, 'des', {})
                            
                            # Xử lý an toàn
                            version = str(_des.get('version', '1.0.0')) if _des else '1.0.0'
                            description = str(_des.get('description', 'Không có mô tả')) if _des else 'Không có mô tả'
                            power = str(_des.get('power', 'Thành viên')) if _des else 'Thành viên'
                            
                            if not power or power.strip() == '':
                                power = 'Thành viên'
                            
                            module_key = module_name[:-3]
                            PTA_info[module_key] = {
                                'aliases': command_names,
                                'version': version,
                                'description': description,
                                'power': power
                            }
            except Exception as e:
                print(f"[MODULE ERROR] {module_name}: {e}")
                continue
    
    return PTA_info

def get_power_info(power_str):
    """Lấy thông tin chi tiết về quyền"""
    if not power_str:
        return {
            'display': 'Thành viên',
            'color': (100, 255, 100),
            'icon': '👤',
            'level': 1
        }
    
    power_lower = str(power_str).lower().strip()
    
    power_map = {
        'admin': {'display': 'Admin', 'color': (255, 50, 50), 'icon': '👑', 'level': 5},
        'administrator': {'display': 'Admin', 'color': (255, 50, 50), 'icon': '👑', 'level': 5},
        'owner': {'display': 'Owner', 'color': (255, 100, 0), 'icon': '⚡', 'level': 6},
        'chủ': {'display': 'Owner', 'color': (255, 100, 0), 'icon': '⚡', 'level': 6},
        'moderator': {'display': 'Mod', 'color': (255, 180, 0), 'icon': '🛡️', 'level': 4},
        'mod': {'display': 'Mod', 'color': (255, 180, 0), 'icon': '🛡️', 'level': 4},
        'vip': {'display': 'VIP', 'color': (180, 100, 255), 'icon': '💎', 'level': 3},
        'premium': {'display': 'Premium', 'color': (100, 200, 255), 'icon': '⭐', 'level': 2},
        'thành viên': {'display': 'Thành viên', 'color': (100, 255, 100), 'icon': '👤', 'level': 1},
        'member': {'display': 'Thành viên', 'color': (100, 255, 100), 'icon': '👤', 'level': 1}
    }
    
    for key, info in power_map.items():
        if key in power_lower:
            return info
    
    # Mặc định
    return {
        'display': power_str.title(),
        'color': (150, 200, 255),
        'icon': '🔹',
        'level': 1
    }

def categorize_commands_creative(PTA_info):
    """Phân loại lệnh sáng tạo"""
    categories = {
        'all': {'name': 'Tất cả', 'icon': '🌐', 'color': (100, 200, 255)},
        'game': {'name': 'Game', 'icon': '🎮', 'color': (255, 100, 150)},
        'fun': {'name': 'Giải trí', 'icon': '😂', 'color': (255, 200, 50)},
        'tool': {'name': 'Công cụ', 'icon': '🛠️', 'color': (100, 255, 150)},
        'media': {'name': 'Media', 'icon': '🎵', 'color': (255, 100, 255)},
        'info': {'name': 'Thông tin', 'icon': 'ℹ️', 'color': (100, 150, 255)},
        'system': {'name': 'Hệ thống', 'icon': '⚙️', 'color': (200, 200, 200)},
        'admin': {'name': 'Quản trị', 'icon': '👑', 'color': (255, 50, 50)}
    }
    
    categorized = {key: [] for key in categories.keys()}
    categorized['all'] = list(PTA_info.items())  # Tất cả lệnh
    
    for module_key, info in PTA_info.items():
        description = str(info.get('description', '')).lower()
        aliases = [str(a).lower() for a in info.get('aliases', [])]
        power_info = get_power_info(info.get('power', ''))
        
        # Phân loại theo quyền
        if power_info['level'] >= 5:
            categorized['admin'].append((module_key, info))
        
        # Phân loại theo nội dung
        if 'game' in description or any('game' in a for a in aliases):
            categorized['game'].append((module_key, info))
        elif 'fun' in description or 'joke' in description or 'vui' in description:
            categorized['fun'].append((module_key, info))
        elif 'tool' in description or 'tiện ích' in description or 'utility' in description:
            categorized['tool'].append((module_key, info))
        elif 'media' in description or 'nhạc' in description or 'video' in description or 'ảnh' in description:
            categorized['media'].append((module_key, info))
        elif 'info' in description or 'thông tin' in description or 'xem' in description:
            categorized['info'].append((module_key, info))
        elif 'system' in description or 'hệ thống' in description:
            categorized['system'].append((module_key, info))
    
    # Lọc các category rỗng (trừ 'all')
    return {k: v for k, v in categorized.items() if v or k == 'all'}

# ================= VẼ MENU NEON FUTURISTIC =================
# ================= VẼ MENU NEON FUTURISTIC =================
def draw_neon_dashboard(categories, selected_category='all'):
    """Vẽ dashboard neon với các category - Tự động điều chỉnh chiều cao"""
    WIDTH = 1250
    
    # Tính toán chiều cao dựa trên số lượng lệnh
    commands = categories.get(selected_category, [])
    max_commands = min(20, len(commands))  # Tối đa 20 lệnh
    cmd_spacing = 70  # Giảm khoảng cách giữa các lệnh
    
    # Tính chiều cao cần thiết
    BASE_HEIGHT = 600  # Chiều cao cố định cho header và category
    HEIGHT = BASE_HEIGHT + (max_commands * cmd_spacing) + 150  # Thêm footer
    
    # Đảm bảo chiều cao tối thiểu và tối đa
    HEIGHT = max(1000, min(HEIGHT, 2550))
    
    # Tạo background neon với chiều cao động
    bg = create_neon_background((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(bg)
    
    # Font chữ
    font_title = get_font(60)
    font_subtitle = get_font(32)
    font_category = get_font(40)
    font_command = get_font(32)  # Giảm kích thước font
    font_desc = get_font(24)     # Giảm kích thước font
    font_info = get_font(22)     # Giảm kích thước font
    emoji_font = get_emoji_font(45)
    
    # Header với hiệu ứng
    header_bg = Image.new('RGBA', (WIDTH, 180), (0, 0, 0, 150))
    bg.alpha_composite(header_bg, (0, 0))
    
    # Tiêu đề chính với glow effect
    title = "🚀 BOT COMMAND DASHBOARD"
    title_x = WIDTH // 2 - font_title.getlength(title) // 2
    draw.text((title_x, 50), title, font=font_title, fill=(255, 255, 255))
    
    # Hiệu ứng glow cho tiêu đề
    for i in range(3, 0, -1):
        glow_color = (100, 200, 255, 30 // i)
        draw.text((title_x - i, 50 - i), title, font=font_title, fill=glow_color)
        draw.text((title_x + i, 50 + i), title, font=font_title, fill=glow_color)
    
    # Thông tin hệ thống
    now = datetime.now().strftime("%H:%M %d/%m/%Y")
    sys_info = f"⏰ {now} • Prefix: {PREFIX} • Commands: {len(categories['all'])}"
    info_x = WIDTH // 2 - font_subtitle.getlength(sys_info) // 2
    draw.text((info_x, 120), sys_info, font=font_subtitle, fill=(180, 220, 255))
    
    # Category selector (dashboard style) - Đơn giản hóa để tiết kiệm không gian
    y_cat = 200
    
    # Hiển thị các category như card - Chỉ hiển thị 4 category đầu
    category_keys = list(categories.keys())
    
    for i, cat_key in enumerate(category_keys[:4]):  # Chỉ hiển thị 4 category đầu
        # Sửa lỗi: Lấy thông tin category từ cấu hình mặc định
        cat_map = {
            'all': {'name': 'Tất cả', 'icon': '🌐', 'color': (100, 200, 255)},
            'game': {'name': 'Game', 'icon': '🎮', 'color': (255, 100, 150)},
            'fun': {'name': 'Giải trí', 'icon': '😂', 'color': (255, 200, 50)},
            'tool': {'name': 'Công cụ', 'icon': '🛠️', 'color': (100, 255, 150)},
            'media': {'name': 'Media', 'icon': '🎵', 'color': (255, 100, 255)},
            'info': {'name': 'Thông tin', 'icon': 'ℹ️', 'color': (100, 150, 255)},
            'system': {'name': 'Hệ thống', 'icon': '⚙️', 'color': (200, 200, 200)},
            'admin': {'name': 'Quản trị', 'icon': '👑', 'color': (255, 50, 50)}
        }
        
        cat_info = cat_map.get(cat_key, {'name': cat_key.title(), 'icon': '📁', 'color': (150, 150, 150)})
        cat_name = cat_info['name']
        cat_icon = cat_info['icon']
        cat_color = cat_info['color']
        count = len(categories.get(cat_key, []))
        
        x_cat = 100 + (i % 2) * 550  # 2 cột thay vì 3
        y_cat = 200 + (i // 2) * 160  # Giảm khoảng cách dọc
        
        # Card category nhỏ hơn
        card_size = (500, 140)
        card = create_glass_card(card_size, (*cat_color, 40))
        
        # Thêm highlight nếu được chọn
        if cat_key == selected_category:
            border = Image.new('RGBA', (card_size[0] + 6, card_size[1] + 6), (*cat_color, 80))
            bg.alpha_composite(border, (x_cat - 3, y_cat - 3))
        
        bg.alpha_composite(card, (x_cat, y_cat))
        
        # Icon và tên - Kích thước nhỏ hơn
        draw.text((x_cat + 20, y_cat + 25), cat_icon, font=emoji_font, fill=cat_color)
        draw.text((x_cat + 80, y_cat + 35), cat_name, font=font_category, fill=cat_color)
        
        # Số lượng lệnh
        count_text = f"{count} lệnh"
        count_width = font_info.getlength(count_text)
        draw.text((x_cat + card_size[0] - count_width - 20, y_cat + 90), 
                 count_text, font=font_info, fill=(200, 220, 255))
    
    # Điều chỉnh vị trí danh sách lệnh
    num_rows = math.ceil(min(len(category_keys), 4) / 2)
    y_commands = 200 + (num_rows * 160) + 40
    
    draw.text((100, y_commands - 40), f"📋 LỆNH TRONG {selected_category.upper()}", 
              font=font_subtitle, fill=(255, 255, 255))
    
    if commands:
        # Hiển thị lệnh với khoảng cách nhỏ hơn
        max_commands = 20  # Tăng số lệnh có thể hiển thị
        cmd_spacing = 70   # Khoảng cách nhỏ hơn
        
        for idx, (module_key, info) in enumerate(commands[:max_commands]):
            y_cmd = y_commands + idx * cmd_spacing
            
            # Dừng nếu vượt quá chiều cao ảnh
            if y_cmd + 70 > HEIGHT - 200:
                break
            
            # Card lệnh nhỏ hơn
            card_width = WIDTH - 200
            card_height = 65  # Giảm chiều cao card
            card = create_glass_card((card_width, card_height), (255, 255, 255, 20))
            bg.alpha_composite(card, (100, y_cmd))
            
            # Icon lệnh (dựa trên ký tự đầu)
            cmd_icon = module_key[0].upper() if module_key else "⚡"
            draw.text((120, y_cmd + 10), cmd_icon, font=emoji_font, fill=(100, 200, 255))
            
            # Tên lệnh chính - Rút gọn nếu quá dài
            main_alias = info['aliases'][0] if info['aliases'] else module_key
            cmd_text = f"{PREFIX}{main_alias}"
            if len(cmd_text) > 25:
                cmd_text = cmd_text[:22] + "..."
            draw.text((170, y_cmd + 8), cmd_text, font=font_command, fill=(255, 255, 255))
            
            # Mô tả ngắn - Rút gọn hơn
            desc = str(info.get('description', ''))
            if len(desc) > 30:
                desc = desc[:27] + "..."
            draw.text((170, y_cmd + 45), desc, font=font_desc, fill=(180, 220, 255))
            
            # Quyền với icon - Kích thước nhỏ hơn
            power_info = get_power_info(info.get('power', ''))
            power_text = f"{power_info['icon']}"
            power_width = font_info.getlength(power_text)
            draw.text((WIDTH - 100 - power_width, y_cmd + 20), power_text, 
                     font=font_info, fill=power_info['color'])
    
    # Footer với navigation
    footer_bg = Image.new('RGBA', (WIDTH, 140), (0, 0, 0, 150))
    
    # Đặt footer ở cuối ảnh
    footer_y = HEIGHT - 140
    bg.alpha_composite(footer_bg, (0, footer_y))
    
    nav_texts = [
        f"🎮 {PREFIX}menugame - Menu game",
        f"🔍 {PREFIX}help <tên> - Tìm kiếm",
        f"📖 {PREFIX}help <số> - Phân trang"
    ]
    
    for i, text in enumerate(nav_texts):
        draw.text(
            (WIDTH // 2 - font_info.getlength(text) // 2, footer_y + 20 + i * 25),
            text,
            font=font_info,
            fill=(150, 200, 255)
        )
    
    # Thông tin tổng số lệnh
    total_text = f"📊 Tổng: {len(commands)} lệnh • Trang 1/{math.ceil(len(commands)/20)}"
    draw.text(
        (WIDTH // 2 - font_info.getlength(total_text) // 2, footer_y + 95),
        total_text,
        font=font_info,
        fill=(255, 255, 200)
    )
    
    # Credit với hiệu ứng neon
    credit = f"✨ Designed by Quocbaoo • v{des['version']}"
    draw.text(
        (WIDTH // 2 - font_info.getlength(credit) // 2, footer_y + 120),
        credit,
        font=font_info,
        fill=(255, 255, 255)
    )
    
    return bg

def draw_command_detail_neon(module_key, info):
    """Vẽ chi tiết lệnh với phong cách neon"""
    WIDTH, HEIGHT = 900, 1200
    
    bg = create_neon_background((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(bg)
    
    font_title = get_font(48)
    font_subtitle = get_font(36)
    font_text = get_font(30)
    font_info = get_font(28)
    font_big = get_font(60)
    emoji_font = get_emoji_font(50)
    
    # Header card
    header_card = create_glass_card((WIDTH - 100, 200), (100, 200, 255, 40))
    bg.alpha_composite(header_card, (50, 50))
    
    # Icon lớn
    main_alias = info['aliases'][0] if info['aliases'] else module_key
    cmd_icon = main_alias[0].upper() if main_alias else "⚡"
    draw.text((WIDTH // 2 - 30, 70), cmd_icon, font=emoji_font, fill=(100, 200, 255))
    
    # Tên lệnh lớn
    cmd_text = f"{PREFIX}{main_alias}"
    draw.text(
        (WIDTH // 2 - font_big.getlength(cmd_text) // 2, 130),
        cmd_text,
        font=font_big,
        fill=(255, 255, 255)
    )
    
    y = 300
    
    # Thông tin chi tiết trong cards
    sections = [
        {
            'title': '📦 Module',
            'content': module_key,
            'color': (100, 200, 255)
        },
        {
            'title': '🏷️ Phiên bản',
            'content': info['version'],
            'color': (255, 200, 100)
        },
        {
            'title': '👑 Quyền truy cập',
            'content': get_power_info(info.get('power', ''))['display'],
            'color': get_power_info(info.get('power', ''))['color']
        }
    ]
    
    for section in sections:
        # Card section
        section_card = create_glass_card((WIDTH - 100, 100), (*section['color'], 30))
        bg.alpha_composite(section_card, (50, y))
        
        draw.text((70, y + 25), section['title'], font=font_subtitle, fill=section['color'])
        
        content_x = WIDTH - 80 - font_text.getlength(section['content'])
        draw.text((content_x, y + 30), section['content'], font=font_text, fill=(255, 255, 255))
        
        y += 120
    
    # Cách sử dụng
    y += 20
    draw.text((70, y), "📝 Cách sử dụng:", font=font_subtitle, fill=(255, 255, 200))
    y += 50
    
    aliases = info['aliases']
    aliases_text = " • ".join([f"{PREFIX}{a}" for a in aliases])
    
    # Card aliases
    aliases_card = create_glass_card((WIDTH - 100, 80), (255, 255, 255, 20))
    bg.alpha_composite(aliases_card, (50, y))
    
    aliases_lines = wrap_text_neon(aliases_text, font_text, WIDTH - 140)
    for line in aliases_lines:
        draw.text((70, y + 20), line, font=font_text, fill=(200, 220, 255))
        y += 40
    y += 20
    
    # Mô tả đầy đủ
    draw.text((70, y), "📄 Mô tả chi tiết:", font=font_subtitle, fill=(255, 255, 200))
    y += 50
    
    description = str(info['description'])
    desc_card = create_glass_card((WIDTH - 100, 300), (255, 255, 255, 15))
    bg.alpha_composite(desc_card, (50, y))
    
    desc_lines = wrap_text_neon(description, font_text, WIDTH - 140)
    for line in desc_lines:
        draw.text((70, y + 20), line, font=font_text, fill=(220, 240, 255))
        y += 40
    
    # Footer
    footer_card = create_glass_card((WIDTH - 100, 100), (0, 0, 0, 100))
    bg.alpha_composite(footer_card, (50, HEIGHT - 120))
    
    back_text = f"🔙 Dùng {PREFIX}help để quay lại menu"
    draw.text(
        (WIDTH // 2 - font_info.getlength(back_text) // 2, HEIGHT - 90),
        back_text,
        font=font_info,
        fill=(150, 200, 255)
    )
    
    return bg

def draw_search_results_neon(results, search_term):
    """Vẽ kết quả tìm kiếm với phong cách neon - Chiều cao động"""
    WIDTH = 1000
    
    # Tính toán chiều cao dựa trên số lượng kết quả
    max_results = min(len(results), 15)  # Tối đa 15 kết quả
    result_spacing = 110
    
    # Chiều cao cơ bản (header + footer)
    BASE_HEIGHT = 400
    HEIGHT = BASE_HEIGHT + (max_results * result_spacing)
    
    # Đảm bảo chiều cao hợp lý
    HEIGHT = max(800, min(HEIGHT, 2500))
    
    bg = create_neon_background((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(bg)
    
    font_title = get_font(52)
    font_subtitle = get_font(36)
    font_command = get_font(32)
    font_desc = get_font(26)
    font_info = get_font(24)
    emoji_font = get_emoji_font(45)
    
    # Header với hiệu ứng tìm kiếm
    header_card = create_glass_card((WIDTH - 100, 180), (255, 100, 150, 40))
    bg.alpha_composite(header_card, (50, 50))
    
    search_icon = "🔍"
    draw.text((WIDTH // 2 - 25, 70), search_icon, font=emoji_font, fill=(255, 150, 200))
    
    title = f"KẾT QUẢ TÌM KIẾM"
    draw.text((WIDTH // 2 - font_title.getlength(title) // 2, 120), 
              title, font=font_title, fill=(255, 255, 255))
    
    search_text = f"'{search_term}' • {len(results)} kết quả"
    draw.text((WIDTH // 2 - font_subtitle.getlength(search_text) // 2, 180), 
              search_text, font=font_subtitle, fill=(255, 200, 200))
    
    y = 280
    
    # Hiển thị kết quả
    for idx, (module_key, info) in enumerate(results[:max_results]):
        y_cmd = y + idx * result_spacing
        
        # Card kết quả với màu luân phiên
        colors = [
            (100, 200, 255, 40),
            (255, 150, 100, 40),
            (150, 255, 150, 40),
            (255, 100, 255, 40)
        ]
        card_color = colors[idx % len(colors)]
        
        card = create_glass_card((WIDTH - 100, 100), card_color)
        bg.alpha_composite(card, (50, y_cmd))
        
        # Số thứ tự
        draw.text((70, y_cmd + 30), f"{idx + 1:02d}", font=font_command, fill=(255, 255, 200))
        
        # Tên lệnh - Rút gọn nếu cần
        main_alias = info['aliases'][0] if info['aliases'] else module_key
        cmd_text = f"{PREFIX}{main_alias}"
        if len(cmd_text) > 20:
            cmd_text = cmd_text[:17] + "..."
        draw.text((120, y_cmd + 20), cmd_text, font=font_command, fill=(255, 255, 255))
        
        # Mô tả ngắn - Rút gọn hơn
        desc = str(info.get('description', ''))
        if len(desc) > 35:
            desc = desc[:32] + "..."
        draw.text((120, y_cmd + 60), desc, font=font_desc, fill=(200, 220, 255))
        
        # Quyền
        power_info = get_power_info(info.get('power', ''))
        power_text = power_info['display']
        power_width = font_info.getlength(power_text)
        draw.text((WIDTH - 80 - power_width, y_cmd + 35), power_text, 
                 font=font_info, fill=power_info['color'])
    
    # Thông báo nếu có nhiều kết quả hơn
    if len(results) > max_results:
        more_text = f"... và {len(results) - max_results} kết quả khác"
        y_more = y + max_results * result_spacing + 20
        draw.text(
            (WIDTH // 2 - font_info.getlength(more_text) // 2, y_more),
            more_text,
            font=font_info,
            fill=(255, 200, 100)
        )
    
    # Footer - Đặt ở cuối ảnh
    footer_y = HEIGHT - 100
    footer_card = create_glass_card((WIDTH, 100), (0, 0, 0, 150))
    bg.alpha_composite(footer_card, (0, footer_y))
    
    footer_text = f"💡 Chọn một lệnh để xem chi tiết: {PREFIX}help <tên lệnh>"
    draw.text(
        (WIDTH // 2 - font_info.getlength(footer_text) // 2, footer_y + 35),
        footer_text,
        font=font_info,
        fill=(150, 200, 255)
    )
    
    # Thông tin trang nếu là phân trang
    if search_term.startswith("Trang"):
        page_info = f"📄 {search_term} • Hiển thị {max_results}/{len(results)} lệnh"
        draw.text(
            (WIDTH // 2 - font_info.getlength(page_info) // 2, footer_y + 65),
            page_info,
            font=font_info,
            fill=(255, 255, 200)
        )
    
    return bg

# ================= XỬ LÝ LỆNH HELP SÁNG TẠO =================
def handle_help_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh help với phong cách mới"""
    menu_parts = message.split()
    PTA_info = get_all_PTA_with_info()
    
    if not PTA_info:
        client.replyMessage(
            Message(text="🌟 KHÔNG CÓ LỆNH NÀO!\n\nBot chưa được cài đặt module nào."),
            message_object, thread_id, thread_type, ttl=12000
        )
        return
    
    client.sendReaction(message_object, "✨", thread_id, thread_type)
    
    # Không có tham số - hiển thị dashboard
    if len(menu_parts) < 2:
        categories = categorize_commands_creative(PTA_info)
        img = draw_neon_dashboard(categories)
        temp_path = autosave(img)
        
        with Image.open(temp_path) as im:
            width, height = im.size
        
        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=180000  # 3 phút
        )
        
        info_msg = f"🚀 COMMAND DASHBOARD\n\n"
        info_msg += f"• Tổng lệnh: {len(PTA_info)}\n"
        info_msg += f"• Prefix hệ thống: {PREFIX}\n"
        info_msg += f"• Thời gian: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
        info_msg += "LỆNH ĐẶC BIỆT:\n"
        info_msg += f"• {PREFIX}menugame - 🎮 Dashboard game\n"
        info_msg += f"• {PREFIX}menu - 📱 Menu chính đầy đủ\n"
        info_msg += f"• {PREFIX}help <tên> - 🔍 Tìm kiếm lệnh\n"
        info_msg += f"• {PREFIX}help <số> - 📄 Phân trang"
        
        client.replyMessage(
            Message(text=info_msg),
            message_object, thread_id, thread_type, ttl=90000  # 1.5 phút
        )
        
        os.remove(temp_path)
        return
    
    # Xử lý tham số
    arg = menu_parts[1].strip().lower()
    
    # Kiểm tra nếu là category
    categories = categorize_commands_creative(PTA_info)
    if arg in categories:
        img = draw_neon_dashboard(categories, arg)
        temp_path = autosave(img)
        
        with Image.open(temp_path) as im:
            width, height = im.size
        
        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=150000
        )
        
        cat_info = categorize_commands_creative({}).get(arg, {})
        cat_name = cat_info.get('name', arg.upper())
        count = len(categories.get(arg, []))
        
        cat_msg = f"📊 {cat_name.upper()} CATEGORY\n\n"
        cat_msg += f"• Số lượng lệnh: {count}\n"
        cat_msg += f"• Icon: {cat_info.get('icon', '📁')}\n"
        cat_msg += f"• Danh mục: {arg}\n\n"
        cat_msg += f"💡 Dùng {PREFIX}help để quay lại dashboard chính"
        
        client.replyMessage(
            Message(text=cat_msg),
            message_object, thread_id, thread_type, ttl=60000
        )
        
        os.remove(temp_path)
        return
    
    # Phân trang
    if arg.isdigit():
        page = int(arg)
        items_per_page = 15
        total_pages = max(1, math.ceil(len(PTA_info) / items_per_page))
        
        if page < 1 or page > total_pages:
            client.replyMessage(
                Message(text=f"❌ TRANG {page} KHÔNG TỒN TẠI!\n\nTổng số trang: {total_pages}"),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        
        # Hiển thị trang đơn giản
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_commands = list(PTA_info.items())[start_idx:end_idx]
        
        # Tạo ảnh phân trang
        img = draw_search_results_neon(page_commands, f"Trang {page}")
        temp_path = autosave(img)
        
        with Image.open(temp_path) as im:
            width, height = im.size
        
        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=120000
        )
        
        page_msg = f"📄 TRANG {page}/{total_pages}\n\n"
        page_msg += f"• Hiển thị: {len(page_commands)} lệnh\n"
        page_msg += f"• Từ: {start_idx + 1} đến {min(end_idx, len(PTA_info))}\n"
        page_msg += f"• Tổng cộng: {len(PTA_info)} lệnh\n\n"
        page_msg += f"📖 Dùng {PREFIX}help <tên lệnh> để xem chi tiết"
        
        client.replyMessage(
            Message(text=page_msg),
            message_object, thread_id, thread_type, ttl=30000
        )
        
        os.remove(temp_path)
        return
    
    # Tìm kiếm
    search_term = arg
    matched_commands = {}
    
    for module_key, info in PTA_info.items():
        # Tìm kiếm toàn diện
        search_fields = [
            str(module_key).lower(),
            str(info.get('description', '')).lower(),
            get_power_info(info.get('power', ''))['display'].lower()
        ]
        
        # Thêm tất cả aliases
        search_fields.extend([str(a).lower() for a in info.get('aliases', [])])
        
        # Kiểm tra từng field
        for field in search_fields:
            if search_term in field:
                matched_commands[module_key] = info
                break
    
    if not matched_commands:
        # Gợi ý tìm kiếm
        suggestions = []
        for module_key, info in PTA_info.items():
            main_alias = info['aliases'][0] if info['aliases'] else module_key
            if len(suggestions) < 5:  # Tối đa 5 gợi ý
                suggestions.append(f"{PREFIX}{main_alias}")
        
        error_msg = f"🔍 KHÔNG TÌM THẤY LỆNH NÀO!\n\n"
        error_msg += f"Từ khóa: '{search_term}'\n\n"
        
        if suggestions:
            error_msg += "Gợi ý lệnh phổ biến:\n"
            for sug in suggestions:
                error_msg += f"• {sug}\n"
            error_msg += f"\n💡 Dùng {PREFIX}help để xem tất cả lệnh"
        
        client.replyMessage(
            Message(text=error_msg),
            message_object, thread_id, thread_type, ttl=15000
        )
        return
    
    # Nếu chỉ có 1 kết quả
    if len(matched_commands) == 1:
        module_key = list(matched_commands.keys())[0]
        info = matched_commands[module_key]
        
        img = draw_command_detail_neon(module_key, info)
        temp_path = autosave(img)
        
        with Image.open(temp_path) as im:
            width, height = im.size
        
        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=150000
        )
        
        # Thông tin text nhanh
        aliases_text = ", ".join([f"{PREFIX}{a}" for a in info['aliases'][:3]])
        if len(info['aliases']) > 3:
            aliases_text += "..."
        
        detail_msg = f"✨ CHI TIẾT LỆNH\n\n"
        detail_msg += f"• Tên: {module_key}\n"
        detail_msg += f"• Phiên bản: {info['version']}\n"
        detail_msg += f"• Quyền: {get_power_info(info['power'])['display']}\n"
        detail_msg += f"• Cách dùng: {aliases_text}\n"
        detail_msg += f"• Mô tả: {info['description'][:80]}..."
        
        client.replyMessage(
            Message(text=detail_msg),
            message_object, thread_id, thread_type, ttl=60000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(temp_path)
        return
    
    # Nhiều kết quả
    img = draw_search_results_neon(list(matched_commands.items())[:12], search_term)
    temp_path = autosave(img)
    
    with Image.open(temp_path) as im:
        width, height = im.size
    
    client.sendLocalImage(
        temp_path,
        thread_id=thread_id,
        thread_type=thread_type,
        width=width,
        height=height,
        ttl=120000
    )
    
    result_msg = f"🔍 TÌM THẤY {len(matched_commands)} KẾT QUẢ\n\n"
    result_msg += f"Từ khóa: '{search_term}'\n\n"
    
    if len(matched_commands) > 12:
        result_msg += f"📋 Đang hiển thị 12/{len(matched_commands)} kết quả\n"
        result_msg += f"💡 Dùng {PREFIX}help <tên cụ thể hơn> để lọc chính xác hơn"
    else:
        result_msg += "💡 Chọn một lệnh để xem chi tiết:\n"
        for module_key, info in list(matched_commands.items())[:5]:
            main_alias = info['aliases'][0] if info['aliases'] else module_key
            result_msg += f"• {PREFIX}help {main_alias}\n"
    
    client.replyMessage(
        Message(text=result_msg),
        message_object, thread_id, thread_type, ttl=45000
    )
    
    os.remove(temp_path)

def PTA():
    return {
        'help': handle_help_command,
        'menuhelp': handle_help_command
    }