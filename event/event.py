import os
import re
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageChops
import requests
from datetime import datetime
import concurrent.futures
import json
from zlapi.models import *

C1, C2, C3, RESET = "\033[38;2;0;255;204m", "\033[38;2;0;255;149m", "\033[38;2;255;51;102m", "\033[0m"

des = {
    'version': "1.4.0", 
    'credits': "Van Chien", 
    'description': "Event image Emoji support", 
    'power': "Thành viên"
}

CACHE = "modules/cache"
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CJK_FONT_PATH = "modules/cache/font/Noto Sans CJK Regular.otf"
EVENT_SETTINGS_FILE = "data/welcome_setting.json"
LINK_BACKGROUND_DEFAULT = "https://photo-stal-7.zdn.vn/gr/jpg/44d0be0596b458ea01a5/1538102626601520187.jpg"
LINK_BACKGROUND_DEFAULT_ZALO = "https://cover-talk.zadn.vn/default"

def get_font_for_char(char, font, emoji_font, cjk_font):
    """Hàm tự động nhận diện ký tự để chọn đúng Font (Emoji, CJK, hoặc mặc định)"""
    try:
        import emoji as emoji_mod
        if emoji_mod.emoji_count(char):
            return emoji_font
    except ImportError:
        if re.match(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', char):
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

def get_font(path, size, is_emoji=False):
    """Hàm load font hỗ trợ Emoji"""
    try:
        if os.path.exists(path):
            if is_emoji:
                try:
                    return ImageFont.truetype(path, size, embedded_color=True)
                except Exception:
                    pass
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    return ImageFont.load_default()

def load_allowed_groups():
    if os.path.exists(EVENT_SETTINGS_FILE):
        try:
            with open(EVENT_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("groups", [])
        except:
            pass
    return []

def hex_to_rgba(hex_color, alpha=255):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, alpha)
    return (255, 255, 255, alpha)

def create_gradient_image(width, height, stops, horizontal=True):
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

def draw_mixed_text(draw, text, x, y, font_text, font_emoji, font_cjk, fill):
    """Hàm tự động vẽ Text xen kẽ Emoji và CJK căn giữa (render từng ký tự)"""
    total_width = 0
    for char in text:
        font_to_use = get_font_for_char(char, font_text, font_emoji, font_cjk)
        bbox = draw.textbbox((0, 0), char, font=font_to_use)
        total_width += (bbox[2] - bbox[0])
        
    current_x = x - (total_width / 2)
    
    for char in text:
        font_to_use = get_font_for_char(char, font_text, font_emoji, font_cjk)
        is_emoji = (font_to_use == font_emoji)
        draw.text((current_x, y), char, font=font_to_use, fill=fill, anchor="lm", embedded_color=is_emoji)
        bbox = draw.textbbox((0, 0), char, font=font_to_use)
        current_x += (bbox[2] - bbox[0])

def draw_text_with_gradient(canvas, text, font, x, y, colors):
    if not colors: 
        colors = ["#FFFFFF"]
        
    try:
        font_size = font.size
    except:
        font_size = 36
        
    font_emoji = get_font(EMOJI_FONT_PATH, font_size, is_emoji=True)
    font_cjk = get_font(CJK_FONT_PATH, font_size)
        
    if len(colors) == 1:
        draw = ImageDraw.Draw(canvas)
        draw_mixed_text(draw, text, x, y, font, font_emoji, font_cjk, hex_to_rgba(colors[0]))
        return

    grad_width = 800
    grad_height = 100
    colors_rgba = [hex_to_rgba(c) for c in colors]
    stops = [(i / max(1, len(colors_rgba) - 1), c) for i, c in enumerate(colors_rgba)]
    
    grad_img = create_gradient_image(grad_width, grad_height, stops, horizontal=True)
    
    temp_canvas = Image.new("RGBA", (grad_width, grad_height), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_canvas)
    
    draw_mixed_text(temp_draw, text, grad_width // 2, grad_height // 2, font, font_emoji, font_cjk, (255, 255, 255, 255))
    
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
    # Đã bổ sung lại add_admin và remove_admin vào map này, mắt trố ra mà xem
    type_map = {
        "welcome": 0, "add_admin": 0, 
        "goodbye": 1, "remove_admin": 1, 
        "kicked": 2, "blocked": 2, 
        "blocked_spam": 2, "blocked_spam_link": 2
    }
    typeImage = type_map.get(file_type, 3)
        
    background = get_link_background_default(userInfo.get('cover'))
    width, height = 1000, 300 
    background = background.resize((width, height), Image.Resampling.LANCZOS)
    canvas = background.copy()

    # Tạo kính đen sắc nét, đập bỏ cái kính mờ (gradient) lởm khởm kia đi!
    # Lớp overlay đen trong suốt với alpha=140 để ảnh nền rõ rệt.
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 140))
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

def process_group_event_image(self, member_id, message_info, groupId, event_time, filename, file_type):
    op = None
    try:
        u = self.fetchUserInfo(member_id) or {}
        ud = {}
        if isinstance(u, dict):
            ud = u.get(member_id, u.get('changed_profiles', {}).get(member_id, {}))
            if not ud and ('avatar' in u or 'avt' in u):
                ud = u
                
        userInfo = {
            'avatar': ud.get('avatar') or ud.get('avt') or "",
            'cover': ud.get('cover') or "",
            'name': ud.get('zaloName') or ud.get('displayName') or ud.get('dpn') or message_info.get('fallbackName', 'không xác định')
        }
        
        image = create_event_image(userInfo, message_info, file_type)
        
        if not os.path.exists(CACHE):
            os.makedirs(CACHE)
            
        op = os.path.join(CACHE, filename)
        image.save(op, format="PNG", quality=100)
        
        # Cái này đang chỉ gửi ảnh trơn, không có thông báo văn bản tag tiếc rườm rà
        self.sendLocalImage(
            op, 
            thread_id=groupId, 
            thread_type=ThreadType.GROUP, 
            width=image.width, 
            height=image.height,
            ttl=320000
        )
    except Exception as e:
        print(f"Error processing group event image: {e}")
    finally:
        if op and os.path.exists(op):
            os.remove(op)

        try:
            event_names = {
                "welcome": "THÀNH VIÊN MỚI", "goodbye": "RỜI NHÓM", "kicked": "SÚT TV",
                "add_admin": "THÊM ADMIN (KEY BẠC)", "remove_admin": "GỠ ADMIN (KEY BẠC)"
            }
            display_name = event_names.get(file_type, file_type.upper())
            g_info = getattr(self, 'group_info_cache', {}).get(groupId) or self.fetchGroupInfo(groupId).gridInfoMap.get(groupId, {})
            print(f"{C1}┌── {C2}[ {display_name} ]{C1} ──────────────────────┐")
            print(f"{C1}│ {C2}Nhóm: {RESET}{g_info.get('name', 'Nhóm ẩn')}")
            print(f"{C1}│ {C2}User: {RESET}{userInfo.get('name', 'Thành viên')}")
            print(f"{C1}└────────────────────────────────────────────┘{RESET}")
        except: pass

def handleGroupEvent(self, eventData, eventType):
    groupId = eventData.get('groupId')
    if not groupId: return
    
    allowed_groups = load_allowed_groups()
    if groupId not in allowed_groups: return
    
    try:
        group_type_val = self.fetchGroupInfo(groupId).gridInfoMap[groupId].type
        group_type_name = "Cộng Đồng" if group_type_val == 2 else "Nhóm"
    except:
        group_type_name = "Nhóm"
        
    groupName = eventData.get('groupName', "Group")
    
    if eventType == GroupEventType.JOIN:
        joinMembers = eventData.get('updateMembers', [])
        sourceId = eventData.get("sourceId")
        event_time = datetime.now()
        
        adder_name = ""
        if sourceId:
            adder_info = self.fetchUserInfo(sourceId) or {}
            if isinstance(adder_info, dict):
                ad = adder_info.get(sourceId, adder_info.get('changed_profiles', {}).get(sourceId, {}))
                adder_name = ad.get('displayName') or ad.get('zaloName') or ""

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for member in joinMembers:
                member_id = member.get('id')
                user_name = member.get('dName', '')
                
                if not adder_name or sourceId == member_id:
                    author_text = "Tham gia trực tiếp hoặc được mời"
                else:
                    author_text = f"Duyệt bởi {adder_name}"
                    
                message_info = {
                    'title': groupName,
                    'userName': f"Chào mừng {user_name}",
                    'subtitle': f"Đã tham gia {group_type_name}",
                    'author': author_text,
                    'fallbackName': user_name
                }
                
                filename = f"welcome_{event_time.timestamp()}.png"
                executor.submit(process_group_event_image, self, member_id, message_info, groupId, event_time, filename, "welcome")
                
    elif eventType in {GroupEventType.LEAVE, GroupEventType.REMOVE_MEMBER}:
        updateMembers = eventData.get('updateMembers', [])
        sourceId = eventData.get("sourceId")
        event_time = datetime.now()
        
        remover_name = "Ai Đó"
        if sourceId:
            remover_info = self.fetchUserInfo(sourceId) or {}
            if isinstance(remover_info, dict):
                rd = remover_info.get(sourceId, remover_info.get('changed_profiles', {}).get(sourceId, {}))
                remover_name = rd.get('displayName') or rd.get('zaloName') or "Ai Đó"

            with concurrent.futures.ThreadPoolExecutor() as executor:
                for member in updateMembers:
                    member_id = member.get('id')
                    user_name = member.get('dName', '')
                    
                    if eventType == GroupEventType.LEAVE:
                        file_type = "goodbye"
                        message_info = {
                            'title': "Member Left The Group",
                            'userName': user_name,
                            'subtitle': f"Vừa rời khỏi {group_type_name}",
                            'author': groupName,
                            'fallbackName': user_name
                        }
                    else:
                        file_type = "kicked"
                        message_info = {
                            'title': "Kicked Out Member",
                            'userName': f"Thằng Oắt Con {user_name}",
                            'subtitle': f"Đã Bị {remover_name} Sút Khỏi {group_type_name}",
                            'author': groupName,
                            'fallbackName': user_name
                        }
                        
                    filename = f"{file_type}_{event_time.timestamp()}.png"
                    executor.submit(process_group_event_image, self, member_id, message_info, groupId, event_time, filename, file_type)
                    
    elif eventType == GroupEventType.ADD_ADMIN:
        updateMembers = eventData.get('updateMembers', [])
        sourceId = eventData.get("sourceId")
        event_time = datetime.now()
        ow_name = "Ai Đó"
        if sourceId:
            ow_info = self.fetchUserInfo(sourceId) or {}
            if isinstance(ow_info, dict):
                od = ow_info.get(sourceId, ow_info.get('changed_profiles', {}).get(sourceId, {}))
                ow_name = od.get('displayName') or od.get('zaloName') or "Ai Đó"

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for member in updateMembers:
                member_id = member.get('id')
                user_name = member.get('dName', '')
                message_info = {
                    'title': groupName,
                    'userName': f"Đại Ca {user_name}",
                    'subtitle': "Vừa Trở Thành Quản Trị Viên",
                    'author': f"Bổ nhiệm bởi {ow_name}",
                    'fallbackName': user_name
                }
                filename = f"add_admin_{event_time.timestamp()}.png"
                executor.submit(process_group_event_image, self, member_id, message_info, groupId, event_time, filename, "add_admin")

    elif eventType == GroupEventType.REMOVE_ADMIN:
        updateMembers = eventData.get('updateMembers', [])
        sourceId = eventData.get("sourceId")
        event_time = datetime.now()
        ow_name = "Ai Đó"
        if sourceId:
            ow_info = self.fetchUserInfo(sourceId) or {}
            if isinstance(ow_info, dict):
                od = ow_info.get(sourceId, ow_info.get('changed_profiles', {}).get(sourceId, {}))
                ow_name = od.get('displayName') or od.get('zaloName') or "Ai Đó"

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for member in updateMembers:
                member_id = member.get('id')
                user_name = member.get('dName', '')
                message_info = {
                    'title': "Removed Admin",
                    'userName': user_name,
                    'subtitle': "Mất Quyền Quản Trị Viên",
                    'author': f"Bởi {ow_name}",
                    'fallbackName': user_name
                }
                filename = f"remove_admin_{event_time.timestamp()}.png"
                executor.submit(process_group_event_image, self, member_id, message_info, groupId, event_time, filename, "remove_admin")

def PTA():
    return {}