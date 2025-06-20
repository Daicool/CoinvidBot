import json
import os
import uuid
from datetime import datetime, timedelta
import pytz

# Múi giờ Việt Nam (+07)
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def parse_duration(duration_str):
    """Chuyển đổi thời gian (1h, 1d, 7d) thành giây."""
    try:
        unit = duration_str[-1].lower()
        value = int(duration_str[:-1])
        if unit == "h":
            return value * 3600
        elif unit == "d":
            return value * 86400
        else:
            raise ValueError("Đơn vị thời gian không hợp lệ. Dùng 'h' (giờ) hoặc 'd' (ngày).")
    except (ValueError, IndexError):
        raise ValueError("Định dạng thời gian không hợp lệ. Ví dụ: 1h, 7d.")

def create_key(duration_str):
    """Tạo key mới với thời gian hết hạn."""
    try:
        seconds = parse_duration(duration_str)
        key = str(uuid.uuid4()).upper()[:12]  # Key dạng ABC123XYZ789
        expires_at = (datetime.now(VN_TZ) + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")
        keys = load_keys()
        keys[key] = {"expires_at": expires_at}
        save_keys(keys)
        return key, expires_at
    except Exception as e:
        return None, str(e)

def load_keys():
    """Đọc keys.json, trả về dict key."""
    try:
        if os.path.exists("keys.json"):
            with open("keys.json", "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys(keys):
    """Lưu keys vào keys.json."""
    try:
        with open("keys.json", "w") as f:
            json.dump(keys, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving keys: {e}")
        return False

def is_key_valid(key):
    """Kiểm tra key có hợp lệ và chưa hết hạn."""
    keys = load_keys()
    if key not in keys:
        return False, "Key không tồn tại."
    try:
        expires_at = datetime.strptime(keys[key]["expires_at"], "%Y-%m-%d %H:%M:%S")
        expires_at = VN_TZ.localize(expires_at)
        if datetime.now(VN_TZ) > expires_at:
            return False, "Key đã hết hạn."
        return True, "Key hợp lệ."
    except Exception as e:
        return False, f"Error checking key: {e}"

def list_keys():
    """Liệt kê tất cả key, thời gian hết hạn, và trạng thái."""
    keys = load_keys()
    if not keys:
        return "Không có key nào."
    result = "Danh sách key:\n"
    for i, (key, data) in enumerate(keys.items(), 1):
        expires_at = data["expires_at"]
        try:
            expires_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            expires_dt = VN_TZ.localize(expires_dt)
            status = "Hợp lệ" if datetime.now(VN_TZ) < expires_dt else "Hết hạn"
        except:
            status = "Lỗi định dạng"
        result += f"{i}. {key} - Hết hạn: {expires_at} ({status})\n"
    return result

def delete_key(key):
    """Xóa key khỏi keys.json."""
    keys = load_keys()
    if key not in keys:
        return False, "Key không tồn tại."
    del keys[key]
    if save_keys(keys):
        return True, f"Đã xóa key {key}."
    return False, "Lỗi khi xóa key."
