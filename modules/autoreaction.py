from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
import json
import os
import random
import logging
from config import ADMIN, PREFIX, HEADER_STYLE

logger = logging.getLogger("AutoreactModule")

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

des = {
    'version': "2.6.0",
    'credits': "Van Chien",
    'description': "Quản lý tự động thả cảm xúc (Bật/tắt cho nhóm hiện tại & Tuỳ chỉnh icon)",
    'power': "Admin"
}

ALLOWED_GROUPS_FILE = "data/autoreaction_settings.json"

def check_admin_permissions(author_id, thread_id, thread_type, client):
    """Kiểm tra quyền admin từ nhiều nguồn: client, seting.json và config.py"""
    author_id = str(author_id)
    
    # 1. Kiểm tra qua phương thức của client (nếu có)
    if hasattr(client, 'is_allowed_author') and client.is_allowed_author(author_id):
        return True

    # 2. Kiểm tra trong file cấu hình seting.json
    try:
        if os.path.exists('seting.json'):
            with open('seting.json', 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
            admin_id = str(current_settings.get('admin', ''))
            adm_list = [str(uid) for uid in current_settings.get('adm', [])]
            
            if author_id == admin_id or author_id in adm_list:
                return True
    except Exception as e:
        logger.error(f"[AUTOREACT] Lỗi đọc seting.json: {e}")

    # 3. Kiểm tra trong config.ADMIN
    if isinstance(ADMIN, list):
        if author_id in [str(uid) for uid in ADMIN]:
            return True
    elif author_id == str(ADMIN):
        return True
        
    return False

def load_settings():
    try:
        if os.path.exists(ALLOWED_GROUPS_FILE):
            with open(ALLOWED_GROUPS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"groups": data, "icons": {}}
                if not isinstance(data, dict):
                    return {"groups": [], "icons": {}}
                if "groups" not in data:
                    data["groups"] = []
                if "icons" not in data:
                    data["icons"] = {}
                return data
    except Exception:
        pass
    return {"groups": [], "icons": {}}

def save_settings(data):
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
        with open(ALLOWED_GROUPS_FILE, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

def get_group_name(client, gid):
    try:
        info = client.fetchGroupInfo(gid)
        # Kiểm tra nếu info là string thì parse sang dict
        if isinstance(info, str):
            info = json.loads(info)
            
        if info and hasattr(info, 'gridInfoMap'):
            grid_map = info.gridInfoMap
            # Kiểm tra grid_map có phải dict không
            if isinstance(grid_map, dict):
                group_data = grid_map.get(str(gid), {})
                return group_data.get('name', 'Không xác định')
        elif isinstance(info, dict):
            return info.get('name', 'Không xác định')
    except Exception as e:
        logger.error(f"Lỗi lấy tên nhóm: {e}")
    return "Không xác định"

def get_all_group_ids(client):
    try:
        groups_data = client.fetchAllGroups()
        if groups_data and hasattr(groups_data, 'gridVerMap'):
            return list(groups_data.gridVerMap.keys())
        return []
    except Exception as e:
        logger.error(f"[AUTOREACT] Lỗi khi lấy danh sách nhóm: {e}")
        return []

def auto_clean_dead_groups(client, settings):
    try:
        allowed_groups = settings.get("groups", [])
        current_gids = [str(gid) for gid in get_all_group_ids(client)]
        if not current_gids:
            return settings 
            
        cleaned_groups = []
        removed_count = 0
        
        for gid in allowed_groups:
            if gid in current_gids:
                cleaned_groups.append(gid)
            else:
                removed_count += 1
                if gid in settings.get("icons", {}):
                    del settings["icons"][gid]
                logger.info(f"[!] Dọn dẹp: Đã tự động xoá UID {gid} do bot không còn trong nhóm.")
        
        if removed_count > 0:
            settings["groups"] = cleaned_groups
            save_settings(settings)
            
        return settings
    except Exception as e:
        logger.error(f"Lỗi dọn dẹp thụ động: {e}")
    
    return settings

def remove_uid_on_leave(group_id):
    try:
        gid_str = str(group_id)
        settings = load_settings()
        allowed_groups = settings.get("groups", [])
        
        if gid_str in allowed_groups:
            allowed_groups.remove(gid_str)
            if gid_str in settings.get("icons", {}):
                del settings["icons"][gid_str]
                
            settings["groups"] = allowed_groups
            save_settings(settings)
            logger.info(f"[ACTIVE] Bot đã rời nhóm {gid_str}. Xoá thành công khỏi data!")
            return True
    except Exception as e:
        logger.error(f"Lỗi khi tự động xoá UID {group_id}: {e}")
    return False

def reply_msg(client, message_object, thread_id, thread_type, author_id, text_content, ttl=15000):
    """Hàm gửi tin nhắn hỗ trợ style Zlapi: Giữ màu cho Header, không áp dụng style cho nội dung text thông báo"""
    header = str(HEADER_STYLE) if HEADER_STYLE else ""
    
    if thread_type == ThreadType.USER:
        full_msg = f"{header}\n{text_content}" if header else text_content
        mention = None
        style_list = []
        
        if header:
            # Giữ nguyên style màu đỏ, in đậm cho HEADER
            style_list.extend([
                MessageStyle(offset=0, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="font", size=18, auto_format=False)
            ])
            
        styles = MultiMsgStyle(style_list) if style_list else None
    else:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and hasattr(user_info, 'changed_profiles') else {}
        name = author_info.get('zaloName', 'Thành viên')
        
        tag_text = f"@{name}"
        full_msg = f"{tag_text}\n{header}\n{text_content}" if header else f"{tag_text}\n{text_content}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))
        
        style_list = []
        offset_header = len(tag_text) + 1
        
        if header:
            # Giữ nguyên style màu đỏ, in đậm cho HEADER
            style_list.extend([
                MessageStyle(offset=offset_header, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="font", size=18, auto_format=False)
            ])
            
        styles = MultiMsgStyle(style_list) if style_list else None
    
    try:
        client.replyMessage(Message(text=full_msg, style=styles, mention=mention),
                               message_object, thread_id=thread_id, thread_type=thread_type, ttl=ttl)
    except Exception:
        try:
            client.sendMessage(Message(text=full_msg, style=styles, mention=mention), thread_id, thread_type)
        except Exception:
            pass

def handle_autoreact_command(message, message_object, thread_id, thread_type, author_id, client):
    """Lệnh xử lý quản lý tính năng autoreact"""
    
    # SỬ DỤNG HÀM KIỂM TRA QUYỀN NÂNG CAO TẠI ĐÂY
    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        reply_msg(client, message_object, thread_id, thread_type, author_id, 
                  "Bạn không đủ quyền hạn để sử dụng lệnh này!\nYêu Cầu: Quản Trị Bot\n🚫🚫🚫", ttl=5000)
        return

    command_parts = message.split()
    
    if len(command_parts) < 2:
        rest_text = (
            f"Hướng dẫn sử dụng lệnh auto reaction:\n"
            f"• {PREFIX}autoreact on: Bật cho nhóm hiện tại.\n"
            f"• {PREFIX}autoreact on <uid>: Bật cho nhóm theo UID.\n"
            f"• {PREFIX}autoreact on all: Bật cho tất cả các nhóm.\n"
            f"• {PREFIX}autoreact off: Tắt cho nhóm này.\n"
            f"• {PREFIX}autoreact off all: Tắt toàn bộ ở cả các nhóm.\n"
            f"• {PREFIX}autoreact icon <icon>: Đổi icon reaction cho nhóm này.\n"
            f"• {PREFIX}autoreact icon reset: Dùng lại random 3 icon mặc định.\n"
            f"• {PREFIX}autoreact list <trang>: Xem danh sách nhóm.\n"
            f"• {PREFIX}autoreact remove <số/all>: Xoá nhóm khỏi danh sách."
        )
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=30000)
        return

    action = command_parts[1].lower()
    settings = load_settings()
    allowed_groups = settings.get("groups", [])
    icons = settings.get("icons", {})
    rest_text = ""
    gid_str = str(thread_id)

    if action in ["on", "enable", "1"]:
        if len(command_parts) >= 3:
            target = command_parts[2].lower()
            if target == "all":
                all_gids = get_all_group_ids(client)
                if not all_gids:
                    rest_text = "Không thể lấy danh sách nhóm từ API hoặc bot chưa tham gia nhóm nào! ❌"
                    reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
                    return
                else:
                    for gid in all_gids:
                        if str(gid) not in allowed_groups:
                            allowed_groups.append(str(gid))
                    settings["groups"] = allowed_groups
                    save_settings(settings)
                    logger.info(f"Đã kích hoạt autoreact cho toàn bộ {len(all_gids)} nhóm.")
                    rest_text = f"Đã bật tự động thả cảm xúc cho {len(all_gids)} nhóm\n✅✅✅"
            else:
                # Bật cho 1 UID cụ thể
                target_uid = command_parts[2]
                if target_uid not in allowed_groups:
                    allowed_groups.append(target_uid)
                    settings["groups"] = allowed_groups
                    save_settings(settings)
                rest_text = f"Đã bật tự động thả cảm xúc cho nhóm có UID: {target_uid}\n✅✅✅"
        else:
            if gid_str not in allowed_groups:
                allowed_groups.append(gid_str)
                settings["groups"] = allowed_groups
                save_settings(settings)
            rest_text = "Đã bật tự động thả cảm xúc khi có người bị tag trong nhóm này!\n✅✅✅"

    elif action in ["off", "disable", "0"]:
        if len(command_parts) >= 3 and command_parts[2].lower() == "all":
            settings["groups"] = []
            settings["icons"] = {}
            save_settings(settings)
            logger.info("Đã tắt toàn bộ autoreact trên tất cả các nhóm.")
            rest_text = "Đã tắt tự động thả cảm xúc trên tất cả các nhóm!\n✅✅✅"
        else:
            if gid_str in allowed_groups:
                allowed_groups.remove(gid_str)
                settings["groups"] = allowed_groups
                save_settings(settings)
            rest_text = "Đã tắt tự động thả cảm xúc nhóm này!\n✅✅✅"

    elif action == "icon":
        if len(command_parts) >= 3:
            icon_arg = command_parts[2]
            if icon_arg.lower() == "reset":
                if gid_str in icons:
                    del icons[gid_str]
                    settings["icons"] = icons
                    save_settings(settings)
                rest_text = "Đã khôi phục danh sách icon ngẫu nhiên mặc định cho nhóm này!\n✅✅✅"
            else:
                icons[gid_str] = icon_arg
                settings["icons"] = icons
                save_settings(settings)
                rest_text = f"Đã thay đổi icon thả cảm xúc cho nhóm này thành: {icon_arg}\n✅✅✅"
        else:
            rest_text = f"Sử dụng lệnh: {PREFIX}autoreact icon <icon> hoặc {PREFIX}autoreact icon reset\n❌❌❌"
            reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
            return

    elif action == "list":
        settings = auto_clean_dead_groups(client, settings)
        allowed_groups = settings.get("groups", [])
        
        if not allowed_groups:
            rest_text = "Hiện chưa có nhóm nào được bật tính năng thả cảm xúc! 📭"
            reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
        else:
            chunk_size = 10
            page = 1
            if len(command_parts) >= 3 and command_parts[2].isdigit():
                page = int(command_parts[2])
                
            total_pages = (len(allowed_groups) + chunk_size - 1) // chunk_size
            
            if page < 1 or page > total_pages:
                reply_msg(client, message_object, thread_id, thread_type, author_id, f"Trang {page} không tồn tại. Chỉ có {total_pages} trang.", ttl=15000)
                return

            start_idx = (page - 1) * chunk_size
            end_idx = start_idx + chunk_size
            chunk = allowed_groups[start_idx:end_idx]
            
            chunk_text = f"📋 Danh sách nhóm đang bật Autoreact (Trang {page}/{total_pages}):\n\n"
            
            for i, gid in enumerate(chunk):
                gname = get_group_name(client, gid)
                global_index = start_idx + i + 1
                icon_set = icons.get(gid, "Ngẫu nhiên")
                chunk_text += f"{global_index}. {gname}\n ╰ UID: {gid} | Icon: {icon_set}\n"
            
            if total_pages > 1:
                chunk_text += f"\nDùng lệnh: {PREFIX}autoreact list <số trang> để xem tiếp"
            
            reply_msg(client, message_object, thread_id, thread_type, author_id, chunk_text, ttl=20000)
        return
    
    elif action == "remove":
        if len(command_parts) >= 3:
            target = command_parts[2].lower()
            if target == "all":
                settings["groups"] = []
                settings["icons"] = {}
                save_settings(settings)
                logger.info("Xoá toàn bộ danh sách autoreact thông qua lệnh remove all.")
                rest_text = "Đã xoá toàn bộ nhóm khỏi danh sách Autoreact thành công!\n✅✅✅"
            elif target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(allowed_groups):
                    removed_gid = allowed_groups[idx]
                    removed_name = get_group_name(client, removed_gid)
                    allowed_groups.pop(idx)
                    
                    if removed_gid in icons:
                        del icons[removed_gid]
                        
                    settings["groups"] = allowed_groups
                    settings["icons"] = icons
                    save_settings(settings)
                    
                    logger.info(f"Xoá UID {removed_gid} ({removed_name}) theo số thứ tự.")
                    rest_text = f"Đã xoá nhóm số {target} ({removed_name}) khỏi danh sách!\n✅✅✅"
                else:
                    rest_text = f"Số thứ tự {target} không tồn tại. Hãy dùng `{PREFIX}autoreact list` để xem lại!\n❌❌❌"
                    reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
                    return
            else:
                rest_text = "Tham số không hợp lệ. Vui lòng nhập số thứ tự hoặc 'all'!\n❌❌❌"
                reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
                return
        else:
            rest_text = f"Sử dụng lệnh: {PREFIX}autoreact remove <số thứ tự/all>\n❌❌❌"
            reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
            return

    else:
        rest_text = f"Lệnh không hợp lệ! Dùng {PREFIX}autoreact để xem hướng dẫn.\n❌❌❌"
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)
        return

    reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)

def check_and_react(client, message_object, thread_id, thread_type):
    """Hàm kiểm tra tin nhắn xem có ai bị tag không để thả reaction"""
    settings = load_settings()
    allowed_groups = settings.get("groups", [])
    icons = settings.get("icons", {})
    
    gid_str = str(thread_id)
    if gid_str not in allowed_groups:
        return

    if hasattr(message_object, 'mentions') and message_object.mentions and len(message_object.mentions) > 0:
        REACTIONS = [
            ":(", ":b", ";o", "8-)", ":)", ":~", ":b", ":')", "8-)", ":-((", ":", ":3", ":z", ":((", "&-(", ":p", ":d", ":o", ":(", ";-)", "--b", ":))", ":-*", ";p", ";-d", "/-showlove", ";d", ";o", ";g", "|-)", ":!", ":l", ":>", ":;", ";f", ":v", ":wipe", ":-dig", ":handclap", "b-)", ":-r", ":-<", ":-o", ";-s", ";?", ";-x", ":-f", "8*)", ";xx", ":-bye", ";!", ">-|", "p-(", ":--|", ":q", "x-)", ":*", ";-a", "8*", ":|", ":x", ":t", ";-/", ":-l", "-)", "/-strong", "/-shit"
        ]
        
        custom_icon = icons.get(gid_str)
        
        if custom_icon:
            try:
                client.sendReaction(message_object, custom_icon, thread_id, thread_type)
            except Exception:
                pass
        else:
            # Lấy ngẫu nhiên 3 icon KHÔNG TRÙNG LẶP để tránh tự ghi đè
            chosen_icons = random.sample(REACTIONS, 3)
            for reaction in chosen_icons:
                try:
                    client.sendReaction(message_object, reaction, thread_id, thread_type)
                except Exception:
                    pass

def PTA():
    return {
        'autoreact': handle_autoreact_command,
        'reaction': handle_autoreact_command
    }