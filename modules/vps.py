import os
import uuid
import json
import random
import string
import time
import threading
from zlapi.models import Message
from zlapi import ThreadType

des = {
    'version': "VIP 4.0 - FIXED",
    'credits': "Nguyễn Gia Hưng (edited)",
    'description': "VPS giả lập xịn, interactive, full lệnh, VIP 4.0 - optimized",
    'power': "Admin/Member"
}

ADMIN_UID = "849987440929228204"
VPS_FILE = "vps_data.json"

# sessions: str(author_id) -> { vps_code: session_data }
sessions = {}

vps_data_lock = threading.Lock()

# --- Load / Save VPS data (thread-safe) ---
if os.path.exists(VPS_FILE):
    try:
        with open(VPS_FILE, "r") as f:
            vps_data = json.load(f)
    except Exception:
        vps_data = {}
else:
    vps_data = {}


def save_vps_data():
    with vps_data_lock:
        with open(VPS_FILE, "w") as f:
            json.dump(vps_data, f, indent=2, ensure_ascii=False)


def load_vps_data():
    global vps_data
    with vps_data_lock:
        if os.path.exists(VPS_FILE):
            try:
                with open(VPS_FILE, "r") as f:
                    vps_data = json.load(f)
            except Exception:
                vps_data = {}
        else:
            vps_data = {}

# --- Utils ---

def random_code():
    # ensure unique code
    for _ in range(10):
        code = ''.join(random.choices(string.ascii_uppercase, k=3)) + ''.join(random.choices(string.digits, k=2))
        with vps_data_lock:
            if code not in vps_data:
                return code
    # fallback to uuid fragment
    return uuid.uuid4().hex[:5].upper()


def fake_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"


def fake_os():
    return random.choice(["Ubuntu 22.04", "Debian 12", "CentOS 8", "Fedora 38", "Alpine 3.18"])


def _format_time(ts):
    if not ts:
        return "Không giới hạn"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except Exception:
        return str(ts)


def fake_shell_output(cmd, session):
    # session: {cwd, fs, login_time, history}
    fs = session.get("fs", {"/": ["home", "var", "tmp"]})
    current = session.get("cwd", "/")
    cmd = cmd.strip()
    if not cmd:
        return ""
    session.setdefault("history", []).append(cmd)
    parts = cmd.split()
    base = parts[0]

    if base == "pwd":
        return current
    elif base == "ls":
        return "  ".join(fs.get(current, []))
    elif base == "cd":
        if len(parts) < 2:
            return "Bạn phải nhập thư mục"
        dest = parts[1]
        if dest == "..":
            if current != "/":
                current = "/".join(current.rstrip("/").split("/")[:-1]) or "/"
        else:
            if dest.startswith("/"):
                target = dest
            else:
                target = current.rstrip("/") + "/" + dest if current != "/" else "/" + dest
            if target in fs:
                current = target
            else:
                return f"Thư mục {dest} không tồn tại"
        session["cwd"] = current
        return ""
    elif base == "mkdir":
        if len(parts) < 2:
            return "Bạn phải nhập tên thư mục"
        newdir = current.rstrip("/") + "/" + parts[1] if current != "/" else "/" + parts[1]
        if newdir in fs:
            return "Thư mục đã tồn tại"
        fs[newdir] = []
        session["fs"] = fs
        return f"Tạo thư mục {parts[1]} thành công"
    elif base == "cat":
        return "Fake file content: đây là nội dung giả lập."
    elif base == "status":
        cpu = random.randint(1, 100)
        ram = random.randint(1, 100)
        return f"CPU Usage: {cpu}%\nRAM Usage: {ram}%"
    elif base == "history":
        hist = session.get("history", [])
        return "\n".join(f"{i+1}. {h}" for i, h in enumerate(hist)) if hist else "Không có lịch sử"
    else:
        return f"Lệnh không hợp lệ: {cmd}"


# --- VPS Commands ---

def handle_vps_command(message, message_object, thread_id, thread_type, author_id, client):
    global sessions, vps_data

    # normalize author id to str for keys
    author_id = str(author_id)

    # reload latest data to avoid stale read (cheap, safe)
    load_vps_data()

    # --- Auto-expiry check: khóa VPS đã hết hạn ---
    now = time.time()
    changed = False
    with vps_data_lock:
        for code, v in list(vps_data.items()):
            if v.get("expires") and v["expires"] != None and now > v["expires"]:
                if not v.get("locked", False):
                    v["locked"] = True
                    changed = True
    if changed:
        save_vps_data()

    parts = message.strip().split()
    args = parts[1:]

    if not args:
        reply = "📌 Lệnh VPS:\n"
        reply += ".vps create <tên VPS>\n.vps list\n.vps my\n.vps duyet <mã>\n.vps lock <mã>\n.vps unlock <mã>\n.vps giahan <mã> <thời gian>\n.vps info <mã>\n.vps login <mã> <pass>\n.vps logout [<mã>]\n(Trong session shell: cd, ls, pwd, mkdir, cat, status, history)\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    cmd = args[0].lower()

    # --- CREATE VPS ---
    if cmd == "create":
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Vui lòng nhập tên VPS."), thread_id, thread_type)
            return
        vps_name = args[1]
        code = random_code()
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        vps = {
            "name": vps_name,
            "code": code,
            "password": password,
            "owner": author_id,
            "locked": False,
            "expires": None,
            "cpu": f"{random.randint(1,8)} vCPU",
            "ram": f"{random.randint(2,32)} GB",
            "disk": f"{random.randint(20,500)} GB",
            "os": fake_os(),
            "ip": fake_ip(),
            "created": time.time()
        }
        with vps_data_lock:
            vps_data[code] = vps
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {vps_name} đã tạo!\nMã: {code}\nMật khẩu: {password}"), thread_id, thread_type)
        return

    # --- LIST VPS ---
    if cmd == "list":
        with vps_data_lock:
            if not vps_data:
                client.sendMessage(Message(text="📄 Không có VPS nào."), thread_id, thread_type)
                return
            reply = "📄 Danh sách VPS đang hoạt động:\n"
            for v in vps_data.values():
                reply += f"- {v['name']} ({v['code']}) | Owner: {v['owner']} | Locked: {v['locked']} | Expires: {_format_time(v.get('expires'))}\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- MY VPS ---
    if cmd == "my":
        reply = f"📦 VPS của bạn ({author_id}):\n"
        found = False
        with vps_data_lock:
            for v in vps_data.values():
                if v.get("owner") == author_id:
                    reply += f"- {v['name']} ({v['code']}) | Locked: {v['locked']} | Expires: {_format_time(v.get('expires'))}\n"
                    found = True
        if not found:
            reply += "Bạn chưa có VPS nào."
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- DUYET VPS (admin) ---
    if cmd == "duyet":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần duyệt"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = False
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được duyệt, có thể sử dụng"), thread_id, thread_type)
        return

    # --- LOCK VPS (admin) ---
    if cmd == "lock":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần khóa"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = True
            save_vps_data()
        client.sendMessage(Message(text=f"🔒 VPS {code} đã bị khóa"), thread_id, thread_type)
        return

    # --- UNLOCK VPS (admin) ---
    if cmd == "unlock":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần mở khóa"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = False
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được mở khóa"), thread_id, thread_type)
        return

    # --- GIA HẠN VPS (admin) ---
    if cmd == "giahan":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 3:
            client.sendMessage(Message(text="❌ Sử dụng: .vps giahan <mã> <10s/5m/1h/1d>"), thread_id, thread_type)
            return
        code = args[1]
        t = args[2]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            now = time.time()
            sec = 0
            try:
                if t.endswith("s"):
                    sec = int(t[:-1])
                elif t.endswith("m"):
                    sec = int(t[:-1]) * 60
                elif t.endswith("h"):
                    sec = int(t[:-1]) * 3600
                elif t.endswith("d"):
                    sec = int(t[:-1]) * 86400
                else:
                    sec = int(t)
            except Exception:
                client.sendMessage(Message(text="❌ Thời gian không hợp lệ."), thread_id, thread_type)
                return
            vps_data[code]["expires"] = now + sec
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được gia hạn thêm {t}. Hết hạn: {_format_time(vps_data[code].get('expires'))}"), thread_id, thread_type)
        return

    # --- INFO VPS ---
    if cmd == "info":
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần xem"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            v = vps_data[code]
            if author_id == ADMIN_UID:
                reply = f"📊 Info VPS {code} (Admin view):\n"
                for k, val in v.items():
                    if k == "expires":
                        reply += f"{k}: {_format_time(val)}\n"
                    else:
                        reply += f"{k}: {val}\n"
            else:
                reply = f"📊 Info VPS {code}:\nName: {v['name']}\nCode: {v['code']}\nOwner: {v['owner']}\nLocked: {v['locked']}\nExpires: {_format_time(v.get('expires'))}\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- LOGIN VPS ---
    if cmd == "login":
        if len(args) < 3:
            client.sendMessage(Message(text="❌ Sử dụng: .vps login <mã> <pass>"), thread_id, thread_type)
            return
        code = args[1]
        password = args[2]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            v = vps_data[code]
            if v.get("locked"):
                client.sendMessage(Message(text="❌ VPS đang bị khóa"), thread_id, thread_type)
                return
            if v.get("password") != password:
                client.sendMessage(Message(text="❌ Sai mật khẩu VPS"), thread_id, thread_type)
                return
        # tạo session cho user -> nhiều VPS cùng lúc được
        sessions.setdefault(author_id, {})
        sessions[author_id][code] = {"cwd": "/", "fs":{"/": ["home", "var", "tmp"]}, "login_time": time.time(), "history": []}
        client.sendMessage(Message(text=f"✅ Đăng nhập thành công VPS {code}. Bạn có thể dùng lệnh giả lập shell: cd, ls, pwd, mkdir, cat, status, history\nĐể thoát: .vps logout {code}"), thread_id, thread_type)
        return

    # --- LOGOUT VPS ---
    if cmd == "logout":
        # optional .vps logout <code> to logout a specific VPS
        if len(args) >= 2:
            code = args[1]
            if author_id in sessions and code in sessions[author_id]:
                del sessions[author_id][code]
                if not sessions[author_id]:
                    del sessions[author_id]
                client.sendMessage(Message(text=f"✅ Đã thoát VPS {code}."), thread_id, thread_type)
            else:
                client.sendMessage(Message(text="⚠️ Bạn chưa login VPS này."), thread_id, thread_type)
            return
        # otherwise logout from all or first session
        if author_id in sessions:
            del sessions[author_id]
            client.sendMessage(Message(text="✅ Đã thoát khỏi tất cả VPS session."), thread_id, thread_type)
        else:
            client.sendMessage(Message(text="⚠️ Bạn không có session VPS nào đang hoạt động."), thread_id, thread_type)
        return

    # --- SHELL INTERACTIVE ---
    # nếu user đang login (ưu tiên VPS code nếu truyền vào lệnh: ".vps <shell command> <mã>" không áp dụng — shell chỉ nhận message thẳng sau khi login)
    user_sessions = sessions.get(author_id, {})
    if user_sessions:
        # lấy VPS đầu tiên đang login (giữ hành vi cũ), có thể nâng cấp để support chọn VPS hiện hành
        code = list(user_sessions.keys())[0]
        session = user_sessions[code]
        output = fake_shell_output(message, session)
        client.sendMessage(Message(text=f"💻 [{code}]: {output}"), thread_id, thread_type)
        return

    client.sendMessage(Message(text="❌ Lệnh không hợp lệ hoặc bạn chưa login VPS. Gõ .vps để xem hướng dẫn."), thread_id, thread_type)


# --- Export ---

def PTA():
    return {
        'vps': handle_vps_command
    }
