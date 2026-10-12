import os
import math
import time
import uuid
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import *
from config import ADMIN

des = {
    'version': "2.0.1",
    'credits': "hi",
    'description': "Xem danh sách bạn bè.",
    'power': "Quản Trị Bot"
}

# ===== CONFIG =====
FONT_PATH = "modules/cache/font/"
BOLD_FONT = FONT_PATH + "BeVietnamPro-Bold.ttf"
MED_FONT = FONT_PATH + "BeVietnamPro-Medium.ttf"
SEMI_FONT = FONT_PATH + "BeVietnamPro-SemiBold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

WIDTH = 1000
ITEM_PER_PAGE = 15
LINE_HEIGHT = 110
AVATAR_SIZE = 70

# ===== COLOR =====
COLOR_BG = (4, 15, 34)
COLOR_BOX = (10, 28, 55)
COLOR_CYAN = (0, 255, 255)
COLOR_YELLOW = (255, 204, 0)
COLOR_WhiTE = (255, 255, 255)
COLOR_GREY = (170, 170, 170)
COLOR_ONLINE = (0, 255, 120)

# ===== FONT LOAD =====
def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# ===== TEXT GLOW =====
def draw_glow_text(draw, pos, text, font, main_color, glow_color):
    x, y = pos

    # glow layer
    for offset in range(1, 4):
        draw.text((x-offset, y), text, font=font, fill=glow_color)
        draw.text((x+offset, y), text, font=font, fill=glow_color)
        draw.text((x, y-offset), text, font=font, fill=glow_color)
        draw.text((x, y+offset), text, font=font, fill=glow_color)

    # main text
    draw.text((x, y), text, font=font, fill=main_color)

# ===== AVATAR =====
def get_avatar(client, uid, size=AVATAR_SIZE):
    try:
        info = client.fetchUserInfo(uid)
        avatar_url = ""

        if hasattr(info, "changed_profiles") and uid in info.changed_profiles:
            avatar_url = info.changed_profiles[uid].avatar
        elif isinstance(info, dict) and uid in info:
            avatar_url = info[uid].get("avatar")

        if not avatar_url:
            raise Exception("no avatar")

        res = requests.get(avatar_url, timeout=5)
        img = Image.open(BytesIO(res.content)).convert("RGBA")
        img = img.resize((size, size))

        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

        out = Image.new("RGBA", (size, size))
        out.paste(img, (0, 0), mask)

        return out

    except:
        fallback = Image.new("RGBA", (size, size), (80, 80, 80))
        return fallback

# ===== RENDER =====
def render_friend_list(client, friends, page, total, author_id):
    total_pages = max(1, math.ceil(total / ITEM_PER_PAGE))
    data = friends[(page - 1) * ITEM_PER_PAGE: page * ITEM_PER_PAGE]

    header_h = 240
    body_h = len(data) * LINE_HEIGHT
    footer_h = 40
    canvas_h = header_h + body_h + footer_h

    img = Image.new("RGB", (WIDTH, canvas_h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # FONT
    title_f = get_font(BOLD_FONT, 55)
    sub_f = get_font(SEMI_FONT, 34)
    info_f = get_font(MED_FONT, 24)
    name_f = get_font(SEMI_FONT, 28)
    uid_f = get_font(MED_FONT, 20)

    # ===== HEADER =====
    author_avatar = get_avatar(client, author_id, 120)
    img.paste(author_avatar, (50, 40), author_avatar)

    author_name = "hi Dz"
    try:
        info = client.fetchUserInfo(author_id)
        if isinstance(info, dict) and author_id in info:
            author_name = info[author_id].get("displayName", author_name)
    except:
        pass

    draw_glow_text(draw, (190, 45), author_name, title_f, COLOR_WhiTE, COLOR_CYAN)
    draw_glow_text(draw, (190, 105), "DANH SÁCH BẠN BÈ", sub_f, COLOR_YELLOW, COLOR_YELLOW)

    draw.text(
        (190, 150),
        f"{total} bạn bè  •  Trang {page}/{total_pages}",
        font=info_f,
        fill=COLOR_WhiTE
    )

    draw.line((50, 200, WIDTH - 50, 200), fill=COLOR_CYAN, width=3)

    # ===== BODY =====
    y = 220
    start = (page - 1) * ITEM_PER_PAGE + 1

    for i, f in enumerate(data, start=start):
        # box glow
        draw.rounded_rectangle((50, y, WIDTH - 50, y + 90), 20, fill=COLOR_BOX)

        # viền neon
        draw.rounded_rectangle((50, y, WIDTH - 50, y + 90), 20, outline=COLOR_CYAN, width=2)

        # index
        draw.text((70, y + 28), str(i), font=name_f, fill=COLOR_CYAN)

        # avatar
        ava = get_avatar(client, f["uid"])
        img.paste(ava, (120, y + 10), ava)

        # name
        draw.text((210, y + 15), f["name"], font=name_f, fill=COLOR_WhiTE)

        # uid
        draw.text((210, y + 55), f"UID: {f['uid']}", font=uid_f, fill=COLOR_GREY)

        # online dot
        draw.ellipse((WIDTH - 90, y + 35, WIDTH - 70, y + 55), fill=COLOR_ONLINE)

        y += LINE_HEIGHT

    # ===== FOOTER =====
    footer = f"/listbb {max(1,page-1)}   •   Trang {page}/{total_pages}   •   /listbb {min(total_pages,page+1)}"
    draw.text((260, y + 10), footer, font=info_f, fill=COLOR_YELLOW)

    path = f"listbb_{uuid.uuid4().hex}.png"
    img.save(path)
    return path

# ===== MAIN =====
def handle_list_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # ===== CHECK ADMIN =====
        if author_id != ADMIN:
            client.sendMessage(
                Message(text="❌ Lệnh này chỉ dành cho admin!"),
                thread_id,
                thread_type
            )
            return

        # ===== LOGIC CŨ GIỮ NGUYÊN =====
        args = message.split() if message else []
        page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

        data = client.fetchAllFriends()
        if not data:
            client.sendMessage(Message(text="❌ Không có data"), thread_id, thread_type)
            return

        friends = []
        for u in data:
            uid = getattr(u, "userId", None) or u.get("userId")
            name = getattr(u, "displayName", None) or u.get("displayName")

            friends.append({
                "uid": uid,
                "name": name
            })

        total = len(friends)

        path = render_friend_list(client, friends, page, total, author_id)

        img = Image.open(path)
        w, h = img.size

        client.sendLocalImage(path, thread_id, thread_type, width=w, height=h)

        time.sleep(2)
        if os.path.exists(path):
            os.remove(path)

    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi: {str(e)}"), thread_id, thread_type)
# ===== REGISTER =====
def PTA():
    return {
        "listbb": handle_list_command
    }