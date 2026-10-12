import os
import math
import importlib
import tempfile
from io import BytesIO
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from zlapi.models import Message

# =========================
# CẤU HÌNH
# =========================
FONT_CANDIDATES = [
    "BeVietnamPro-Bold.ttf",
    "BeVietnamPro-SemiBold.ttf",
    "modules/cache/font/BeVietnamPro-Bold.ttf",
    "modules/cache/font/BeVietnamPro-SemiBold.ttf",
]
AVATAR_FALLBACK = ".gio.jpg"
CACHE_DIR = "modules/cache/menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

PAGE_SIZE = 12

DESIGN = {
    "bg": (8, 4, 28, 255),
    "panel": (22, 8, 46, 232),
    "panel_soft": (30, 12, 58, 222),
    "line_pink": (255, 0, 170, 255),
    "line_cyan": (0, 210, 255, 255),
    "text": (245, 245, 255, 255),
    "text_soft": (189, 186, 223, 255),
    "badge_admin": (173, 46, 110, 255),
    "badge_user": (34, 101, 217, 255),
    "dot_on": (252, 74, 105, 255),
}

GROUP_STATUS_ITEMS = [
    "Anti Undo", "Anti Link", "Anti Sticker", "Anti Video",
    "Phê Duyệt", "Sự Kiện", "Anti Forward", "Anti Spam",
    "Anti Photo", "Anti File", "Anti Icon", "Anti Bot",
    "Tương Tác", "Anti Nude",
]

des = {
    "version": "5.0.0",
    "credits": "XTHAI X ADR",
    "description": "Menu ảnh giao diện neon 2 cột như mẫu.",
    "power": "Thành viên"
}


# =========================
# FONT / ẢNH / TIỆN ÍCH
# =========================
def _font_path():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def get_font(size: int):
    font_path = _font_path()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def load_image_from_url(url: str, timeout: int = 10):
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGBA")


def load_avatar(avatar_url: str | None = None, size: int = 220):
    img = None
    if avatar_url:
        try:
            img = load_image_from_url(avatar_url, timeout=8)
        except Exception:
            img = None

    if img is None and os.path.exists(AVATAR_FALLBACK):
        try:
            img = Image.open(AVATAR_FALLBACK).convert("RGBA")
        except Exception:
            img = None

    if img is None:
        img = Image.new("RGBA", (size, size), (25, 16, 60, 255))
        d = ImageDraw.Draw(img)
        d.ellipse((12, 12, size - 12, size - 12), fill=(0, 180, 255, 40), outline=(0, 220, 255), width=6)

    return ImageOps.fit(img, (size, size), method=Image.LANCZOS)


def circle_crop(img: Image.Image, size: int):
    img = ImageOps.fit(img.convert("RGBA"), (size, size), method=Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def draw_rounded_panel(base: Image.Image, box, fill, radius=28, outline=None, outline_width=2):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill, outline=outline, width=outline_width)
    base.paste(panel, (x1, y1), panel)


def draw_glow(base: Image.Image, box, color, blur=18, radius=28, alpha=70):
    x1, y1, x2, y2 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rgba = (color[0], color[1], color[2], alpha)
    d.rounded_rectangle(box, radius=radius, outline=rgba, width=3)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def fit_text(text, max_width, base_size, min_size=16):
    size = base_size
    while size >= min_size:
        font = get_font(size)
        if font.getlength(text) <= max_width:
            return font
        size -= 1
    return get_font(min_size)


def ellipsize(text, font, max_width):
    if font.getlength(text) <= max_width:
        return text
    dots = "..."
    while text and font.getlength(text + dots) > max_width:
        text = text[:-1]
    return (text + dots) if text else dots


def wrap_text(text, font, max_width, max_lines=None):
    words = str(text or "").split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = current + " " + word
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = ellipsize(lines[-1], font, max_width)
    return lines


def save_image(img: Image.Image):
    fd, path = tempfile.mkstemp(prefix="menu_neon_", suffix=".jpg")
    os.close(fd)
    img.convert("RGB").save(path, "JPEG", quality=96, optimize=True, progressive=True)
    return path


# =========================
# LẤY THÔNG TIN COMMAND
# =========================
def get_all_commands_with_info():
    items = []
    modules_dir = "modules"
    if not os.path.isdir(modules_dir):
        return items

    for module_name in sorted(os.listdir(modules_dir), key=lambda s: s.lower()):
        if not module_name.endswith(".py") or module_name == "__init__.py":
            continue
        mod_key = module_name[:-3]
        try:
            mod = importlib.import_module(f"modules.{mod_key}")
        except Exception:
            continue

        try:
            command_map = None
            if hasattr(mod, "PTA"):
                command_map = mod.PTA()
            elif hasattr(mod, "TQuan"):
                command_map = mod.TQuan()

            if not isinstance(command_map, dict) or not command_map:
                continue

            meta = getattr(mod, "des", {}) or {}
            aliases = [str(k).strip() for k in command_map.keys() if str(k).strip()]
            if not aliases:
                continue

            primary = aliases[0]
            items.append({
                "module": mod_key,
                "name": primary,
                "aliases": aliases,
                "description": str(meta.get("description", "Chưa có mô tả")).strip(),
                "power": str(meta.get("power", "User")).strip(),
                "version": str(meta.get("version", "1.0.0")).strip(),
            })
        except Exception:
            continue

    items.sort(key=lambda x: x["name"].lower())
    return items


def paginate(items, page=1, page_size=PAGE_SIZE):
    total_pages = max(1, math.ceil(len(items) / max(1, page_size)))
    if page < 1 or page > total_pages:
        return None, total_pages
    start = (page - 1) * page_size
    return items[start:start + page_size], total_pages


def search_commands(items, term: str):
    s = term.lower().strip()
    return [
        item for item in items
        if s in item["module"].lower() or s in item["name"].lower() or any(s in a.lower() for a in item["aliases"])
    ]


# =========================
# LẤY INFO BOT/USER
# =========================
def _pick_profile_from_fetch_result(info, uid):
    if info is None:
        return {}

    changed_profiles = getattr(info, "changed_profiles", None)
    if isinstance(changed_profiles, dict):
        return changed_profiles.get(str(uid)) or changed_profiles.get(uid) or {}

    if isinstance(info, dict):
        return info.get(str(uid)) or info.get(uid) or info

    return {}


def get_identity_info(client, fallback_uid):
    uid = str(getattr(client, "uid", None) or fallback_uid or "0")
    name = "BOT MENU"
    avatar = None

    try:
        raw = client.fetchUserInfo(uid)
        profile = _pick_profile_from_fetch_result(raw, uid)
        if isinstance(profile, dict):
            name = (
                profile.get("zaloName")
                or profile.get("displayName")
                or profile.get("name")
                or name
            )
            avatar = (
                profile.get("avatar")
                or profile.get("avatarUrl")
                or profile.get("normalUrl")
                or profile.get("hdUrl")
            )
    except Exception:
        pass

    return {
        "uid": uid,
        "name": str(name)[:40],
        "avatar": avatar,
        "time_str": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
    }


# =========================
# RENDER
# =========================
def create_base_canvas(width=1242, height=1268):
    bg = Image.new("RGBA", (width, height), DESIGN["bg"])
    d = ImageDraw.Draw(bg)

    # sao nền nhẹ
    stars = [
        (38, 44), (1140, 66), (1210, 170), (230, 321), (622, 512), (721, 850),
        (1180, 1015), (689, 1098), (300, 1200), (915, 1150), (450, 1030),
        (845, 240), (1045, 400), (120, 870), (990, 840), (570, 1180)
    ]
    for x, y in stars:
        r = 2 if (x + y) % 3 else 3
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 180))

    return bg


def draw_avatar_block(img: Image.Image, box, identity, current_page, total_pages, total_commands):
    x1, y1, x2, y2 = box
    d = ImageDraw.Draw(img)
    draw_glow(img, box, DESIGN["line_pink"], blur=22, radius=30, alpha=80)
    draw_rounded_panel(img, box, DESIGN["panel"], radius=30, outline=DESIGN["line_pink"], outline_width=2)

    header_h = 150
    header_box = (x1, y1, x2, y1 + header_h)
    draw_rounded_panel(img, header_box, (70, 4, 117, 245), radius=30)
    d.rectangle((x1, y1 + header_h - 30, x2, y1 + header_h), fill=(70, 4, 117, 245))

    avatar = circle_crop(load_avatar(identity.get("avatar"), 170), 170)
    av_x = x1 + (x2 - x1 - 170) // 2
    av_y = y1 + 20

    for offset, alpha in [(20, 40), (12, 80), (6, 120)]:
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((av_x - offset, av_y - offset, av_x + 170 + offset, av_y + 170 + offset), fill=(0, 210, 255, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        img.alpha_composite(glow)

    ring = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((av_x - 8, av_y - 8, av_x + 178, av_y + 178), outline=DESIGN["line_cyan"], width=5)
    rd.ellipse((av_x - 2, av_y - 2, av_x + 172, av_y + 172), outline=DESIGN["line_pink"], width=3)
    img.alpha_composite(ring)
    img.paste(avatar, (av_x, av_y), avatar)

    name_font = fit_text(identity["name"], (x2 - x1) - 40, 28, 18)
    name_text = ellipsize(identity["name"], name_font, (x2 - x1) - 40)
    name_y = y1 + 195
    d.text((x1 + (x2 - x1 - name_font.getlength(name_text)) / 2, name_y), name_text, font=name_font, fill=DESIGN["text"])

    info_font = get_font(18)
    uid_text = f"UID: {identity['uid']}"
    t_text = identity["time_str"]
    d.text((x1 + (x2 - x1 - info_font.getlength(uid_text)) / 2, name_y + 36), uid_text, font=info_font, fill=DESIGN["text_soft"])
    d.text((x1 + (x2 - x1 - info_font.getlength(t_text)) / 2, name_y + 66), t_text, font=info_font, fill=DESIGN["text_soft"])

    line_y = name_y + 115
    d.line((x1 + 18, line_y, x2 - 18, line_y), fill=DESIGN["line_pink"], width=2)

    title_font = get_font(22)
    small_font = get_font(16)
    counter_title = "DANH SÁCH LỆNH"
    d.text((x1 + (x2 - x1 - title_font.getlength(counter_title)) / 2, line_y + 16), counter_title, font=title_font, fill=DESIGN["line_pink"])

    sub = f"{total_commands} lệnh • {current_page}/{total_pages} trang"
    d.text((x1 + (x2 - x1 - small_font.getlength(sub)) / 2, line_y + 52), sub, font=small_font, fill=DESIGN["text_soft"])

    stat_top = line_y + 92
    gap = 14
    stat_w = ((x2 - x1) - 20 - gap) // 2
    stat_h = 72
    left_stat = (x1 + 10, stat_top, x1 + 10 + stat_w, stat_top + stat_h)
    right_stat = (x1 + 10 + stat_w + gap, stat_top, x2 - 10, stat_top + stat_h)

    for box_stat, label, value in [
        (left_stat, "Tổng lệnh", str(total_commands)),
        (right_stat, "Số trang", f"{current_page}/{total_pages}"),
    ]:
        draw_glow(img, box_stat, DESIGN["line_cyan"], blur=12, radius=18, alpha=70)
        draw_rounded_panel(img, box_stat, DESIGN["panel_soft"], radius=18, outline=DESIGN["line_cyan"], outline_width=2)
        cx = (box_stat[0] + box_stat[2]) / 2
        d.text((cx - get_font(16).getlength(label) / 2, box_stat[1] + 12), label, font=get_font(16), fill=DESIGN["text_soft"])
        val_font = get_font(18)
        d.text((cx - val_font.getlength(value) / 2, box_stat[1] + 38), value, font=val_font, fill=(123, 233, 255, 255))

    group_y = stat_top + stat_h + 18
    d.line((x1 + 18, group_y, x2 - 18, group_y), fill=DESIGN["line_cyan"], width=2)
    group_title = "TRẠNG THÁI NHÓM"
    d.text((x1 + (x2 - x1 - get_font(18).getlength(group_title)) / 2, group_y + 10), group_title, font=get_font(18), fill=DESIGN["text_soft"])

    col1_x = x1 + 16
    col2_x = x1 + (x2 - x1) // 2 + 8
    start_y = group_y + 48
    status_font = get_font(14)
    row_gap = 29

    for idx, item in enumerate(GROUP_STATUS_ITEMS[:7]):
        yy = start_y + idx * row_gap
        d.ellipse((col1_x, yy + 2, col1_x + 16, yy + 18), fill=DESIGN["dot_on"])
        d.text((col1_x + 22, yy), item, font=status_font, fill=DESIGN["text"])

    for idx, item in enumerate(GROUP_STATUS_ITEMS[7:14]):
        yy = start_y + idx * row_gap
        d.ellipse((col2_x, yy + 2, col2_x + 16, yy + 18), fill=DESIGN["dot_on"])
        d.text((col2_x + 22, yy), item, font=status_font, fill=DESIGN["text"])


def normalize_power_label(power_text: str):
    s = (power_text or "").lower()
    admin_keys = ["admin", "quản trị", "duyệt", "owner", "qtv"]
    return "ADMIN" if any(k in s for k in admin_keys) else "USER"


def draw_command_card(img: Image.Image, box, index_no: int, item: dict, accent):
    x1, y1, x2, y2 = box
    d = ImageDraw.Draw(img)

    draw_glow(img, box, accent, blur=16, radius=24, alpha=85)
    draw_rounded_panel(img, box, DESIGN["panel_soft"], radius=24, outline=accent, outline_width=2)

    # cột nhấn bên trái
    d.rounded_rectangle((x1 - 3, y1 + 10, x1 + 7, y2 - 10), radius=7, fill=accent)

    idx_font = get_font(17)
    title_font = fit_text(f">{item['name']}", (x2 - x1) - 240, 24, 17)
    desc_font = fit_text(item['description'], (x2 - x1) - 210, 17, 13)

    d.text((x1 + 18, y1 + 16), f"#{index_no}", font=idx_font, fill=DESIGN["text_soft"])
    title_text = ellipsize(f">{item['name']}", title_font, (x2 - x1) - 240)
    d.text((x1 + 86, y1 + 12), title_text, font=title_font, fill=accent)

    desc = ellipsize(item["description"], desc_font, (x2 - x1) - 210)
    d.text((x1 + 86, y1 + 48), desc, font=desc_font, fill=DESIGN["text_soft"])

    badge_text = normalize_power_label(item["power"])
    badge_color = DESIGN["badge_admin"] if badge_text == "ADMIN" else DESIGN["badge_user"]
    badge_w, badge_h = 106, 38
    bx2 = x2 - 18
    bx1 = bx2 - badge_w
    by1 = y1 + (y2 - y1 - badge_h) // 2
    by2 = by1 + badge_h
    draw_rounded_panel(img, (bx1, by1, bx2, by2), badge_color, radius=16)
    badge_font = get_font(16)
    d.text((bx1 + (badge_w - badge_font.getlength(badge_text)) / 2, by1 + 9), badge_text, font=badge_font, fill=(255, 255, 255, 255))


def render_menu_image(items, identity, page, total_pages):
    img = create_base_canvas()

    left_box = (34, 36, 395, 1205)
    right_start_x = 418
    right_end_x = 1210
    top_y = 36
    gap_y = 18
    card_h = 82

    draw_avatar_block(img, left_box, identity, page, total_pages, len(items) if total_pages == 1 else None)

    # sửa tổng lệnh theo toàn bộ danh sách ở lần gọi bên ngoài bằng cách gán attribute tạm
    return img


def build_menu_image(page_items, identity, page, total_pages, total_commands):
    img = create_base_canvas()
    left_box = (34, 36, 395, 1205)
    draw_avatar_block(img, left_box, identity, page, total_pages, total_commands)

    right_start_x = 418
    right_end_x = 1210
    top_y = 36
    card_h = 82
    gap_y = 18
    accent_cycle = [DESIGN["line_pink"], DESIGN["line_cyan"]]

    for i, item in enumerate(page_items):
        y1 = top_y + i * (card_h + gap_y)
        y2 = y1 + card_h
        box = (right_start_x, y1, right_end_x, y2)
        draw_command_card(img, box, ((page - 1) * PAGE_SIZE) + i + 1, item, accent_cycle[i % 2])

    return save_image(img)


def build_detail_image(item, identity):
    img = create_base_canvas(width=1242, height=900)
    d = ImageDraw.Draw(img)

    title_box = (42, 36, 1200, 130)
    draw_glow(img, title_box, DESIGN["line_pink"], blur=18, radius=26, alpha=85)
    draw_rounded_panel(img, title_box, DESIGN["panel_soft"], radius=26, outline=DESIGN["line_pink"], outline_width=2)

    title = f">{item['name']}"
    title_font = fit_text(title, 1000, 34, 20)
    d.text((70, 62), title, font=title_font, fill=DESIGN["line_pink"])

    info_box = (42, 160, 1200, 842)
    draw_glow(img, info_box, DESIGN["line_cyan"], blur=20, radius=28, alpha=80)
    draw_rounded_panel(img, info_box, DESIGN["panel"], radius=28, outline=DESIGN["line_cyan"], outline_width=2)

    avatar = circle_crop(load_avatar(identity.get("avatar"), 120), 120)
    img.paste(avatar, (74, 200), avatar)
    d.text((220, 212), ellipsize(identity['name'], get_font(26), 420), font=get_font(26), fill=DESIGN["text"])
    d.text((220, 250), f"UID: {identity['uid']}", font=get_font(18), fill=DESIGN["text_soft"])
    d.text((220, 278), identity['time_str'], font=get_font(18), fill=DESIGN["text_soft"])

    meta_y = 360
    label_font = get_font(22)
    value_font = get_font(20)
    desc_font = get_font(19)

    rows = [
        ("Lệnh", item['name']),
        ("Alias", ", ".join(item['aliases'][:10])),
        ("Version", item['version']),
        ("Quyền", item['power']),
    ]
    for label, value in rows:
        d.text((78, meta_y), f"{label}:", font=label_font, fill=DESIGN["line_cyan"])
        d.text((230, meta_y), ellipsize(value, value_font, 900), font=value_font, fill=DESIGN["text"])
        meta_y += 56

    d.text((78, meta_y + 10), "Mô tả:", font=label_font, fill=DESIGN["line_pink"])
    lines = wrap_text(item['description'], desc_font, 1040, max_lines=8)
    yy = meta_y + 54
    for line in lines:
        d.text((78, yy), line, font=desc_font, fill=DESIGN["text_soft"])
        yy += 34

    return save_image(img)


# =========================
# HANDLE LỆNH
# =========================
def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = (message or "").split()
    all_items = get_all_commands_with_info()
    identity = get_identity_info(client, author_id)

    def send_image(path, reaction="📘"):
        try:
            if not path or not os.path.exists(path) or os.path.getsize(path) <= 0:
                raise FileNotFoundError("menu image empty")
            client.sendLocalImage(path, thread_id, thread_type)
            try:
                client.sendReaction(message_object, reaction, thread_id, thread_type)
            except Exception:
                pass
        except Exception:
            client.replyMessage(Message(text="❌ Tạo/gửi ảnh menu thất bại."), message_object, thread_id, thread_type)

    if not all_items:
        client.replyMessage(Message(text="⚠️ Không quét được module để tạo menu."), message_object, thread_id, thread_type)
        return

    if len(parts) < 2:
        page_items, total_pages = paginate(all_items, 1, PAGE_SIZE)
        send_image(build_menu_image(page_items, identity, 1, total_pages, len(all_items)), "📘")
        return

    arg = parts[1].strip()
    if arg.isdigit():
        page = int(arg)
        page_items, total_pages = paginate(all_items, page, PAGE_SIZE)
        if page_items is None:
            client.replyMessage(Message(text=f"⚠️ Trang {page} không hợp lệ. Tổng trang: {total_pages}."), message_object, thread_id, thread_type)
            return
        send_image(build_menu_image(page_items, identity, page, total_pages, len(all_items)), "📄")
        return

    found = search_commands(all_items, arg)
    if not found:
        client.replyMessage(Message(text=f"❌ Không tìm thấy lệnh: {arg}"), message_object, thread_id, thread_type)
        return

    if len(found) == 1:
        send_image(build_detail_image(found[0], identity), "🔎")
        return

    page_items, total_pages = paginate(found, 1, PAGE_SIZE)
    send_image(build_menu_image(page_items, identity, 1, total_pages, len(found)), "🔍")


# =========================
# REGISTER
# =========================
def PTA():
    return {"menu": handle_menu_command}


# ===== Compatibility layer for old modules =====
def autosave(img, quality=97):
    return save_image(img)

def get_bg_image(size, page=None):
    bg = create_base_canvas(width=size[0], height=size[1])
    return bg

def _smart_resize(img, w, h):
    try:
        return img.resize((int(w), int(h)), Image.LANCZOS)
    except Exception:
        return img.resize((int(w), int(h)))

def handle_menu_menu(message, message_object, thread_id, thread_type, author_id, client):
    return handle_menu_command(message, message_object, thread_id, thread_type, author_id, client)

def ping(*args, **kwargs):
    return 'pong'

def get_mitaizl():
    try:
        return PTA()
    except Exception:
        return {'menu': handle_menu_menu}
