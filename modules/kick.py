import json
import os
import requests
import tempfile
import random
from io import BytesIO
from datetime import datetime

# Import đầy đủ các model cần thiết từ zlapi giống PTA.py
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
from config import ADMIN, PREFIX, HEADER_STYLE
from PIL import Image, ImageDraw, ImageFont, ImageChops

# Thêm try-except để import pilmoji an toàn cho phần vẽ emoji gradient
try:
    from pilmoji import Pilmoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False
    print("CẢNH BÁO: Chưa cài đặt thư viện 'pilmoji'. Hãy chạy lệnh 'pip install pilmoji' để hiển thị được emoji.")

with open('seting.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

ADMIN_ID = settings.get('admin')
ADM_IDS = settings.get('adm', [])

des = {
    'version': "1.1.0",
    'credits': "Van Chien",
    'description': "Block thành viên trong nhóm",
    'power': "Quản trị viên Bot",
    'reaction': False
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
LINK_BACKGROUND_DEFAULT = "https://photo-stal-7.zdn.vn/gr/jpg/573676224e488016d959/1486149405335369099.jpg"
LINK_BACKGROUND_DEFAULT_ZALO = "https://cover-talk.zadn.vn/default"

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

# ---------------- KIỂM TRA QUYỀN MỚI ----------------
def check_admin_permissions(author_id, thread_id, thread_type, client):
    author_id = str(author_id)
    
    if hasattr(client, 'is_allowed_author') and client.is_allowed_author(author_id):
        return True

    try:
        with open('seting.json', 'r', encoding='utf-8') as f:
            current_settings = json.load(f)
        admin_id = str(current_settings.get('admin', ''))
        adm_list = [str(uid) for uid in current_settings.get('adm', [])]
        
        if author_id == admin_id or author_id in adm_list:
            return True
    except Exception:
        pass

    if author_id in ADMIN:
        return True
        
    return False


# ---------------- CÁC HÀM VẼ ẢNH EVENT KHI KICK THÀNH CÔNG ----------------
def hex_to_rgba(hex_color, alpha=255):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, alpha)
    return (255, 255, 255, alpha)

def create_gradient_image(width, height, stops, horizontal=False):
    stops = sorted(stops, key=lambda x: x[0])
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    def get_color(ratio):
        if ratio <= stops[0][0]: return stops[0][1]
        if ratio >= stops[-1][0]: return stops[-1][1]
        for i in range(len(stops) - 1):
            r1, c1 = stops[i]
            r2, c2 = stops[i+1]
            if r1 <= ratio <= r2:
                range_ratio = (ratio - r1) / (r2 - r1)
                r = int(c1[0] + (c2[0] - c1[0]) * range_ratio)
                g = int(c1[1] + (c2[1] - c1[1]) * range_ratio)
                b = int(c1[2] + (c2[2] - c1[2]) * range_ratio)
                a = int(c1[3] + (c2[3] - c1[3]) * range_ratio)
                return (r, g, b, a)
        return stops[-1][1]

    if horizontal:
        for x in range(width):
            color = get_color(x / width)
            draw.line([(x, 0), (x, height)], fill=color)
    else:
        for y in range(height):
            color = get_color(y / height)
            draw.line([(0, y), (width, y)], fill=color)
    return img

def draw_text_with_gradient(canvas, text, font, x, y, colors):
    if not colors: 
        colors = ["#FFFFFF"]
        
    if len(colors) == 1:
        if HAS_PILMOJI:
            with Pilmoji(canvas) as pilmoji:
                pilmoji.text((x, y), text, font=font, fill=hex_to_rgba(colors[0]), anchor="mm")
        else:
            draw = ImageDraw.Draw(canvas)
            draw.text((x, y), text, font=font, fill=hex_to_rgba(colors[0]), anchor="mm")
        return

    grad_width = 800
    grad_height = 100
    colors_rgba = [hex_to_rgba(c) for c in colors]
    stops = [(i / max(1, len(colors_rgba) - 1), c) for i, c in enumerate(colors_rgba)]
    
    grad_img = create_gradient_image(grad_width, grad_height, stops, horizontal=True)
    
    temp_canvas = Image.new("RGBA", (grad_width, grad_height), (0, 0, 0, 0))
    if HAS_PILMOJI:
        with Pilmoji(temp_canvas) as pilmoji:
            pilmoji.text((grad_width // 2, grad_height // 2), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    else:
        temp_draw = ImageDraw.Draw(temp_canvas)
        temp_draw.text((grad_width // 2, grad_height // 2), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    
    mask = temp_canvas.split()[3]
    paste_x = int(x - grad_width // 2)
    paste_y = int(y - grad_height // 2)
    
    canvas.paste(grad_img, (paste_x, paste_y), mask)

def get_link_background_default(cover_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    if cover_url and cover_url != LINK_BACKGROUND_DEFAULT_ZALO:
        try:
            r = requests.get(cover_url, headers=headers, timeout=5)
            if r.status_code == 200:
                return Image.open(BytesIO(r.content)).convert("RGBA")
        except Exception as e:
            print(f"Lỗi tải cover: {e}")
    
    try:
        r = requests.get(LINK_BACKGROUND_DEFAULT, headers=headers, timeout=5)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"Lỗi tải background mặc định: {e}")
        
    return Image.new("RGBA", (1000, 300), (30, 30, 53, 255))

def create_event_image(userInfo, message_info, file_type):
    type_map = {"welcome": 0, "goodbye": 1, "kicked": 2, "blocked": 2, "blocked_spam": 2, "blocked_spam_link": 2}
    typeImage = type_map.get(file_type, 3)
    
    if typeImage in [0, 1]:
        fluent = 0.35 
    elif typeImage == 2:
        fluent = 0.85
    else:
        fluent = 0.8
        
    background = get_link_background_default(userInfo.get('cover'))
    width, height = 1000, 300 
    background = background.resize((width, height), Image.Resampling.LANCZOS)
    canvas = background.copy()

    overlay_stops = [
        (0.0, (30, 30, 53, int(255 * fluent))),
        (0.5, (26, 37, 71, int(255 * fluent))),
        (1.0, (19, 27, 54, int(255 * fluent)))
    ]
    overlay = create_gradient_image(width, height, overlay_stops, horizontal=False)
    canvas.paste(overlay, (0, 0), overlay)

    xAvatar = 118
    widthAvatar = 162
    heightAvatar = 162
    yAvatar = height // 2 - heightAvatar // 2
    borderWidth = 6

    if typeImage == 0:
        gradientColors = ["#00FF80", "#00FF80"] 
    elif typeImage == 1:
        gradientColors = ["#FFFFFF", "#F0F0F0", "#FAFAFF", "#F8FBFF", "#EAEAFF", "#FFF5FA", "#FFFFFF"]
    elif typeImage == 2:
        gradientColors = ["#ff0000", "#ff1111", "#ff2200", "#ff0022", "#ff3300"]
    else:
        gradientColors = ["#FF1493", "#FF69B4", "#FFD700", "#FFA500", "#FF8C00", "#00FF7F", "#40E0D0"]
    
    shuffledColors = gradientColors.copy()
    if typeImage != 0:
        random.shuffle(shuffledColors)

    avatar_url = userInfo.get("avatar")
    if avatar_url:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(avatar_url, headers=headers, timeout=5)
            if r.status_code == 200:
                avatar_img = Image.open(BytesIO(r.content)).convert("RGBA")
                avatar_img = avatar_img.resize((widthAvatar, heightAvatar), Image.Resampling.LANCZOS)
                
                border_stops = [(i / max(1, len(shuffledColors) - 1), hex_to_rgba(c)) for i, c in enumerate(shuffledColors)]
                border_size = widthAvatar + 2 * borderWidth
                border_bg = create_gradient_image(border_size, border_size, border_stops, horizontal=True)
                
                border_mask = Image.new("L", (border_size, border_size), 0)
                ImageDraw.Draw(border_mask).ellipse((0, 0, border_size, border_size), fill=255)
                border_bg.putalpha(border_mask)
                canvas.paste(border_bg, (int(xAvatar - border_size / 2), int(height / 2 - border_size / 2)), border_bg)
                
                av_mask = Image.new("L", (widthAvatar, heightAvatar), 0)
                ImageDraw.Draw(av_mask).ellipse((0, 0, widthAvatar, heightAvatar), fill=255)
                canvas.paste(avatar_img, (int(xAvatar - widthAvatar / 2), int(yAvatar)), av_mask)
                
                draw = ImageDraw.Draw(canvas)
                line_x = xAvatar + widthAvatar // 2 + borderWidth + 30
                draw.line([(line_x, yAvatar + 30), (line_x, yAvatar + heightAvatar - 30)], fill="white", width=3)
        except Exception as e:
            print("Lỗi load avatar:", e)

    x1 = xAvatar - widthAvatar // 2 + widthAvatar
    x2 = int(x1 + (width - x1) / 2 - 5)
    
    try:
        font36 = ImageFont.truetype(FONT_PATH, 36)
        font32 = ImageFont.truetype(FONT_PATH, 32)
    except:
        font36 = ImageFont.load_default()
        font32 = ImageFont.load_default()

    main_color = [shuffledColors[0]]

    draw_text_with_gradient(canvas, message_info['title'], font36, x2, 86, main_color)
    draw_text_with_gradient(canvas, message_info['userName'], font36, x2, 136, main_color)
    draw_text_with_gradient(canvas, message_info['subtitle'], font32, x2, 181, main_color)
    draw_text_with_gradient(canvas, message_info['author'], font32, x2, 226, main_color)

    return canvas


# --- HÀM LẤY TÊN VÀ GỬI TIN NHẮN TÙY CHỈNH THEO CHUẨN PTA.py ---

def get_username(client, user_id):
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, "changed_profiles"):
            return info.changed_profiles.get(str(user_id), {}).get('zaloName', 'Không xác định')
        if isinstance(info, dict):
             return info.get(str(user_id), {}).get('zaloName', 'Không xác định')
        return "Không xác định"
    except Exception:
        return "Không xác định"

def send_custom_reply(client, message_text, message_object, thread_id, thread_type, author_id, ttl=12000):
    if thread_type == ThreadType.USER:
        full_msg = f"{HEADER_STYLE}\n{message_text}"
        mention = None
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
            MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
        ])
    else:
        name = get_username(client, author_id)
        tag_text = f"@{name}"
        full_msg = f"{tag_text}\n{HEADER_STYLE}\n{message_text}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))
        styles = MultiMsgStyle([
            MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="bold", auto_format=False),
            MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
        ])
    
    client.replyMessage(
        Message(text=full_msg, style=styles, mention=mention),
        message_object, 
        thread_id=thread_id, 
        thread_type=thread_type, 
        ttl=ttl
    )

# -------------------------------------------------------------

def handle_ban_command(message, message_object, thread_id, thread_type, author_id, client):
    # Sử dụng hàm check quyền
    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        send_custom_reply(client, "Bạn không có đủ quyền để sử dụng lệnh này\nYêu cầu quyền hạn: Quản Trị Bot\n🚫🚫🚫", message_object, thread_id, thread_type, author_id)
        return

    command_parts = message.strip().split()
    user_ids_to_ban = []
    
    if message_object.mentions:
        user_ids_to_ban.extend([str(mention.uid) for mention in message_object.mentions])
    elif message_object.quote:
        user_ids_to_ban.append(str(message_object.quote.ownerId))

    # Đã thay thế ảnh hướng dẫn bằng thông báo văn bản khi không chỉ định ai cần block
    if not user_ids_to_ban or (len(command_parts) > 1 and command_parts[1].lower() == "help"):
        send_custom_reply(client, ":d Đại ca muốn kick ai?", message_object, thread_id, thread_type, author_id)
        return

    group_data = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admins = group_data.adminIds
    owners = group_data.creatorId
    groupName = group_data.name or "Nhóm"
    
    try:
        group_type_val = group_data.type
        group_type_name = "Cộng Đồng" if group_type_val == 2 else "Nhóm"
    except:
        group_type_name = "Nhóm"

    if client.uid not in admins and client.uid != owners:
        send_custom_reply(client, "Đưa Key Vàng 🔑, Em Kick Cho Đại Ca Xem :D", message_object, thread_id, thread_type, author_id)
        return

    admin_name = "Quản trị viên"
    try:
        admin_info = client.fetchUserInfo(author_id) or {}
        if isinstance(admin_info, dict):
            ad = admin_info.get(str(author_id), admin_info.get('changed_profiles', {}).get(str(author_id), {}))
            admin_name = ad.get('zaloName') or ad.get('displayName') or ad.get('name') or "Quản trị viên"
    except:
        pass

    success = []
    fail = []

    for user_id in user_ids_to_ban:
        if user_id == ADMIN_ID:
            fail.append(f"Không thể block admin chính.")
            continue
        if user_id in ADM_IDS and str(author_id) != ADMIN_ID:
            fail.append(f"Đại Ca Không thể bảo em kick quản trị bot được 🚀.")
            continue
        if user_id == owners:
            fail.append(f"Không thể block chủ nhóm.")
            continue
        if user_id in admins and str(author_id) != owners:
            fail.append(f":d không có quyền block trưởng nhóm.")
            continue

        try:
            client.blockUsersInGroup(user_id, thread_id)
            success.append(user_id)
        except Exception as e:
            fail.append(f"Lỗi khi block {user_id}: {str(e)}")

    for user_id in success:
        # Lấy thông tin user bị kick để render ảnh
        u = client.fetchUserInfo(user_id) or {}
        ud = {}
        if isinstance(u, dict):
            ud = u.get(user_id, u.get('changed_profiles', {}).get(user_id, {}))
            if not ud and ('avatar' in u or 'avt' in u):
                ud = u
                
        user_name = ud.get('zaloName') or ud.get('displayName') or ud.get('dpn') or str(user_id)
        
        userInfo = {
            'avatar': ud.get('avatar') or ud.get('avt') or "",
            'cover': ud.get('cover') or "",
            'name': user_name
        }

        message_info = {
            'title': "Kicked Out Member",
            'userName': f"Thằng Oắt Con {user_name}",
            'subtitle': f"Đã Bị {admin_name} Sút Khỏi {group_type_name}",
            'author': groupName,
            'fallbackName': user_name
        }
        
        # Gọi hàm tạo ảnh từ event
        canvas = create_event_image(userInfo, message_info, "kicked")
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            temp_path = tf.name
            canvas.save(temp_path, format="PNG", quality=100)
            
        with Image.open(temp_path) as im:
            w, h = im.size
        
        client.sendLocalImage(temp_path, thread_id=thread_id, thread_type=thread_type, width=w, height=h, ttl=320000)
        os.remove(temp_path)

    if fail:
        send_custom_reply(client, "\n".join(fail), message_object, thread_id, thread_type, author_id)

def PTA():
    return {
        'ban': handle_ban_command,
        'cut': handle_ban_command,
        'bien': handle_ban_command,
        'kick': handle_ban_command,
        'sut': handle_ban_command
    }