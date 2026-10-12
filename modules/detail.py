
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import base64
import emoji
import concurrent.futures
import time
import psutil
import platform
import json
import tempfile
import sys
from zlapi.models import Message

des = {'version': "1.6.0", 'credits': "Quoc Thaizz", 'description': "Bot Detail", 'power': "User"}
start_time = time.time()
start_ram_used = psutil.virtual_memory().used
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

AUTO_APPROVE_PATH = "data/auto_approve_settings.json"
ANTIALL_PATH = "data/antiall_settings.json"
ANTIPHOTO_PATH = "data/antiphoto_settings.json"
ANTIRICON_PATH = "data/antiricon_settings.json"
ANTIFILE_PATH = "data/antifile_settings.json"
ANTIVIDEO_PATH = "data/antivideo_settings.json"
ANTISTICKER_PATH = "data/antisticker_settings.json"
AUTODOWNLOAD_PATH = "modules/cache/autodownload_groups.json"

def create_dynamic_bg_menu(W, H):
    """Tạo background gradient với blur effect"""
    base = Image.new('RGBA', (W, H), (15, 15, 20, 255))
    top = Image.new('RGBA', (W, H), (30, 30, 45, 255))
    mask = Image.new('L', (W, H))
    for x in range(W):
        for y in range(H):
            mask.putpixel((x, y), int(255 * (x / W)))
    bg = Image.composite(top, base, mask)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse([W//4-200, H//4-200, W//4+200, H//4+200], fill=(60, 60, 100, 40))
    d.ellipse([W*3//4-150, H*3//4-150, W*3//4+150, H*3//4+150], fill=(100, 60, 80, 30))
    bg = Image.alpha_composite(bg, overlay)
    bg = bg.filter(ImageFilter.GaussianBlur(50))
    return bg

def get_font(size):
    try: 
        return ImageFont.truetype(FONT_PATH, size)
    except IOError: 
        return ImageFont.load_default()

def get_emoji_font(size):
    try: 
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except IOError: 
        return get_font(size)

def calculate_text_width(text, font, emoji_font):
    return sum(emoji_font.getlength(c) if emoji.emoji_count(c) else font.getlength(c) for c in text)

def draw_rainbow_border(draw, x, y, size, width=4):
    """Vẽ viền bảy màu (rainbow) quanh avatar"""
    import math
    
    # 7 màu cầu vồng
    rainbow_colors = [
        (255, 0, 0),      # Đỏ
        (255, 127, 0),    # Cam
        (255, 255, 0),    # Vàng
        (0, 255, 0),      # Xanh lá
        (0, 0, 255),      # Xanh dương
        (75, 0, 130),     # Chàm
        (148, 0, 211)     # Tím
    ]
    
    # Vẽ nhiều vòng tròn đồng tâm với màu khác nhau
    num_layers = len(rainbow_colors)
    layer_width = width / num_layers
    
    for i, color in enumerate(rainbow_colors):
        offset = i * layer_width
        draw.ellipse(
            [x - offset, y - offset, x + size + offset, y + size + offset],
            outline=color,
            width=max(1, int(layer_width))
        )

def draw_item(draw, icon, name, enabled, position, font, emoji_font, value_font, box_size):
    """Vẽ một feature card"""
    x, y = position
    box_w, box_h = box_size
    radius = 24
    fill = (35, 35, 45, 180) 
    outline = (255, 255, 255, 40)
    draw.rounded_rectangle([x, y, x+box_w, y+box_h], radius, fill=fill, outline=outline, width=1)
    draw.line([x + 20, y + 40, x + box_w - 20, y + 40], fill=(255, 255, 255, 30), width=1)
    
    # Icon
    icon_font = emoji_font
    icon_x = x + 30
    icon_y = y + 5
    draw.text((icon_x, icon_y), icon, font=icon_font, fill=(255,255,255))
    
    # Name
    text_x = x + 30
    text_y = y + 60
    draw.text((text_x, text_y), name, font=font, fill=(255,255,255))
    
    # Status badge
    status = "ON" if enabled else "OFF"
    status_color = (0, 255, 0) if enabled else (255, 0, 0)
    badge_w = value_font.getlength(status) + 20
    draw.rounded_rectangle(
        [x + box_w - badge_w - 20, y + 60, x + box_w - 20, y + 95], 
        radius=8, 
        fill=(20, 20, 30, 230)
    )
    draw.text((x + box_w - badge_w - 10, y + 62), status, font=value_font, fill=status_color)

def fetch_image(url):
    """Download và convert image từ URL"""
    if not url: 
        return None
    try:
        if url.startswith('data:image'): 
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGB")
        response = requests.get(url, stream=True, timeout=3)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except: 
        return None

def format_time_compact(seconds):
    """Format uptime thành d h m s"""
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0: parts.append(f"{int(days)}d")
    if hours > 0: parts.append(f"{int(hours)}h")
    if minutes > 0: parts.append(f"{int(minutes)}m")
    parts.append(f"{int(seconds)}s")
    return " ".join(parts)

def detect_platform():
    """
    Phát hiện platform đang chạy
    Returns: 'android', 'termux', 'windows', 'linux', 'macos'
    """
    system = platform.system().lower()
    
    # Check Termux (Android)
    if os.path.exists('/data/data/com.termux'):
        return 'termux'
    
    # Check Android (general)
    if system == 'linux':
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                if 'android' in version:
                    return 'android'
        except:
            pass
    
    # Check Windows
    if system == 'windows':
        return 'windows'
    
    # Check macOS
    if system == 'darwin':
        return 'macos'
    
    # Default Linux
    if system == 'linux':
        return 'linux'
    
    return system

def get_os_name():
    """
    Lấy tên OS hiển thị đẹp
    """
    plat = detect_platform()
    
    if plat == 'termux':
        return 'Termux (Android)'
    elif plat == 'android':
        return 'Android'
    elif plat == 'windows':
        # Windows version
        try:
            ver = platform.version()
            if '10' in ver:
                return 'Windows 10'
            elif '11' in ver:
                return 'Windows 11'
            else:
                return f'Windows {platform.release()}'
        except:
            return 'Windows'
    elif plat == 'macos':
        try:
            ver = platform.mac_ver()[0]
            return f'macOS {ver}'
        except:
            return 'macOS'
    elif plat == 'linux':
        try:
            # Try to get Linux distro
            import distro
            return f'{distro.name()} {distro.version()}'
        except:
            return 'Linux'
    
    return platform.system()

def get_disk_usage():
    """
    Lấy disk usage cho tất cả platform
    Returns: (used_gb, total_gb) hoặc None
    """
    plat = detect_platform()
    
    try:
        if plat in ['windows']:
            # Windows: dùng C:/ drive
            disk = psutil.disk_usage('C:/')
        elif plat in ['termux', 'android']:
            # Android/Termux: thử nhiều path
            paths_to_try = [
                '/data',
                '/storage/emulated/0',
                '/sdcard',
                os.path.expanduser('~'),
                '/'
            ]
            
            disk = None
            for path in paths_to_try:
                try:
                    if os.path.exists(path):
                        disk = psutil.disk_usage(path)
                        break
                except:
                    continue
            
            if not disk:
                disk = psutil.disk_usage('/')
        else:
            # Linux/macOS: dùng root
            disk = psutil.disk_usage('/')
        
        used_gb = disk.used / (1024**3)
        total_gb = disk.total / (1024**3)
        return (used_gb, total_gb)
        
    except Exception as e:
        print(f"[ERROR] Cannot get disk usage: {e}")
        return None

def get_system_metrics():
    """
    Lấy system metrics cho tất cả platform
    """
    ram = psutil.virtual_memory()
    uptime = format_time_compact(time.time() - start_time)
    
    # CPU frequency
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq and cpu_freq.current:
            cpu = f"{cpu_freq.current:.0f}Mhz"
        else:
            cpu = "N/A"
    except:
        cpu = "N/A"
    
    # OS name
    os_name = get_os_name()
    
    # Disk usage
    disk_info = get_disk_usage()
    if disk_info:
        disk_used, disk_total = disk_info
        disk_str = f"{disk_used:.0f}/{disk_total:.0f}GB"
    else:
        disk_str = "N/A"
    
    return [
        ("🧭", "Uptime", uptime),
        ("📜", "OS", os_name),
        ("📊", "RAM", f"{ram.used/(1024**2):.0f}/{ram.total/(1024**2):.0f}MB"),
        ("💾", "Disk", disk_str),
        ("⚡", "CPU", cpu)
    ]

def process_info_image(avatar_url, author_name, features_dict):
    """Tạo image detail với tất cả thông tin"""
    features = [
        ("🚨", "Anti All", features_dict.get("antiall", False)),
        ("📁", "Anti File", features_dict.get("antifile", False)),
        ("📎", "Anti Link", features_dict.get("antilink", False)),
        ("📷", "Anti Photo", features_dict.get("antiphoto", False)),
        ("😡", "Anti rIcon", features_dict.get("antiricon", False)),
        ("🔰", "Anti Spam", features_dict.get("antispam", False)),
        ("🎨", "Anti Sticker", features_dict.get("antisticker", False)),
        ("🚫", "Anti Undo", features_dict.get("undo", False)),
        ("📹", "Anti Video", features_dict.get("antivideo", False)),
        ("👥", "Approve", features_dict.get("auto_approve", False)),
        ("📥", "Auto Download", features_dict.get("autodownload", False)),
        ("📜", "Auto Send", features_dict.get("autosend", False)),
        ("🚫", "BadWord Filter", features_dict.get("loctk", False)),
        ("🔔", "Group Event", features_dict.get("welcome", False)),
        ("💬", "Listen Group", features_dict.get("interaction", False)),
    ]
    
    metrics = get_system_metrics()
    
    W, H = 1400, 1200
    image = create_dynamic_bg_menu(W, H)
    draw = ImageDraw.Draw(image, "RGBA")
    
    # Fonts
    f_header = get_font(60)
    f_sub = get_font(24)
    f_item = get_font(28)
    f_val = get_font(22)
    f_em = get_emoji_font(32)
    f_met = get_font(18)
    
    # Header
    draw.text((60, 50), "SYSTEM CONFIGURATION", font=f_header, fill=(255, 255, 255, 255))
    
    # Avatar - ĐỔI VỊ TRÍ: từ y=50 lên y=20
    avatar_image = fetch_image(avatar_url)
    AV_SIZE = 150
    avatar_x = W - AV_SIZE - 60
    avatar_y = 20  # ✅ Lên cao hơn (từ 50 → 20)
    
    if avatar_image:
        # Tạo mask tròn
        mask = Image.new("L", (AV_SIZE, AV_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, AV_SIZE, AV_SIZE), fill=255)
        
        # Paste avatar
        image.paste(avatar_image.resize((AV_SIZE, AV_SIZE)), (avatar_x, avatar_y), mask)
        
        # ✅ VẼ VIỀN BẢY MÀU
        draw_rainbow_border(draw, avatar_x, avatar_y, AV_SIZE, width=6)
    
    draw.text((60, 130), f"OWNER: {author_name}", font=f_sub, fill=(180, 180, 180, 255))
    
    # System metrics cards
    sys_y = 200
    m_cols = 5
    m_gap = 20
    m_w = (W - 120 - (m_cols-1)*m_gap) // m_cols
    m_h = 100
    
    for i, (icon, label, val) in enumerate(metrics):
        mx = 60 + i*(m_w + m_gap)
        draw.rounded_rectangle(
            [mx, sys_y, mx+m_w, sys_y+m_h], 
            16, 
            fill=(35, 35, 45, 180), 
            outline=(255, 255, 255, 30), 
            width=1
        )
        
        # Title
        title_text = f"{icon} {label}"
        tw = f_met.getlength(title_text)
        draw.text((mx + (m_w - tw)//2, sys_y+15), title_text, font=f_met, fill=(180, 180, 180))
        
        # Value
        vw = f_val.getlength(str(val))
        draw.text((mx + (m_w - vw)//2, sys_y+55), str(val), font=f_val, fill=(255, 255, 255))

    # Feature cards
    cols = 3
    margin_x, margin_y = 60, sys_y + 130
    gap_x, gap_y = 25, 25
    card_w = (W - 2*margin_x - (cols-1)*gap_x) // cols
    card_h = 130
    
    for idx, (icon, label, status) in enumerate(features):
        c, r = idx % cols, idx // cols
        px, py = margin_x + c*(card_w + gap_x), margin_y + r*(card_h + gap_y)
        draw_item(draw, icon, label, status, (px, py), f_item, f_em, f_val, (card_w, card_h))

    # Footer
    plat_name = detect_platform().capitalize()
    footer_text = f"ZaloBot Auto | {plat_name} | My name is Hoàng Khánh Primen"
    f_footer = get_font(20)
    footer_w = f_footer.getlength(footer_text)
    draw.text(((W - footer_w) // 2, H - 50), footer_text, font=f_footer, fill=(120, 220, 255, 150))
    
    return image.convert("RGB")

def autosave(img, quality=97):
    """Lưu image vào temp file"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(
            tf, "JPEG", 
            quality=quality, 
            dpi=(180,180), 
            optimize=True, 
            progressive=True, 
            subsampling=0
        )
        return tf.name

def admin():
    """Lấy admin ID từ seting.json"""
    try:
        if os.path.exists('seting.json'):
            with open('seting.json','r') as f: 
                return json.load(f).get('account_bot')
    except: 
        return None

def handle_detail_command(message, message_object, thread_id, thread_type, author_id, client):
    """Main handler cho lệnh detail"""
    output_path = None
    try:
        settings_paths = {
            "undo": "data/undo_settings.json", 
            "loctk": "data/loctk_settings.json",
            "antispam": "data/spam_settings.json", 
            "antiricon": ANTIRICON_PATH,
            "antifile": ANTIFILE_PATH, 
            "antivideo": ANTIVIDEO_PATH,
            "antisticker": ANTISTICKER_PATH, 
            "welcome": "data/welcome_setting.json", 
            "antilink": "data/antilink_settings.json", 
            "antiphoto": "data/antiphoto_settings.json", 
            "interaction": "modules/cache/duyetboxdata.json", 
            "autosend": "modules/cache/sendtask_autosend.json",
            "autodownload": AUTODOWNLOAD_PATH
        }
        
        # Load settings
        settings = {}
        for key, path in settings_paths.items():
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding='utf-8') as f: 
                        settings[key] = json.load(f)
                except: 
                    settings[key] = {}
        
        # Parse features
        features_dict = {
            "undo": settings.get("undo",{}).get("groups",{}).get(str(thread_id),False),
            "loctk": settings.get("loctk",{}).get(str(thread_id),False),
            "antispam": settings.get("antispam",{}).get(str(thread_id),False),
            "antiricon": settings.get("antiricon",{}).get(str(thread_id),False),
            "antifile": settings.get("antifile",{}).get(str(thread_id),False),
            "antivideo": settings.get("antivideo",{}).get(str(thread_id),False),
            "antisticker": settings.get("antisticker",{}).get(str(thread_id),False),
            "welcome": str(thread_id) in settings.get("welcome",{}).get("groups",[]),
            "antilink": settings.get("antilink",{}).get(str(thread_id),False),
            "antiphoto": settings.get("antiphoto",{}).get(str(thread_id),False),
            "interaction": str(thread_id) in settings.get("interaction",[]),
            "autosend": str(thread_id) in settings.get("autosend",{}).get("groups",[]),
            "autodownload": str(thread_id) in settings.get("autodownload",{}).get("groups",[])
        }
        
        # Auto approve
        if os.path.exists(AUTO_APPROVE_PATH):
            with open(AUTO_APPROVE_PATH, "r") as f:
                try:
                    auto_approve_data = json.load(f)
                    features_dict["auto_approve"] = auto_approve_data.get(str(thread_id), False)
                except: 
                    features_dict["auto_approve"] = False
        else:
            features_dict["auto_approve"] = False
        
        # Anti all
        if os.path.exists(ANTIALL_PATH):
            with open(ANTIALL_PATH, "r") as f:
                try:
                    antiall_data = json.load(f)
                    features_dict["antiall"] = antiall_data.get(str(thread_id), False)
                except: 
                    features_dict["antiall"] = False
        else:
            features_dict["antiall"] = False

        # Get user info
        user_id_to_fetch = admin() or author_id
        user_info = client.fetchUserInfo(user_id_to_fetch)
        user_data = user_info.changed_profiles.get(str(user_id_to_fetch), {}) if user_info and hasattr(user_info, 'changed_profiles') else {}
        avatar_url = user_data.get("avatar")
        author_name = user_data.get("displayName", "Unknown")
        
        # Generate image
        image_to_save = process_info_image(avatar_url, author_name, features_dict)
        
        # Save and send
        output_path = autosave(image_to_save)
        if os.path.exists(output_path):
            with Image.open(output_path) as im: 
                width, height = im.size
            client.sendLocalImage(
                output_path, 
                thread_id=thread_id, 
                thread_type=thread_type, 
                width=width, 
                height=height, 
                ttl=120000
            )
    except Exception as e:
        client.sendMessage(
            Message(text=f"• An error occurred: {str(e)}"), 
            thread_id, 
            thread_type, 
            ttl=60000
        )
    finally:
        if output_path and os.path.exists(output_path): 
            os.remove(output_path)

def PTA():
    return {'detail': handle_detail_command}