# modules/check.py
from zlapi.models import *
import platform
import psutil
import time
import datetime
import os
import sys

des = {
    'version': "1.0.0",
    'credits': "Hoàng Khánh Prime",
    'description': "xem thông tin ",
    'power': "Thành viên"
}

bot_name = "Hoàng Khánh Prime"
cre = "Hoàng Khánh Prime"
start_time = time.time()

def get_uptime():
    uptime_sec = int(time.time() - start_time)
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60
    seconds = uptime_sec % 60
    return f"{hours}h {minutes}m {seconds}s"

def get_system_info():
    return f"{platform.system()} {platform.release()} ({platform.version()})"

def get_cpu_info():
    cpu_name = platform.processor() or "Unknown CPU"
    cpu_cores = psutil.cpu_count(logical=False) or 1
    cpu_threads = psutil.cpu_count(logical=True) or 1
    cpu_usage = psutil.cpu_percent(interval=0.1)
    return f"{cpu_name}\n📊 Cores: {cpu_cores} | Threads: {cpu_threads} | Usage: {cpu_usage}%"

def get_ram_info():
    mem = psutil.virtual_memory()
    return {"total": round(mem.total/1024**3,2), "used": round(mem.used/1024**3,2), "available": round(mem.available/1024**3,2), "percent": mem.percent}

def get_swap_info():
    swap = psutil.swap_memory()
    return {"total": round(swap.total/1024**3,2), "used": round(swap.used/1024**3,2), "free": round(swap.free/1024**3,2)}

def get_disk_info():
    disk_path = '/data' if 'TERMUX_VERSION' in os.environ else '/'
    disk = psutil.disk_usage(disk_path)
    return f"💿 {disk_path}: {round(disk.used/1024**3,2)}/{round(disk.total/1024**3,2)} GB ({disk.percent}%) - Free: {round(disk.free/1024**3,2)} GB"

def get_process_info():
    process = psutil.Process(os.getpid())
    return f"PID: {process.pid} | RAM: {round(process.memory_info().rss/1024**2,2)}MB | CPU: {process.cpu_percent(interval=0.1)}%"

def get_python_info():
    return f"CPython {platform.python_version()}"

def get_app_info():
    if 'TERMUX_VERSION' in os.environ:
        return "Termux"
    return "Windows Terminal/CMD/PowerShell"

def handle_check_command(message, message_object, thread_id, thread_type, author_id, client):
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    ram_info = get_ram_info()
    swap_info = get_swap_info()
    content = f"""[ THÔNG TIN BOT ]
⏰ Thời gian: {date_str} {time_str}
⏱️ Uptime: {get_uptime()}

🖥️ HỆ THỐNG: {get_system_info()}
💻 CPU: {get_cpu_info()}
💾 STORAGE: {get_disk_info()}
📊 RAM: {ram_info['used']}/{ram_info['total']} GB ({ram_info['percent']}%)
💫 SWAP: {swap_info['used']}/{swap_info['total']} GB
🐍 Python: {get_python_info()} | Chạy trên: {get_app_info()}
🚀 Process: {get_process_info()}
👑 Admin: {bot_name}
🎨 Creator: {cre}"""
    client.replyMessage(Message(text=content), message_object, thread_id, thread_type)

# Hàm xuất ra kiểu TQuan
def PTA():
    return {
        'check': handle_check_command
    }
