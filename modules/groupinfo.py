import os
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, ThreadType

des = {
    "version": "1.3",
    "credits": "N G H",
    "description": "Groupinfo UI to đẹp vừa đủ, không mất chữ",
    "power": "Thành viên"
}

CACHE = "modules/cache/groupinfo"
os.makedirs(CACHE, exist_ok=True)

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)


# ---------------- Avatar tròn ----------------
def load_avatar(url, size=240):
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        img = Image.new("RGBA", (size, size), (120,120,120))

    img = img.resize((size, size))

    mask = Image.new("L", (size, size))
    d = ImageDraw.Draw(mask)
    d.ellipse((0,0,size,size), fill=255)
    img.putalpha(mask)

    return img


# ---------------- Auto wrap ----------------
def wrap(text, font, max_w):
    words = text.split()
    cur = ""
    lines = []

    for w in words:
        test = (cur + " " + w).strip()
        if font.getlength(test) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)
    return lines[:3]  # giới hạn 3 dòng để đẹp


# ---------------- RENDER ẢNH ----------------
def render_groupinfo(group, creator):
    # Ảnh rộng - cao vừa đủ
    W, H = 1200, 850
    img = Image.new("RGBA", (W, H), (17, 20, 28))
    d = ImageDraw.Draw(img)

    # Font
    f_title = load_font(70)
    f_key   = load_font(40)
    f_val   = load_font(40)

    # Title
    d.text((W//2 - 260, 50), "THÔNG TIN NHÓM", font=f_title, fill=(0,200,255))

    # ---------------- CARD ----------------
    CW, CH = 1000, 540
    CX, CY = 100, 200

    card = Image.new("RGBA", (CW, CH), (25,25,35,240))
    dc = ImageDraw.Draw(card)

    dc.rounded_rectangle((0,0,CW,CH), radius=40, outline=(0,200,255), width=5)

    # Avatar to đẹp
    av = load_avatar(group.fullAvt, 240)
    card.alpha_composite(av, (50, 150))

    # ---------------- TEXT ----------------
    text_x = 340
    y = 70
    max_w = CW - text_x - 50

    desc   = group.desc or "Không có mô tả"
    total  = getattr(group, "totalMember", "Không rõ")
    gid    = getattr(group, "globalId", "Không rõ")

    try:
        created = datetime.fromtimestamp(group.createdTime/1000).strftime("%H:%M • %d/%m/%Y")
    except:
        created = "Không rõ"

    info = [
        ("Tên nhóm:", group.name),
        ("Mô tả:", desc),
        ("Thành viên:", str(total)),
        ("Trưởng nhóm:", creator),
        ("Ngày tạo:", created),
        ("Global ID:", gid),
    ]

    for key, val in info:
        dc.text((text_x, y), key, font=f_key, fill=(0,200,255))

        lines = wrap(val, f_val, max_w)
        ly = y

        for line in lines:
            dc.text((text_x + 260, ly), line, font=f_val, fill="white")
            ly += f_val.size + 6

        y += max(f_key.size + 20, len(lines) * (f_val.size + 15))

    img.alpha_composite(card, (CX, CY))

    out = os.path.join(CACHE, "groupinfo_final.png")
    img.convert("RGB").save(out, quality=95)
    return out, W, H


# ---------------- COMMAND ----------------
def handle_groupinfo(message, msg_obj, tid, ttype, uid, client):
    try:
        data = client.fetchGroupInfo(tid)
        group = data.gridInfoMap.get(tid)

        def getname(id):
            try:
                info = client.fetchUserInfo(id)
                p = info.changed_profiles.get(id, {})
                return p.get("zaloName", "Ẩn danh")
            except:
                return "Ẩn danh"

        creator = getname(group.creatorId)

        img_path, W, H = render_groupinfo(group, creator)
        client.sendLocalImage(img_path, tid, ttype, width=W, height=H)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi groupinfo: {e}"),
            msg_obj, tid, ttype
        )


def PTA():
    return {
        "groupinfo": handle_groupinfo
    }
