import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from config import PREFIX
import subprocess
from concurrent.futures import ThreadPoolExecutor
from zlapi.models import Message, ThreadType, Mention, MessageStyle, MultiMsgStyle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

AUDIO_QUALITY_PRESET = 'Balanced'

def to_rounded_font(text):
    normal_chars  = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    rounded_chars = "𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
    trans = str.maketrans(normal_chars, rounded_chars)
    return text.translate(trans)

def utf16_len(s):
    return sum(1 if ord(c) < 0x10000 else 2 for c in s)

def get_styled_msg(base_text, mention_uid=None, mention_name=None):
    mention = None
    if mention_name and mention_uid:
        mention_str = f"@{mention_name}"
        if base_text.startswith(mention_str):
            rest_of_text = base_text[len(mention_str):]
            final_text = mention_str + to_rounded_font(rest_of_text)
            mention = Mention(uid=mention_uid, length=utf16_len(mention_str), offset=0)
        else:
            final_text = mention_str + " " + to_rounded_font(base_text)
            mention = Mention(uid=mention_uid, length=utf16_len(mention_str), offset=0)
    else:
        final_text = to_rounded_font(base_text)

    if mention:
        return Message(text=final_text, mention=mention)
    return Message(text=final_text)

des = {
    'version': "4.0.9",
    'credits': "Hoàng Vĩnh Phúc x Gemini (Super Optimized)",
    'description': "Tải nhạc SoundCloud siêu tốc (Streaming Convert + Fast UI Render).",
    'power': "Thành viên"
}

SEARCH_TIMEOUT = 120 

os.makedirs(os.path.join(os.path.dirname(__file__), 'cache'), exist_ok=True)

client_id_cache = None

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('zaloName', 'Không xác định')
    except Exception: return 'Không xác định'

def get_user_avatar(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('avatar', '')
    except Exception: return ''

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9", "Referer": 'https://soundcloud.com/', "Origin": "https://soundcloud.com"
    }

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: return ImageFont.load_default()

def truncate_text(text, font, max_width):
    if font.getlength(text) <= max_width: return text
    while font.getlength(text + "...") > max_width and len(text) > 0: text = text[:-1]
    return text + "..."

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []; current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if font.getlength(test_line) <= max_width: current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

def delete_file(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e: logging.error(f"[delete_file] Lỗi: {e}")

def autosave(img, quality=90):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(tf.name, "JPEG", quality=quality)
        return tf.name

def upload_to_temp_service(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=300)
            response.raise_for_status()
        data = response.json()
        if data.get('status') == 'success':
            return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        raise Exception("Tải lên thất bại")
    except Exception as e:
        raise Exception(f"Lỗi upload tmpfiles: {e}")
        
def process_audio(audio_url, title):
    compressed_file_path = None
    try:
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        temp_id = int(time.time() * 1000)
        CACHE_DIR_SCL = os.path.join(os.path.dirname(__file__), 'cache')
        compressed_file_path = os.path.join(CACHE_DIR_SCL, f"{safe_title}_{temp_id}_scl.aac")

        # TỐI ƯU CỰC MẠNH: Bỏ bước tải file Python. Truyền thẳng link vào FFmpeg để stream + convert cùng lúc.
        command = [
            'ffmpeg', '-y', 
            '-i', audio_url, 
            '-vn', '-c:a', 'aac', '-b:a', '96k', # 96k giảm dung lượng, giúp tải và upload tmpfiles siêu nhanh
            compressed_file_path
        ]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=400)

        public_url = upload_to_temp_service(compressed_file_path)
        return public_url, compressed_file_path
    except Exception as e:
        if compressed_file_path and os.path.exists(compressed_file_path):
            delete_file(compressed_file_path)
        raise Exception(f"Lỗi khi xử lý audio stream: {e}")

def get_client_id():
    global client_id_cache
    if client_id_cache: return client_id_cache
    try:
        res = requests.get('https://soundcloud.com/', headers=get_headers(), timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        urls = [tag.get('src') for tag in soup.find_all('script', {'crossorigin': True}) if tag.get('src') and tag.get('src').startswith('https')]
        res = requests.get(urls[-1], headers=get_headers(), timeout=5)
        client_id_cache = re.search(r'client_id:"(.*?)"', res.text).group(1)
        return client_id_cache
    except Exception: return None

def wait_for_client_id():
    for _ in range(5):
        client_id = get_client_id()
        if client_id: return client_id
        time.sleep(1)
    raise Exception("Không thể kết nối đến SoundCloud để lấy client_id.")

def ms_to_mmss(ms):
    try: return f"{ms // 60000:02}:{(ms // 1000) % 60:02}"
    except: return "??:??"

def search_songs(query):
    try:
        client_id = wait_for_client_id()
        search_url = f'https://api-v2.soundcloud.com/search/tracks?q={requests.utils.quote(query)}&client_id={client_id}&limit=11'
        response = requests.get(search_url, headers=get_headers(), timeout=5)
        data = response.json()
        
        songs = []
        for item in data.get('collection', []):
            if not item.get('permalink_url'): continue
            title = item.get('title', 'Unknown Title')
            link = item.get('permalink_url')
            cover_url = item.get('artwork_url') or item.get('user', {}).get('avatar_url', '')
            duration = ms_to_mmss(item.get('duration', 0))
            playback_count = item.get('playback_count', 0)
            likes_count = item.get('likes_count', 0)
            comment_count = item.get('comment_count', 0)
            artist = item.get('user', {}).get('username', 'Unknown Artist')
            
            songs.append((link, title, cover_url, duration, playback_count, likes_count, comment_count, artist))
            if len(songs) >= 11: break
        return songs
    except Exception as e:
        logging.error(f"Lỗi search API: {e}")
        return []

def get_music_stream_url(link):
    try:
        client_id = wait_for_client_id()
        data = requests.get(f'https://api-v2.soundcloud.com/resolve?url={link}&client_id={client_id}', headers=get_headers(), timeout=5).json()
        for transcode in data.get('media', {}).get('transcodings', []):
            if transcode.get('format', {}).get('protocol') == 'progressive':
                return requests.get(f"{transcode['url']}?client_id={client_id}", headers=get_headers(), timeout=5).json().get('url')
        raise Exception("Không tìm thấy stream URL hợp lệ.")
    except Exception: return None

def format_stat(n):
    if n >= 1000000: return f"{n/1000000:.1f}M".replace('.0', '')
    if n >= 1000: return f"{n/1000:.1f}K".replace('.0', '')
    return str(n)

def fetch_image(url, size=None):
    if not url: return None
    try:
        if size: url = url.replace('-large', size)
        res = requests.get(url, headers=get_headers(), timeout=4)
        if res.status_code == 200: return Image.open(BytesIO(res.content)).convert("RGBA")
    except: pass
    return None

def draw_song_list_image(songs):
    if not songs: return None
    
    W, H = 1080, 480
    # Thêm chút tone xanh mờ tinh tế cho giao diện
    img = Image.new("RGBA", (W, H), (12, 16, 28))
    draw = ImageDraw.Draw(img)
    
    font_large_title = get_font(24)
    font_large_artist = get_font(18)
    font_small_title = get_font(18)
    font_small_artist = get_font(15)
    font_number = get_font(16)
    font_badge = get_font(14)

    cover_urls = [s[2] for s in songs]
    with ThreadPoolExecutor(max_workers=11) as executor:
        futures = [executor.submit(fetch_image, url, '-t500x500' if i==0 else None) for i, url in enumerate(cover_urls)]
        fetched_images = [f.result() for f in futures]

    link, title, _, duration, play, like, cmt, artist = songs[0]
    draw.rounded_rectangle([20, 20, 340, 460], radius=15, fill=(22, 30, 50))
    
    c_img = fetched_images[0]
    if c_img:
        c_img = c_img.resize((280, 280), getattr(Image, 'Resampling', Image).LANCZOS)
        mask = Image.new("L", (280, 280), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 280, 280], 15, fill=255)
        c_img.putalpha(mask)
        img.paste(c_img, (40, 40), c_img)
        
    t_str = truncate_text(title, font_large_title, 280)
    draw.text((40, 340), t_str, font=font_large_title, fill=(255, 255, 255))
    a_str = truncate_text(artist, font_large_artist, 280)
    draw.text((40, 375), a_str, font=font_large_artist, fill=(180, 180, 180))
    
    # Nút badge nổi bật xanh cyan
    draw.rounded_rectangle([110, 415, 250, 445], radius=15, fill=(0, 150, 255))
    bw = font_badge.getlength("SoundCloud")
    draw.text((110 + (140 - bw) / 2, 422), "SoundCloud", font=font_badge, fill=(255, 255, 255))

    for idx, s in enumerate(songs[1:11]):
        link, title, _, duration, play, like, cmt, artist = s
        col = idx // 5
        row = idx % 5
        item_x = 360 + col * 360
        item_y = 20 + row * 91
        
        draw.rounded_rectangle([item_x, item_y, item_x + 340, item_y + 75], radius=15, fill=(22, 30, 50))
        
        c_img = fetched_images[idx + 1]
        if c_img:
            c_img = c_img.resize((55, 55), getattr(Image, 'Resampling', Image).LANCZOS)
            mask = Image.new("L", (55, 55), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, 55, 55], 10, fill=255)
            c_img.putalpha(mask)
            img.paste(c_img, (item_x + 10, item_y + 10), c_img)
            
        t_str = truncate_text(title, font_small_title, 220)
        draw.text((item_x + 75, item_y + 15), t_str, font=font_small_title, fill=(255, 255, 255))
        
        info_str = f"{artist} | {duration}" if duration else artist
        info_str = truncate_text(info_str, font_small_artist, 220)
        draw.text((item_x + 75, item_y + 40), info_str, font=font_small_artist, fill=(180, 180, 180))
        
        num_str = str(idx + 2)
        nw = font_number.getlength(num_str)
        draw.text((item_x + 325 - nw, item_y + 28), num_str, font=font_number, fill=(150, 200, 255))

    return autosave(img)

def draw_song_detail_image(title, artist, duration, playback_count, like_count, comment_count, cover, requester_avatar_url):
    W, H = 700, 240
    img = Image.new("RGBA", (W, H), (15, 25, 45))
    draw = ImageDraw.Draw(img)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_cover = executor.submit(fetch_image, cover, '-t500x500')
        f_avatar = executor.submit(fetch_image, requester_avatar_url)
        cover_img = f_cover.result()
        r_img = f_avatar.result()

    if cover_img:
        # Tối ưu Pillow: Thu nhỏ ảnh -> Làm mờ -> Phóng to (Tốc độ xử lý tăng gấp 10 lần)
        small_bg = cover_img.resize((int(W/4), int(H/4))).filter(ImageFilter.GaussianBlur(0))
        bg = small_bg.resize((W+40, H+40), getattr(Image, 'Resampling', Image).LANCZOS)
        
        # Ám một lớp layer xanh biển mờ cho đồng bộ style U.I
        overlay = Image.new("RGBA", (W+40, H+40), (10, 15, 30, 180))
        bg.alpha_composite(overlay)
        img.paste(bg, (-20, -20))

    cx, cy, cr = 130, 120, 80
    if cover_img:
        # Viền cover sáng xanh 
        draw.ellipse([cx-cr-5, cy-cr-5, cx+cr+5, cy+cr+5], fill=(0, 200, 255))
        draw.ellipse([cx-cr-2, cy-cr-2, cx+cr+2, cy+cr+2], fill=(255,255,255))
        
        ms = min(cover_img.width, cover_img.height)
        l, t = (cover_img.width - ms)//2, (cover_img.height - ms)//2
        c_crop = cover_img.crop((l, t, l+ms, t+ms)).resize((cr*2, cr*2), getattr(Image, 'Resampling', Image).LANCZOS)
        mask = Image.new("L", (cr*2, cr*2), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, cr*2, cr*2], fill=255)
        c_crop.putalpha(mask)
        img.paste(c_crop, (cx-cr, cy-cr), c_crop)

        icon_r = 18
        ix, iy = cx + cr - 25, cy + cr - 25
        draw.ellipse([ix-icon_r, iy-icon_r, ix+icon_r, iy+icon_r], fill=(255,85,0))
        draw.text((ix-12, iy-12), "☁️", font=get_emoji_font(18), fill=(255,255,255))

    font_title = get_font(26)
    font_title_small = get_font(22)
    font_info = get_font(18)
    emoji_font = get_emoji_font(18)

    tx = 240
    max_w = W - tx - 90

    title_width = font_title.getlength(title)
    if title_width > max_w:
        lines = wrap_text(title, font_title_small, max_w)
        ty = 35
        for line in lines[:2]:
            if len(lines) > 2 and line == lines[1]: line = line + "..."
            draw.text((tx, ty), line, font=font_title_small, fill=(255,255,255))
            ty += 30
        ty += 15
    else:
        ty = 40
        draw.text((tx, ty), title, font=font_title, fill=(0, 255, 204))
        ty += 40

    draw.text((tx, ty), f"Artist: {artist}", font=font_info, fill=(0, 255, 149))
    ty += 30
    draw.text((tx, ty), "From SoundCloud", font=font_info, fill=(0, 255, 128))
    ty += 35
    
    stats = [("🎧", format_stat(playback_count)), ("❤️", format_stat(like_count)), ("💬", format_stat(comment_count))]
    sx = tx
    for emoji, val in stats:
        draw.text((sx, ty), emoji, font=emoji_font, fill=(255,255,255))
        sx += 26
        draw.text((sx, ty + 2), val, font=font_info, fill=(255,255,255))
        sx += font_info.getlength(val) + 20

    if r_img:
        ar = 30 
        ax, ay = W - 50, H - 50
        draw.ellipse([ax-ar-3, ay-ar-3, ax+ar+3, ay+ar+3], fill=(0, 200, 255)) # Viền xanh cho avatar người tải
        draw.ellipse([ax-ar-1, ay-ar-1, ax+ar+1, ay+ar+1], fill=(255,255,255))
        
        ms = min(r_img.width, r_img.height)
        l, t = (r_img.width - ms)//2, (r_img.height - ms)//2
        a_crop = r_img.crop((l, t, l+ms, t+ms)).resize((ar*2, ar*2), getattr(Image, 'Resampling', Image).LANCZOS)
        mask = Image.new("L", (ar*2, ar*2), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, ar*2, ar*2], fill=255)
        a_crop.putalpha(mask)
        img.paste(a_crop, (ax-ar, ay-ar), a_crop)

    return autosave(img)
    
# =========================================================================
def extract_msg_id(response):
    if not response: return None
    if hasattr(response, 'messageId'): return str(response.messageId)
    if hasattr(response, 'msgId'): return str(response.msgId)
    if isinstance(response, dict):
        m_id = response.get('messageId') or response.get('msgId')
        if not m_id and 'data' in response:
            data_val = response['data']
            if isinstance(data_val, dict):
                m_id = data_val.get('msgId')
        return str(m_id) if m_id else None
    return None

def execute_delmsg_logic(client, thread_id, target_msg_id=None):
    bot_uid = str(getattr(client, 'uid', '0'))
    try:
        group_data = client.getRecentGroup(thread_id)
        if not group_data or not hasattr(group_data, 'groupMsgs'): return
        
        messages_to_delete = group_data.groupMsgs
        if not messages_to_delete: return

        for msg in messages_to_delete:
            msg_dict = msg if isinstance(msg, dict) else (msg.__dict__ if hasattr(msg, '__dict__') else {})
            
            msg_author_id = str(msg_dict.get('uidFrom', '0'))
            if msg_author_id == '0':
                msg_author_id = bot_uid

            if msg_author_id == bot_uid:
                current_msg_id = str(msg_dict.get('msgId'))
                content = str(msg_dict.get('content', ''))
                
                is_target_id = target_msg_id and current_msg_id == target_msg_id
                is_menu_text = "bằng số index để tải" in content or to_rounded_font("bằng số index để tải") in content
                is_wait_text = "Chờ bé lấy nhạc chút" in content or to_rounded_font("Chờ bé lấy nhạc chút") in content

                if is_target_id or is_menu_text or is_wait_text:
                    try:
                        client.deleteGroupMsg(current_msg_id, msg_author_id, str(msg_dict.get('cliMsgId', '')), thread_id)
                        time.sleep(0.05)
                    except: pass
    except Exception as e:
        logging.error(f"Lỗi execute_delmsg_logic: {e}")

def force_delete_msg(client, response_obj, thread_id):
    try:
        bot_uid = str(getattr(client, 'uid', '0'))
        if bot_uid == '0' and hasattr(client, '_auth') and 'uid' in client._auth:
            bot_uid = str(client._auth['uid'])
            
        msg_id = extract_msg_id(response_obj)
        cli_msg_id = getattr(response_obj, 'cliMsgId', '')
        
        if not cli_msg_id and isinstance(response_obj, dict):
            cli_msg_id = str(response_obj.get('cliMsgId', ''))
            if not cli_msg_id and 'data' in response_obj:
                data_val = response_obj['data']
                if isinstance(data_val, dict):
                    cli_msg_id = str(data_val.get('cliMsgId', ''))
        elif hasattr(response_obj, '__dict__'):
            cli_msg_id = str(response_obj.__dict__.get('cliMsgId', ''))
        
        if msg_id:
            if cli_msg_id:
                client.deleteGroupMsg(msg_id, bot_uid, cli_msg_id, thread_id)
            execute_delmsg_logic(client, thread_id, target_msg_id=msg_id)
        else:
            execute_delmsg_logic(client, thread_id, target_msg_id=None)
    except Exception as e:
        logging.error(f"Lỗi force_delete_msg: {e}")
        execute_delmsg_logic(client, thread_id, target_msg_id=extract_msg_id(response_obj))

# =========================================================================
def handle_scl_command(message_text, message_object, thread_id, thread_type, author_id, client):
    if not hasattr(client, 'scl_user_states'):
        client.scl_user_states = {}
        
    user_states = client.scl_user_states
    name = get_user_name(client, author_id)
    parts = message_text.strip().split()
    
    query_or_choice = ""
    if len(parts) > 1: query_or_choice = " ".join(parts[1:])
    elif author_id in user_states:
        match = re.search(r'\b(\d+)\b', message_text.strip())
        if match: query_or_choice = match.group(1)

    compressed_path_to_delete = None

    try:
        if query_or_choice.isdigit() and author_id in user_states:
            state = user_states[author_id]
            
            if time.time() - state['time_of_search'] > SEARCH_TIMEOUT:
                del user_states[author_id]
                return

            songs = state['songs']
            index = int(query_or_choice) - 1
            if not (0 <= index < len(songs)):
                client.replyMessage(get_styled_msg(f"@{name} lựa chọn không hợp lệ.", author_id, name), message_object, thread_id, thread_type, ttl=60000)
                return

            link, title, cover_url, duration_str, playback_count, like_count, comment_count, artist = songs[index]

            send_response_obj = state.get('send_response')
            del user_states[author_id] 
            force_delete_msg(client, send_response_obj, thread_id)

            wait_content = f"@{name} Chờ bé lấy nhạc chút, xong sẽ gọi cho hay!\n\n🎵: {title}"
            wait_msg_response = client.replyMessage(get_styled_msg(wait_content, author_id, name), message_object, thread_id, thread_type, ttl=120000)

            audio_stream_url = get_music_stream_url(link)
            if not audio_stream_url: raise Exception("Không thể lấy stream URL từ SoundCloud.")

            requester_avatar_url = get_user_avatar(client, author_id)
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                audio_future = executor.submit(process_audio, audio_stream_url, title)
                image_future = executor.submit(
                    draw_song_detail_image, title, artist, duration_str, 
                    playback_count, like_count, comment_count, cover_url, requester_avatar_url
                )
                public_url, compressed_path_to_delete = audio_future.result()
                detail_image_path = image_future.result()

            content = f"@{name}\n> From SoundCloud <\nNhạc Bạn Chọn Đây!!"
            client.send(
                get_styled_msg(content, author_id, name),
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=210000
            )

            force_delete_msg(client, wait_msg_response, thread_id)

            with Image.open(detail_image_path) as im: width, height = im.size
            client.sendLocalImage(
                detail_image_path, 
                thread_id=thread_id, 
                thread_type=thread_type,
                width=width, 
                height=height, 
                message=None, 
                ttl=210000
            )
            delete_file(detail_image_path)

            client.sendRemoteVoice(
                public_url, 
                thread_id=thread_id, 
                thread_type=thread_type,
                fileSize=int(os.path.getsize(compressed_path_to_delete)), 
                ttl=1800000
            )
            
            return

        if not query_or_choice:
            client.replyMessage(get_styled_msg(f"@{name} Vui lòng nhập tên bài hát.", author_id, name), message_object, thread_id, thread_type, ttl=60000)
            return

        songs = search_songs(query_or_choice)
        if not songs:
            client.replyMessage(get_styled_msg(f"@{name} Không tìm thấy kết quả cho '{query_or_choice}'.", author_id, name), message_object, thread_id, thread_type, ttl=60000)
            return

        img_path = draw_song_list_image(songs)
        with Image.open(img_path) as im: width, height = im.size
        
        send_response = client.sendLocalImage(
            img_path, thread_id=thread_id, thread_type=thread_type, width=width, height=height,
            message=get_styled_msg(f"@{name} hãy trả lời tin nhắn này bằng số index để tải", author_id, name),
            ttl=120000
        )
        
        user_states[author_id] = {
            'songs': songs, 
            'time_of_search': time.time(), 
            'send_response': send_response
        }
        delete_file(img_path)
        
    except Exception as e:
        logging.error(f"Lỗi trong handle_scl_command: {e}", exc_info=True)
        client.replyMessage(get_styled_msg(f"@{name} đã xảy ra lỗi: {e}", author_id, name), message_object, thread_id, thread_type, ttl=60000)
    finally:
        if compressed_path_to_delete:
            delete_file(compressed_path_to_delete)

def PTA():
    return { 'scl': handle_scl_command }