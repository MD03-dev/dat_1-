# config.example.py
# Copy file này thành config.py rồi điền giá trị thật vào.
# KHÔNG commit file config.py lên git.

import json

def read_setting_value(key):
    try:
        with open('seting.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get(key)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file seting.json. Sử dụng giá trị mặc định cho {key}.")
        return None
    except json.JSONDecodeError:
        print(f"Lỗi: File seting.json không hợp lệ. Sử dụng giá trị mặc định cho {key}.")
        return None

def read_prefix():
    return read_setting_value('prefix') or "?"

def read_admin():
    return read_setting_value('admin') or "YOUR_ADMIN_ID"

# ===== ĐIỀN GIÁ TRỊ THẬT VÀO ĐÂY =====
IMEI = "your-imei-uuid-here"

SESSION_COOKIES = {
    "nl_b04af40bb0e193acf8a9877592394ada": "your_value",
    "zpdid": "your_value",
    "zlogin_session": "your_value",
    "_zlang": "vn",
    "zpsid": "your_value",
    "__zi": "your_value",
    "zpw_sek": "your_value"
}

HEADER_STYLE = "Tên Bot Của Bạn"
API_KEY = "your_api_key"
SECRET_KEY = "your_secret_key"

ADMIN = read_admin()
ADM = read_admin()
PREFIX = read_prefix()

GEMINI_API_KEY = "your_gemini_api_key"
