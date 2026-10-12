import os
import json
import time
import signal
import threading
from datetime import datetime
from zlapi.models import Message
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from PIL import Image, ImageDraw, ImageFont
import io

des = {
    'version': "1.2.0",
    'credits': "Lê Thịnhhhh",
    'description': "câu cá",
    'power': "Admin"
}


def generate_player_info_image(player, uid):
    img = Image.new("RGB", (600, 400), color=(35, 45, 60))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_text = ImageFont.truetype("arial.ttf", 22)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    draw.text((20, 20), f"🎣 HỒ SƠ NGƯỜI CHƠI", font=font_title, fill=(255, 255, 255))
    draw.text((20, 70), f"👤 ID: {uid}", font=font_text, fill=(220, 220, 220))
    draw.text((20, 100), f"⚡ Cấp độ: {player['level']} ({player['exp']}/{player['exp_next']})", font=font_text, fill=(255, 255, 200))
    draw.text((20, 130), f"💰 Vàng: {player['coins']}", font=font_text, fill=(255, 255, 100))
    draw.text((20, 160), f"🎣 Cần: {RODS[player['rod']]['name']}", font=font_text, fill=(180, 220, 255))
    bait_name = BAITS[player['bait']]['name'] if player.get("bait") else "Không dùng"
    draw.text((20, 190), f"🪱 Mồi: {bait_name}", font=font_text, fill=(180, 255, 180))
    draw.text((20, 220), f"🗺️ Khu vực: {AREAS[player['area']]['name']}", font=font_text, fill=(255, 200, 180))
    draw.text((20, 260), f"🐟 Cá thường: {player['stats'].get('common', 0)}", font=font_text, fill=(200, 200, 200))
    draw.text((20, 290), f"🐠 Cá hiếm: {player['stats'].get('rare', 0)}", font=font_text, fill=(150, 200, 255))
    draw.text((20, 320), f"🐋 Truyền thuyết: {player['stats'].get('legendary', 0)}", font=font_text, fill=(255, 220, 150))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def send_with_small_style(client, text, thread_id, thread_type, ttl=10000):
    styles = MultiMsgStyle([MessageStyle(offset=0, length=len(text), style="font", size="3", auto_format=False)])
    client.sendMessage(Message(text=text, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=ttl)

ADMIN_ID = "691778513938002350"

BASE_DIR = "modules/data/cauca"
DATA_FILE = os.path.join(BASE_DIR, "fishing_data.json")
COOLDOWN_FILE = os.path.join(BASE_DIR, "fishing_cooldowns.json")
GUILD_FILE = os.path.join(BASE_DIR, "fishing_guilds.json")
INVITE_FILE = os.path.join(BASE_DIR, "fishing_invitations.json")
TTL_FILE = os.path.join(BASE_DIR, "fishing_ttls.json")

def ensure_data_files():
    os.makedirs(BASE_DIR, exist_ok=True)
    for path in [DATA_FILE, COOLDOWN_FILE, GUILD_FILE, INVITE_FILE, TTL_FILE]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

def load_json(path):
    ensure_data_files()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    ensure_data_files()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_ttls():
    return load_json(TTL_FILE)

def save_ttls(ttls):
    save_json(TTL_FILE, ttls)

def set_ttl(key, seconds_from_now):
    ttls = load_ttls()
    expiry = int(time.time() * 1000) + int(seconds_from_now * 1000)
    ttls[key] = expiry
    save_ttls(ttls)

def ttl_remaining(key):
    ttls = load_ttls()
    now = int(time.time() * 1000)
    exp = ttls.get(key)
    if not exp:
        return 0
    rem_ms = exp - now
    return max(0, rem_ms / 1000.0)

def clean_ttls(do_expire_actions=True):
    ttls = load_ttls()
    now = int(time.time() * 1000)
    removed = []
    for k, expiry in list(ttls.items()):
        if expiry <= now:
            removed.append(k)
            ttls.pop(k, None)
            if do_expire_actions:
                if k.startswith("bait:"):
                    uid = k.split(":", 1)[1]
                    pd = load_json(DATA_FILE)
                    if uid in pd:
                        pd[uid]["bait"] = None
                        save_json(DATA_FILE, pd)
    if removed:
        save_ttls(ttls)
    return removed

def load_cooldowns():
    cd = load_json(COOLDOWN_FILE)
    return clean_cooldowns(cd)

def clean_cooldowns(cooldowns):
    now = int(time.time() * 1000)
    valid = {uid: ts for uid, ts in cooldowns.items() if ts > now}
    return valid

def save_cooldowns(cooldowns):
    cooldowns = clean_cooldowns(cooldowns)
    save_json(COOLDOWN_FILE, cooldowns)

global_leaderboard = {
    "fishing": {}
}

def sync_leaderboard(player_data):
    count = 0
    try:
        for user_id, pdata in player_data.items():
            global_leaderboard["fishing"][user_id] = {
                "level": pdata.get("level", 1),
                "exp": pdata.get("exp", 0),
                "coins": pdata.get("coins", 0),
                "totalCatch": pdata.get("totalCatch", 0),
                "common": pdata.get("stats", {}).get("common", 0),
                "rare": pdata.get("stats", {}).get("rare", 0),
                "legendary": pdata.get("stats", {}).get("legendary", 0),
                "trash": pdata.get("stats", {}).get("trash", 0),
            }
            count += 1
    except Exception:
        pass

def save_player_data():
    save_json(DATA_FILE, player_data)
    sync_leaderboard(player_data)

def load_player_data():
    global player_data
    player_data = load_json(DATA_FILE)
    sync_leaderboard(player_data)

def auto_save_loop():
    while True:
        time.sleep(300)
        try:
            save_player_data()
            save_cooldowns(load_cooldowns())
            clean_ttls(do_expire_actions=True)
        except Exception:
            pass

threading.Thread(target=auto_save_loop, daemon=True).start()

def graceful_exit(*_):
    save_player_data()
    save_cooldowns(load_cooldowns())
    clean_ttls(do_expire_actions=True)
    exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

AREAS = {
    "lake": {
        "name": "🏞️ Hồ Bình Yên",
        "unlock": 1,
        "fishRates": {"common": 70, "rare": 20, "legendary": 8, "trash": 2},
        "expMultiplier": 1.0,
        "coinMultiplier": 1.0
    },
    "river": {
        "name": "🌊 Dòng Sông Lớn",
        "unlock": 5,
        "fishRates": {"common": 60, "rare": 25, "legendary": 10, "trash": 5},
        "expMultiplier": 1.1,
        "coinMultiplier": 1.2
    },
    "sea": {
        "name": "🌅 Biển Sâu",
        "unlock": 10,
        "fishRates": {"common": 40, "rare": 35, "legendary": 20, "trash": 5},
        "expMultiplier": 1.3,
        "coinMultiplier": 1.4
    },
    "abyss": {
        "name": "⚓ Vực Thẳm",
        "unlock": 20,
        "fishRates": {"common": 25, "rare": 40, "legendary": 30, "trash": 5},
        "expMultiplier": 1.6,
        "coinMultiplier": 1.8
    },
    "forbidden": {
        "name": "🔥 Vùng Cấm Truyền Thuyết",
        "unlock": 35,
        "fishRates": {"common": 10, "rare": 30, "legendary": 55, "trash": 5},
        "expMultiplier": 2.0,
        "coinMultiplier": 2.5
    },
}

RODS = {
    "basic": {"name": "🎣 Cần Câu Gỗ", "price": 0, "bonus": {"exp": 0, "rare": 0, "cooldown": 0}},
    "iron": {"name": "⚙️ Cần Câu Sắt", "price": 1000, "bonus": {"exp": 10, "rare": 5, "cooldown": 1}},
    "gold": {"name": "✨ Cần Câu Vàng", "price": 5000, "bonus": {"exp": 20, "rare": 10, "cooldown": 2}},
    "diamond": {"name": "💎 Cần Câu Kim Cương", "price": 15000, "bonus": {"exp": 30, "rare": 15, "cooldown": 3}},
    "mythic": {"name": "🌈 Cần Câu Thần Thoại", "price": 50000, "bonus": {"exp": 50, "rare": 30, "cooldown": 5}},
}

BAITS = {
    "worm": {"name": "🪱 Giun Đất", "price": 50, "duration": 300, "effects": {"common": 15}},
    "shrimp": {"name": "🦐 Tôm Sống", "price": 300, "duration": 180, "effects": {"rare": 20}},
    "magic": {"name": "✨ Mồi Ma Thuật", "price": 1500, "duration": 120, "effects": {"legendary": 30}},
}

BOSSES = {
    "kraken": {"name": "🐙 Kraken", "hp": 500, "reward": {"exp": 300, "coins": 1000, "items": ["shrimp"]}},
    "megalodon": {"name": "🦈 Megalodon", "hp": 2000, "reward": {"exp": 1000, "coins": 5000, "items": ["magic"]}},
    "leviathan": {"name": "🌊 Leviathan", "hp": 5000, "reward": {"exp": 3000, "coins": 15000, "items": ["magic", "mythic"]}},
}

UPGRADES = {
    "luck": {"name": "🍀 May Mắn", "max": 10, "price": 2000, "effect": "+1% tỉ lệ cá hiếm mỗi cấp"},
    "strength": {"name": "💪 Sức Mạnh", "max": 10, "price": 3000, "effect": "+1% sát thương boss mỗi cấp"},
    "efficiency": {"name": "⚡ Hiệu Suất", "max": 10, "price": 4000, "effect": "-1s cooldown mỗi cấp"},
}

def initialize_fishing_system():
    ensure_data_files()
    load_player_data()
    clean_ttls(do_expire_actions=True)

initialize_fishing_system()

# ==========================
# 🎲 RANDOM FISH GENERATOR
# ==========================
import random
import math

def random_fish(area_name, rod_bonus=0, bait_bonus=None):
    """Trả về (fish_type, rarity, weight, coin_reward)"""
    area = AREAS.get(area_name, AREAS["lake"])
    base = area["fishRates"]
    bait_bonus = bait_bonus or {}

    total_weight = sum(base.values())
    r = random.uniform(0, total_weight)
    cumulative = 0
    rarity = "common"
    for k, v in base.items():
        bonus = bait_bonus.get(k, 0)
        cumulative += v + bonus
        if r <= cumulative:
            rarity = k
            break

    fish_types = {
        "common": ["🐟 Cá Rô", "🐠 Cá Chép", "🐡 Cá Nóc"],
        "rare": ["🦑 Mực", "🦐 Tôm Hùm", "🐙 Bạch Tuộc"],
        "legendary": ["🐉 Cá Rồng", "🐋 Cá Voi", "🐊 Thần Ngư"],
        "trash": ["🪵 Cành Cây", "🩴 Dép Rách", "🗑️ Rác Biển"]
    }

    fish = random.choice(fish_types[rarity])
    weight = random.randint(200, 2000)
    coin = int(weight / 5 * area["coinMultiplier"])
    return fish, rarity, weight, coin

# ==========================
# 🧾 PLAYER FUNCTIONS
# ==========================

def get_player(data, uid):
    if uid not in data:
        data[uid] = {
            "level": 1,
            "exp": 0,
            "coins": 0,
            "rod": "basic",
            "bait": None,
            "area": "lake",
            "stats": {"common": 0, "rare": 0, "legendary": 0, "trash": 0},
            "bag": [],
            "bossKills": 0,
            "upgrades": {"luck": 0, "strength": 0, "efficiency": 0},
            "guild": None
        }
    # Ensure bait still valid by TTL
    if data[uid].get("bait"):
        rem = ttl_remaining(f"bait:{uid}")
        if rem <= 0:
            data[uid]["bait"] = None
    return data[uid]


def add_exp(player, amount):
    player["exp"] += amount
    level_up = 0
    while player["exp"] >= player["level"] * 100:
        player["exp"] -= player["level"] * 100
        player["level"] += 1
        level_up += 1
    return level_up
# ==========================
# ✨ Helper: Mention
# ==========================
def mention_text(uid, text):
    tag = f"@{uid}"
    return Message(text=f"{tag} {text}", mention=[{"tag": tag, "id": uid}])
# ==========================
# 🏗️ MAIN COMMAND HANDLER
# ==========================
def handle_cauca_command(message, message_object, thread_id, thread_type, author_id, client):
    global player_data
    msg = message.strip().lower()
    parts = msg.split()
    cmd = parts[1] if len(parts) > 1 else "help"
    uid = str(author_id)

    # LOAD DATA
    cooldowns = load_cooldowns()
    player = get_player(player_data, uid)
    now_ms = int(time.time() * 1000)

    # COOLDOWN CHECK
    if uid in cooldowns and cooldowns[uid] > now_ms:
        wait_s = (cooldowns[uid] - now_ms) / 1000
        client.sendMessage(Message(text=f"⏳ Chờ {int(wait_s)}s để câu tiếp!"), thread_id=thread_id, thread_type=thread_type)
        return

    # ====== COMMANDS ======
    if cmd == "help":
        help_text = (
            "🎣 GAME CÂU CÁ BÉ BII 🎣\n"
            "• cauca cau → Thả cần câu 🎣\n"
            "• cauca bag → Xem túi cá 🎒\n"
            "• cauca shop → Cửa hàng 🛒\n"
            "• cauca mua <vật phẩm> → Mua vật phẩm 💰\n"
            "• cauca sell → Bán cá 🪙\n"
            "• cauca can → Xem danh sách cần câu ⚙️\n"
            "• cauca moi → Xem danh sách mồi câu 🪱\n"
            "• cauca map → Xem bản đồ & di chuyển khu vực 🗺️\n"
            "• cauca boss → Đánh boss khổng lồ ⚔️\n"
            "• cauca upgrade → Nâng cấp kỹ năng ⚡\n"
            "• cauca info → Xem hồ sơ cá nhân 📜\n"
            "• cauca rank → Xem bảng xếp hạng 🏆\n"
            "• cauca guild → Xem thông tin bang hội 🏰\n"
            "• cauca quest → Nhiệm vụ hàng ngày 🎯\n"
            "• cauca achievement → Thành tựu 🏅\n"
            "\n"
            "💼 LỆNH ADMIN:\n"
            "• cauca nap <user_id> <vàng> → Nạp vàng 💵\n"
            "• cauca buff <user_id> <level> → Buff cấp ⚡\n"
            "\n"
            "🐟 ĐỘ HIẾM CỦA CÁ:\n"
            "• 🐟 Cá Thường (70%) — 10–18 EXP\n"
            "• 🐠 Cá Hiếm (20%) — 25–40 EXP\n"
            "• 🐉 Cá Huyền Thoại (5%) — 80–120 EXP\n"
            "• 👟 Rác (5%) — 1 EXP\n"
            "\n"
            "🪱 GIỚI HẠN MỒI CÂU:\n"
            "• Mỗi người chỉ có 5 lần sử dụng mồi miễn phí\n"
            "• Mua mồi câu từ shop để reset lại giới hạn\n"
            "\n"
            "⏰ Cooldown: 1 giây/lần câu\n"
            "🎯 Lên cấp để mở khóa khu vực & boss mới!\n"
        )
        client.sendMessage(Message(text=help_text), thread_id=thread_id, thread_type=thread_type)
        return

        #    # 🎣 LỆNH CÂU CÁ
    if cmd == "cau":
        rod = RODS.get(player["rod"], RODS["basic"])
        fish, rarity, w, c = random_fish(player["area"])
        exp_gain = 10 + rod["bonus"]["exp"]
        player["bag"].append({"fish": fish, "rarity": rarity, "w": w, "c": c})
        player["coins"] += c
        player["stats"][rarity] += 1
        lvup = add_exp(player, exp_gain)

        cooldowns[uid] = now_ms + 1000
        save_json(DATA_FILE, player_data)
        save_json(COOLDOWN_FILE, cooldowns)

        # 🧩 nếu chưa có exp_next thì đặt mặc định
        exp_next = player.get("exp_next", 100)

        msg_lines = [
            "🎉 **CÂU CÁ THÀNH CÔNG!** 🎉",
            "",
            f"{fish} ({rarity})",
            "",
            "🎁 **PHẦN THƯỞNG:**",
            f"💰 +{c} vàng",
            f"✨ +{exp_gain} EXP",
            f"⚖️ Trọng lượng: {w}g",
            "",
            f"🎯 Cấp độ: {player['level']} | EXP: {player['exp']}/{exp_next}",
            f"💰 Tổng vàng: {player['coins']:,}",
        ]

        if lvup > 0:
            msg_lines.append(f"\n⬆️ **Lên cấp {player['level']}!** 🎉")

        msg_lines.append("\n🐟 Tiếp tục thả cần nào!")

        msg = "\n".join(msg_lines)

        client.sendMessage(
            mention_text(uid, msg),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=10000
        )

        print(f"[FISHING] 🎣 {uid} bắt {fish} ({rarity}) +{c} vàng.")
        return


           # 💼 BAG (Túi đồ)
    if cmd == "bag":
        bag = player.get("bag", [])[-10:]  # Lấy 10 cá mới nhất
        if not bag:
            client.sendMessage(
                Message(text="👜 Túi trống."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        # Gộp cá trùng nhau (cùng tên, rarity, giá, trọng lượng)
        grouped = {}
        for b in bag:
            key = (b['fish'], b['rarity'], b['w'], b['c'])
            grouped[key] = grouped.get(key, 0) + 1

        # Tạo danh sách hiển thị
        lines = []
        for (fish, rarity, w, c), qty in grouped.items():
            lines.append(f"{fish} ({rarity}) — {w}g — {c} vàng x{qty}")

        msg = "🧺 **TÚI CÁ CỦA BẠN** 🧺\n\n" + "\n".join(lines)
        client.sendMessage(
            Message(text=msg),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

            
        
        # ⚔️ LỆNH DANHBOSS
    if cmd == "danhboss":
        handle_danhboss_command(uid, player_data, client, thread_id, thread_type)
        return


        # ✅ thêm "x1" ở cuối mỗi dòng
        lines = [
            f"{b['fish']} ({b['rarity']}) - {b['w']}g - {b['c']} vàng x1"
            for b in bag
        ]

        # 💡 danh sách các loại cần + ID
        rod_list = "\n".join([
            f"{v['name']} (ID: {k})"
            for k, v in RODS.items()
        ])

        bag_text = "🧺 Túi cá:\n" + "\n".join(lines)
        bag_text += f"\n\n📦 Tổng số cá trong túi: {total_fish}"
        bag_text += "\n\n🎣 Danh sách các loại cần câu:\n" + rod_list

        client.sendMessage(
            Message(text=bag_text),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

            # 💰 LỆNH NẠP — Hiển thị bảng giá và cho admin nạp
    if cmd == "nap":
        # Nếu người chơi chỉ gõ "cauca nap" → hiển thị bảng giá
        if len(parts) == 2:
            nap_table = (
                "💳 **BẢNG GIÁ NẠP VÀNG** 💳\n\n"
                "💵 20.000 VNĐ → 💰 20.000 vàng\n"
                "💵 50.000 VNĐ → 💰 60.000 vàng (+10%)\n"
                "💵 100.000 VNĐ → 💰 130.000 vàng (+30%)\n"
                "💵 200.000 VNĐ → 💰 300.000 vàng (+50%)\n"
                "💎 Nạp từ admin sẽ cộng trực tiếp vào tài khoản.\n\n"
                "👉 Liên hệ: **Lê Thịnhh💖** để nạp nhé!"
            )
            client.sendMessage(
                Message(text=nap_table),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        # Nếu admin nạp cho người khác
        if len(parts) >= 4 and uid == ADMIN_ID:
            target_id = parts[2]
            try:
                gold = int(parts[3])
            except ValueError:
                client.sendMessage(
                    Message(text="⚠️ Số vàng phải là con số hợp lệ!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            target_player = get_player(player_data, target_id)
            target_player["coins"] = target_player.get("coins", 0) + gold
            save_json(DATA_FILE, player_data)

            msg = f"💰 Admin đã nạp **{gold:,} vàng** cho người chơi ID `{target_id}`!"
            client.sendMessage(
                Message(text=msg),
                thread_id=thread_id,
                thread_type=thread_type
            )
            print(f"[ADMIN] 💰 {uid} nạp {gold:,} vàng cho {target_id}")
            return

        # Nếu không phải admin mà cố nạp cho người khác
        client.sendMessage(
            Message(text="🚫 Chỉ admin mới được phép nạp vàng trực tiếp!"),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return


    # 🛒 SHOP
    if cmd == "shop":
        items = []
        items.append("🎣 CẦN CÂU:")
        for k, v in RODS.items():
            items.append(f"{v['name']} - {v['price']} vàng")
        items.append("\n🪱 MỒI CÂU:")
        for k, v in BAITS.items():
            items.append(f"{v['name']} - {v['price']} vàng - Thời gian: {v['duration']}s")
        client.sendMessage(Message(text="\n".join(items)), thread_id=thread_id, thread_type=thread_type)
        return

    # 🛍️ MUA
    if cmd == "mua" and len(parts) >= 3:
        item = parts[2]
        all_shop = {**RODS, **BAITS}
        if item not in all_shop:
            client.sendMessage(Message(text="❌ Không có vật phẩm này!"), thread_id=thread_id, thread_type=thread_type)
            return
        price = all_shop[item]["price"]
        if player["coins"] < price:
            client.sendMessage(Message(text="❌ Không đủ vàng!"), thread_id=thread_id, thread_type=thread_type)
            return
        player["coins"] -= price
        if item in RODS:
            player["rod"] = item
        else:
            player["bait"] = item
            # Set TTL for bait using BAITS[item]['duration'] seconds
            duration_s = BAITS[item].get("duration", 0)
            if duration_s > 0:
                set_ttl(f"bait:{uid}", duration_s)
        save_json(DATA_FILE, player_data)
        client.sendMessage(Message(text=f"✅ Mua {all_shop[item]['name']} thành công!"), thread_id=thread_id, thread_type=thread_type)
        print(f"[FISHING] 💰 {uid} mua {item}")
        return

    # 🧙‍♂️ UPGRADE
    if cmd == "upgrade":
        upgrades_text = "⚙️ DANH SÁCH NÂNG CẤP:\n"
        for k, v in UPGRADES.items():
            lv = player["upgrades"].get(k, 0)
            upgrades_text += f"• {v['name']} (Lv {lv}/{v['max']}) - {v['effect']} - Giá {v['price']} vàng\n"
        client.sendMessage(Message(text=upgrades_text), thread_id=thread_id, thread_type=thread_type)
        return



    # 🏅 RANK
    if cmd == "rank":
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
        lines = [f"{i+1}. {p[0]} - {p[1]['coins']} vàng" for i, p in enumerate(sorted_players)]
        client.sendMessage(Message(text="🏆 TOP NGƯỜI GIÀU:\n" + "\n".join(lines)), thread_id=thread_id, thread_type=thread_type)
        return

        # 🧍 XEM HỒ SƠ NGƯỜI CHƠI (INFO)
    if cmd == "info":
        buffer = generate_player_info_image(player, uid)
        client.sendLocalImage(
            image=buffer,
            message=Message(text=f"📜 Hồ sơ của bạn, {player['name'] if 'name' in player else uid}:"),
            thread_id=thread_id,
            thread_type=thread_type
        )
        print(f"[INFO] 📜 {uid} xem hồ sơ cá nhân.")
        return
        # 🎣 XEM DANH SÁCH CẦN CÂU
    if cmd == "can":
        current_rod = player["rod"]
        rod_lines = []
        for rod_id, rod in RODS.items():
            active = "✅" if rod_id == current_rod else "⚪"
            rod_lines.append(
                f"{active} {rod['name']} (ID: {rod_id}) - 💰 {rod['price']} vàng"
            )

        rod_text = (
            "🎣 DANH SÁCH CẦN CÂU 🎣\n\n"
            + "\n".join(rod_lines)
            + f"\n\n🔸 Cần đang sử dụng: {RODS[current_rod]['name']} (ID: {current_rod})"
        )

        client.sendMessage(
            Message(text=rod_text),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
        # 🪱 XEM DANH SÁCH MỒI CÂU
    if cmd == "moi":
        current_bait = player.get("bait")
        bait_lines = []

        for bait_id, bait in BAITS.items():
            active = "✅" if bait_id == current_bait else "⚪"
            effects = ", ".join([f"+{v}% {k}" for k, v in bait["effects"].items()])
            bait_lines.append(
                f"{active} {bait['name']} (ID: {bait_id}) - 💰 {bait['price']} vàng - ⏳ {bait['duration']}s - {effects}"
            )

        bait_text = (
            "🪱 DANH SÁCH MỒI CÂU 🪱\n\n"
            + "\n".join(bait_lines)
        )

        if current_bait:
            rem = ttl_remaining(f"bait:{uid}")
            rem_text = f"{int(rem)}s còn lại" if rem > 0 else "đã hết hạn"
            bait_text += f"\n\n🎣 Mồi đang dùng: {BAITS[current_bait]['name']} ({rem_text})"
        else:
            bait_text += "\n\n🎣 Hiện tại bạn chưa dùng mồi nào."

        client.sendMessage(
            Message(text=bait_text),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
        # 🗺️ XEM & DI CHUYỂN MAP
    if cmd == "map":
        # Nếu chỉ gõ "cauca map" -> xem danh sách
        if len(parts) == 2:
            current_area = player["area"]
            lines = []
            for area_id, area in AREAS.items():
                locked = "✅" if player["level"] >= area["unlock"] else "🔒"
                current = "📍" if area_id == current_area else "⚪"
                lines.append(
                    f"{current} {locked} {area['name']} (ID: {area_id}) - 🔓 Mở khóa Lv {area['unlock']}"
                )

            map_text = (
                "🗺️ DANH SÁCH KHU VỰC CÂU CÁ 🗺️\n\n"
                + "\n".join(lines)
                + f"\n\n📍 Đang ở: {AREAS[current_area]['name']} (ID: {current_area})"
                + "\n\n➡️ Gõ: cauca map <id> để di chuyển nếu bạn đủ cấp."
            )

            client.sendMessage(
                Message(text=map_text),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        # Nếu có ID khu -> thử di chuyển
        if len(parts) >= 3:
            target_id = parts[2]
            if target_id not in AREAS:
                client.sendMessage(
                    Message(text="❌ Khu vực không tồn tại!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            target_area = AREAS[target_id]
            if player["level"] < target_area["unlock"]:
                client.sendMessage(
                    Message(text=f"🔒 Cần Lv {target_area['unlock']} mới có thể đến {target_area['name']}!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            # Cập nhật khu vực
            old_area = player["area"]
            player["area"] = target_id
            save_json(DATA_FILE, player_data)

            msg = (
                f"🚶 Bạn đã di chuyển từ {AREAS[old_area]['name']} "
                f"đến {AREAS[target_id]['name']} thành công!\n"
                f"🎣 Hãy thử câu cá tại khu vực mới!"
            )
            client.sendMessage(
                Message(text=msg),
                thread_id=thread_id,
                thread_type=thread_type
            )
            print(f"[FISHING] 🌍 {uid} di chuyển đến {target_id}.")
            return
            
        # ⚡ LỆNH BUFF LEVEL (ADMIN)
    if cmd == "buff":
        # Kiểm tra quyền admin
        if uid != ADMIN_ID:
            client.sendMessage(
                Message(text="⛔ Bạn không có quyền dùng lệnh này."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        # Cú pháp: cauca buff <user_id> <số_level>
        if len(parts) < 4:
            client.sendMessage(
                Message(text="⚠️ Cú pháp: cauca buff <user_id> <số_level>"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        target_id = str(parts[2])
        try:
            add_lv = int(parts[3])
        except ValueError:
            client.sendMessage(
                Message(text="❌ Số level phải là số nguyên."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        target_player = get_player(player_data, target_id)
        old_lv = target_player["level"]
        target_player["level"] += add_lv
        if target_player["level"] < 1:
            target_player["level"] = 1  # không cho xuống 0
        save_json(DATA_FILE, player_data)

        # Tin nhắn xác nhận
        msg_admin = f"✅ Đã buff +{add_lv} cấp cho {target_id} (Lv {old_lv} ➜ {target_player['level']})."
        msg_user = f"⚡ Bạn vừa được Admin buff +{add_lv} cấp! (Cấp mới: {target_player['level']})"

        client.sendMessage(
            Message(text=msg_admin),
            thread_id=thread_id,
            thread_type=thread_type
        )

        client.sendMessage(
            Message(text=msg_user),
            thread_id=thread_id,
            thread_type=thread_type
        )

        print(f"[ADMIN] ⚡ Admin {uid} buff {add_lv} cấp cho {target_id} (Lv {old_lv} ➜ {target_player['level']}).")
        return
        #cc
            # 🧩 LỆNH BOSS
    if cmd == "boss":
        # Nếu admin gõ "cauca boss auto" thì bật auto boss
        if len(parts) > 2 and parts[2] == "auto" and uid == ADMIN_ID:
            start_auto_boss(client, thread_id, thread_type)
            client.sendMessage(
                Message(text="✅ Hệ thống auto triệu hồi boss mỗi giờ đã bật!"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        # ⚔️ các xử lý boss khác (ví dụ fight)
        client.sendMessage(
            Message(text="⚔️ Gõ cauca boss fight để chiến đấu hoặc cauca boss auto để bật auto boss."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

        # ❌ Nếu không khớp lệnh nào
    client.sendMessage(
        Message(
            text=(
                "😗 Lệnh Nay hien Dang duoc bé bii cap nhat😗!\n"

            )
        ),
        thread_id=thread_id,
        thread_type=thread_type
    )

    # Xoá trạng thái nếu có
    if uid in active_commands:
        del active_commands[uid]
    return 



    # 🏰 GUILD
    if cmd == "guild":
        guilds = load_json(GUILD_FILE)
        guild_name = player["guild"] or "Chưa tham gia"
        client.sendMessage(Message(text=f"🏰 Bang hội: {guild_name}"), thread_id=thread_id, thread_type=thread_type)
        return

    # 🆘 DEFAULT
    client.sendMessage(Message(text="❌ Lệnh không hợp lệ! Gõ 'cauca help' để xem hướng dẫn."), thread_id=thread_id, thread_type=thread_type)

# ==========================
# 🚀 INIT SYSTEM
# ==========================

def initialize_fishing_system():
    ensure_data_files()
    load_player_data()
    # Clean expired ttls at startup
    clean_ttls(do_expire_actions=True)
   

initialize_fishing_system()


# ==========================
# 🚨 KHỞI ĐỘNG AUTO BOSS
# ==========================
def start_auto_boss(client, thread_id, thread_type):
    t = threading.Thread(
        target=auto_spawn_boss,
        args=(client, thread_id, thread_type),
        daemon=True
    )
    t.start()
    
# ==========================
# 📤 EXPORT FOR BOT
# ==========================
import threading
import time

def send_temp_message(client, text, thread_id, thread_type, delay=10):
    """
    Gửi tin nhắn tạm thời, tự xoá sau X giây (mặc định 10s)
    """
    try:
        msg = client.sendMessage(Message(text=text), thread_id=thread_id, thread_type=thread_type)
        if msg and hasattr(msg, "message_id"):
            def delete_later(mid):
                time.sleep(delay)
                try:
                    client.unsendMessage(mid)
                    print(f"[FISHING] 🕒 Đã xoá tin nhắn sau {delay}s")
                except Exception as e:
                    print(f"[FISHING] ⚠️ Lỗi xoá tin nhắn: {e}")
            threading.Thread(target=delete_later, args=(msg.message_id,), daemon=True).start()
        return msg
    except Exception as e:
        print(f"[FISHING] ⚠️ Lỗi gửi tin nhắn tạm: {e}")

import threading
import random
import time

# ==========================
# ⚔️ AUTO TRIỆU HỒI BOSS MỖI GIỜ + CHỌN BOSS YẾU NHẤT
# ==========================

CURRENT_BOSS = None  # 🐉 Boss hiện tại đang hoạt động

def start_auto_boss(client, default_thread_id, default_thread_type):
    import threading, time, random

    def auto_boss_loop():
        global CURRENT_BOSS
        first = True  # Lần đầu tiên sẽ spawn ngay, không chờ

        while True:
            try:
                # 🕒 Chờ 1 tiếng giữa các lần spawn (3600s)
                # 👉 Nếu test, đổi 3600 -> 60 (1 phút)
                if not first:
                    time.sleep(3600)
                first = False

                # 🎯 Chọn boss yếu nhất (ít HP nhất)
                try:
                    min_hp = min(b.get("hp", 99) for b in BOSSES.values())
                    weak_bosses = [(i, b) for i, b in BOSSES.items() if b.get("hp", 99) == min_hp]
                    boss_id, boss = random.choice(weak_bosses)
                except Exception:
                    boss_id, boss = random.choice(list(BOSSES.items()))  # fallback nếu lỗi

                # 🔧 Dữ liệu an toàn
                emoji = boss.get("emoji", "🐉")
                name = boss.get("name", "Boss bí ẩn")
                area = boss.get("area", "Khu vực không xác định")
                hp = boss.get("hp", 300)
                reward = boss.get("reward", {"coins": 1000, "exp": 100, "items": []})

                # 💾 Lưu boss hiện tại
                CURRENT_BOSS = {
                    "id": boss_id,
                    "name": name,
                    "emoji": emoji,
                    "area": area,
                    "hp": hp,
                    "max_hp": hp,
                    "reward": reward,
                    "attackers": {}
                }

                # 🧾 Thông báo boss xuất hiện
                msg = (
                    f"⚔️ **BOSS YẾU XUẤT HIỆN!** ⚔️\n\n"
                    f"{emoji} {name} đã xuất hiện tại {area}!\n"
                    f"❤️ Máu: {hp:,}\n"
                    f"💰 Thưởng: {reward.get('coins', 0):,} vàng + {reward.get('exp', 0)} EXP\n"
                    f"🎁 Vật phẩm: {', '.join(reward.get('items', [])) or 'Không có'}\n\n"
                    f"⏳ Gõ **cauca danhboss** để tham chiến!"
                )

                client.sendMessage(
                    Message(text=msg),
                    thread_id=default_thread_id,
                    thread_type=default_thread_type
                )

                print(f"[AUTO-BOSS] 🐉 Đã triệu hồi boss yếu nhất: {name} ({boss_id}).")

            except Exception as e:
                print(f"[AUTO-BOSS] ⚠️ Lỗi: {e}")
                time.sleep(30)

    # ✅ Chạy thread nền
    t = threading.Thread(target=auto_boss_loop, daemon=True)
    t.start()
    print("[AUTO-BOSS] ✅ Hệ thống triệu hồi boss yếu nhất tự động mỗi giờ đã bật.")

# ==========================
# ⚔️ LỆNH ĐÁNH BOSS — CÓ FIX LỖI 'name'
# ==========================
def handle_danhboss_command(uid, player_data, client, thread_id, thread_type):
    import random, time
    global CURRENT_BOSS

    player = get_player(player_data, uid)
    if not CURRENT_BOSS:
        client.sendMessage(
            Message(text="🐉 Hiện tại không có boss nào đang hoạt động."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

    boss = CURRENT_BOSS

    # 🎯 Tên người chơi an toàn
    pname = player.get("name", f"Người chơi {uid}")

    # 🎯 Gây sát thương theo cấp độ
    dmg = random.randint(50, 120) + player.get("level", 1) * 5
    boss["hp"] -= dmg
    if boss["hp"] < 0:
        boss["hp"] = 0

    # Lưu damage
    boss["attackers"][uid] = boss["attackers"].get(uid, 0) + dmg

    # 🧾 Thông báo tấn công
    msg = (
        f"⚔️ {pname} tấn công {boss.get('emoji', '🐉')} {boss.get('name', 'Boss bí ẩn')}!\n"
        f"💥 Gây {dmg:,} sát thương!\n"
        f"❤️ Boss còn {boss['hp']:,}/{boss['max_hp']:,} HP."
    )

    # 💀 Nếu boss chết
    if boss["hp"] <= 0:
        reward = boss.get("reward", {"exp": 100, "coins": 500})
        exp_gain = reward.get("exp", 100)
        coin_gain = reward.get("coins", 500)

        player["exp"] = player.get("exp", 0) + exp_gain
        player["coins"] = player.get("coins", 0) + coin_gain

        # 🎖️ Xếp hạng damage
        ranking = sorted(boss["attackers"].items(), key=lambda x: x[1], reverse=True)
        top_lines = []
        for i, (pid, dmg_done) in enumerate(ranking[:3]):
            pname = player_data.get(pid, {}).get("name", f"Người chơi {pid}")
            top_lines.append(f"{i+1}. {pname} — {dmg_done:,} dmg")

        msg = (
            f"🎉 **BOSS ĐÃ BỊ HẠ!** 🎉\n\n"
            f"{boss.get('emoji', '🐉')} {boss.get('name', 'Boss bí ẩn')} đã ngã gục!\n"
            f"⭐ +{exp_gain} EXP\n"
            f"💰 +{coin_gain:,} vàng\n\n"
            f"🏆 **Top Sát Thương:**\n" + "\n".join(top_lines)
        )

        # 🧹 Reset boss
        CURRENT_BOSS = None
        save_json(DATA_FILE, player_data)

    # Gửi tin nhắn kết quả
    client.sendMessage(
        Message(text=msg),
        thread_id=thread_id,
        thread_type=thread_type
    )

def PTA():
    """Export cho hệ thống bot"""
    return {
        "cauca": handle_cauca_command
    }

