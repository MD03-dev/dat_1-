import json
import random
import time
from zlapi.models import *
from config import PREFIX

des = {
    'version': "2.0.0",
    'credits': "Nguyễn Tiến Đức + GPT",
    'description': "Game Chứng Khoán + Biểu Đồ Riêng",
    'power': "Thành viên"
}

PRICE_FILE = "modules/cache/stock_data.json"
COOLDOWN = 8
last_play = {}

# ================= LOAD / SAVE =================
def load_money():
    try:
        with open('modules/cache/money.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_money(data):
    with open('modules/cache/money.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_stock():
    try:
        with open(PRICE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_stock(data):
    with open(PRICE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ================= UTILS =================
def format_money(n):
    n = int(n)
    if abs(n) >= 1_000_000_000:
        return f"{n//1_000_000_000}B"
    if abs(n) >= 1_000_000:
        return f"{n//1_000_000}M"
    if abs(n) >= 1_000:
        return f"{n//1_000}K"
    return str(n)

def parse_bet(text, balance):
    text = text.lower()
    if text == "all":
        return balance if balance > 0 else 0, None
    if text.endswith('%'):
        return int(balance * float(text[:-1]) / 100), None
    mul = 1
    if text.endswith('k'):
        mul = 1_000
        text = text[:-1]
    elif text.endswith('m'):
        mul = 1_000_000
        text = text[:-1]
    try:
        return int(float(text) * mul), None
    except:
        return 0, "Sai số tiền"

# ================= STOCK =================
def init_stock(uid, stock):
    if uid not in stock:
        stock[uid] = {
            "price": random.randint(800, 1200),
            "history": []
        }

def update_price(uid, stock):
    percent = random.randint(-10, 10)
    if percent == 0:
        percent = 1
    price = stock[uid]["price"]
    new_price = max(1, int(price * (100 + percent) / 100))
    stock[uid]["price"] = new_price
    stock[uid]["history"].append(new_price)
    stock[uid]["history"] = stock[uid]["history"][-10:]
    return percent

def render_chart(prices):
    blocks = "▁▂▃▄▅▆▇█"
    min_p, max_p = min(prices), max(prices)
    if min_p == max_p:
        return blocks[0] * len(prices)
    chart = ""
    for p in prices:
        idx = int((p - min_p) / (max_p - min_p) * (len(blocks) - 1))
        chart += blocks[idx]
    return chart

# ================= HELP =================
def help_text():
    return (
        "📈 CHỨNG KHOÁN ẢO 📉\n"
        "━━━━━━━━━━━━━━━\n"
        f"➜ {PREFIX}ck mua <tiền>\n"
        f"➜ {PREFIX}ck bán <tiền>\n"
        f"➜ {PREFIX}ck chart\n\n"
        "🎯 Luật:\n"
        "➜ Giá biến động ±10%\n"
        "➜ Mỗi người 1 cổ phiếu riêng\n"
        "➜ Có biểu đồ lịch sử"
    )

# ================= MAIN =================
def handle_ck(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    uid = str(author_id)
    money = load_money()
    stock = load_stock()

    init_stock(uid, stock)

    if len(args) == 1 or args[1].lower() in ["help", "hd"]:
        client.replyMessage(Message(text=help_text()), message_object, thread_id, thread_type)
        return

    if args[1].lower() == "chart":
        history = stock[uid]["history"] or [stock[uid]["price"]]
        chart = render_chart(history)
        msg = (
            "📊 BIỂU ĐỒ CỔ PHIẾU 📊\n"
            f"Giá hiện tại: {stock[uid]['price']}\n\n"
            f"{chart}"
        )
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)
        return

    if args[1].lower() not in ["mua", "bán"]:
        client.replyMessage(Message(text="❌ Sai lệnh"), message_object, thread_id, thread_type)
        return

    now = time.time()
    if uid in last_play and now - last_play[uid] < COOLDOWN:
        client.replyMessage(Message(text="⏳ Chờ chút nữa"), message_object, thread_id, thread_type)
        return

    bet, _ = parse_bet(args[2], money.get(uid, 0))
    if bet <= 0 or bet > money.get(uid, 0):
        client.replyMessage(Message(text="❌ Tiền không hợp lệ"), message_object, thread_id, thread_type)
        return

    percent = update_price(uid, stock)
    win = (args[1] == "mua" and percent > 0) or (args[1] == "bán" and percent < 0)
    profit = int(bet * abs(percent) / 100)
    money[uid] = money.get(uid, 0) + (profit if win else -profit)

    save_money(money)
    save_stock(stock)
    last_play[uid] = now

    result = (
        "📈 KẾT QUẢ CHỨNG KHOÁN 📉\n"
        f"📊 Biến động: {percent:+d}%\n"
        f"💼 Vốn: {format_money(bet)}\n"
        f"{'🟢 LÃI' if win else '🔴 LỖ'} {format_money(profit)}"
    )

    client.replyMessage(Message(text=result), message_object, thread_id, thread_type)

# ================= REGISTER =================
def PTA():
    return {
        'ck': handle_ck,
        'chungkhoan': handle_ck
    }
