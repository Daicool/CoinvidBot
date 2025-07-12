import requests
import json
import time
import os
import csv
from datetime import datetime, timezone, timedelta
import random
import stem
from stem.control import Controller

# Khởi tạo session với Tor
session = requests.Session()
session.proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

# Thông tin API
API_URL = "https://m.coinvid.com/api/rocket-api/game/issue-result/page"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US",
    "Authorization": "Basic cm9ja2V0X3dlYjpyb2NrZXRfd2Vi",
    "Blade-Auth": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJpc3N1c2VyIiwiYXVkIjoiYXVkaWVuY2UiLCJ0ZW5hbnRfaWQiOiI2NzczNDMiLCJ1c2VyX25hbWUiOiJ2dW9uZ2RhaWN1dG85OTk5IiwidG9rZW5fdHlwZSI6ImFjY2Vzc190b2tlbiIsInJvbGVfbmFtZSI6IiIsInVzZXJfdHlwZSI6InJvY2tldCIsInVzZXJfaWQiOiIxNzgyNDA2NjIzODgyMTk0OTQ1IiwiZGV0YWlsIjp7ImF2YXRhciI6IjI4IiwidmlwTGV2ZWwiOjJ9LCJhY2NvdW50IjoidnVvbmdkYWljdXRvOTk5OSIsImNsaWVudF9pZCI6InJvY2tldF93ZWIiLCJleHAiOjE3NTA2NTQyNDAsIm5iZiI6MTc1MDA0OTQ0MH0.u24wAvp1vFPSfp5lPkohLgggSkCnbbegIukxA-5iHcLhb2KbEEELnQUQ-Bba7oOzpCCV4SZzVOfNy24GuABXsg",
    "Connection": "keep-alive",
    "Cookie": "JSESSIONID=SjdlkXQOe1u3eVkpk8KJHFPfAz2gbd5xi-2SmXfH",
    "Referer": "https://m.coinvid.com/openHistory?gameName=RG1M",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "user_type": "rocket"
}

# Thông tin API đăng nhập
LOGIN_URL = "https://m.coinvid.com/api/rocket-api/member/login"
LOGIN_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US",
    "Authorization": "Basic cm9ja2V0X3dlYjpyb2NrZXRfd2Vi",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://m.coinvid.com",
    "Referer": "https://m.coinvid.com/login?backUrl=%2FuserCenter",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "user_type": "rocket"
}
LOGIN_DATA = {
    "username": "vuongdaicuto9999",
    "password": "Hoangvuonglop5d@"  # Thay bằng mật khẩu thực tế
}

def load_token():
    """Đọc Blade-Auth token từ file token.json"""
    try:
        if os.path.exists("token.json"):
            with open("token.json", "r") as f:
                data = json.load(f)
                return data.get("access_token")
        return None
    except Exception as e:
        log_error_response({"error": str(e)}, "Error loading token")
        return None

def save_token(token):
    """Lưu Blade-Auth token vào file token.json"""
    try:
        with open("token.json", "w") as f:
            json.dump({"access_token": token}, f, indent=2)
    except Exception as e:
        log_error_response({"error": str(e)}, "Error saving token")

def refresh_token():
    """Gọi API đăng nhập để lấy Blade-Auth token mới"""
    try:
        response = session.post(LOGIN_URL, headers=LOGIN_HEADERS, data=LOGIN_DATA, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "access_token" in data["data"]:
                new_token = data["data"]["access_token"]
                save_token(new_token)
                HEADERS["Blade-Auth"] = new_token
                return new_token
        return None
    except requests.exceptions.RequestException as e:
        log_error_response({"error": str(e)}, "Login error")
        return None

def adjust_color(value, color):
    """Điều chỉnh màu theo trường hợp đặc biệt"""
    if value == "0" and color == "purple":
        return "red"
    if value == "5" and color == "purple":
        return "green"
    return color

def get_current_ip():
    """Lấy IP hiện tại qua Tor"""
    try:
        response = session.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        log_error_response({"error": str(e)}, "Error getting current IP")
        return None

def renew_tor_ip():
    """Đổi IP Tor bằng cách gửi NEWNYM signal và xác nhận IP mới"""
    try:
        old_ip = get_current_ip()
        if old_ip is None:
            return False

        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(stem.Signal.NEWNYM)
            time.sleep(10)  # Đợi 10 giây để đảm bảo IP mới được gán

        new_ip = get_current_ip()
        if new_ip is not None and new_ip != old_ip:
            print(f"Tor IP renewed from {old_ip} to {new_ip}")
            return True
        else:
            print("Failed to renew Tor IP")
            return False
    except Exception as e:
        log_error_response({"error": str(e)}, "Error renewing Tor IP")
        return False

def log_error_response(response_data, error):
    """Lưu Response lỗi vào error_log_history.json"""
    try:
        log_entry = {
            "timestamp": datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S %z"),
            "error": str(error),
            "response": response_data
        }
        with open("error_log_history.json", "a") as f:
            json.dump(log_entry, f, indent=2)
            f.write("\n")
    except Exception as e:
        print(f"Error logging response: {e}")

def fetch_historical_data(record_count=2000):
    """Lấy dữ liệu lịch sử theo số lượng bản ghi yêu cầu"""
    token = load_token()
    if not token:
        token = refresh_token()
        if not token:
            return False, "Failed to obtain token"

    HEADERS["Blade-Auth"] = token
    total_records_fetched = 0
    page = 1
    all_records = []
    max_retries = 3

    while total_records_fetched < record_count:
        params = {
            "subServiceCode": "RG1M",
            "size": 2000,
            "current": page
        }
        retries = 0
        while retries < max_retries:
            try:
                response = session.get(API_URL, headers=HEADERS, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "data" not in data or "records" not in data["data"]:
                        log_error_response(data, "Missing 'data' or 'records'")
                        break

                    records = data["data"]["records"]
                    total = data["data"]["total"]
                    if not records:
                        print(f"No more records found at page {page}")
                        break

                    for record in records:
                        if total_records_fetched >= record_count:
                            break
                        issue = record["issue"]
                        value = record["value"]
                        color = record["simpleResultFormatList"][0]["color"]
                        adjusted_color = adjust_color(value, color)
                        issue_date = record["issueDate"]
                        plan_draw_time = record["planDrawTime"]

                        all_records.append([issue, issue_date, plan_draw_time, adjusted_color, value])
                        total_records_fetched += 1

                    vietnam_tz = timezone(timedelta(hours=7))
                    current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S %z")
                    print(f"[{current_time}] Fetched page {page}, total records: {total_records_fetched}/{record_count} (Total available: {total})")

                    if total_records_fetched >= record_count or len(records) < 25 or total_records_fetched >= total:
                        break
                    page += 1
                    time.sleep(random.uniform(1, 3))  # Tránh bị phát hiện là bot
                    break  # Thoát vòng lặp retry nếu thành công
                elif response.status_code in [403, 429]:
                    retries += 1
                    print(f"IP restricted (status: {response.status_code}), attempt {retries}/{max_retries}")
                    if renew_tor_ip():
                        time.sleep(10)
                        token = refresh_token()  # Làm mới token sau khi đổi IP
                        if token:
                            HEADERS["Blade-Auth"] = token
                            continue
                    else:
                        time.sleep(60)
                else:
                    log_error_response(response.json() if response.text else {"status": response.status_code}, "Request failed")
                    break
            except requests.exceptions.RequestException as e:
                log_error_response({"error": str(e)}, "Request error")
                retries += 1
                if "timeout" in str(e).lower() or "connection" in str(e).lower():
                    time.sleep(10)
                if retries == max_retries:
                    break

        if retries == max_retries:
            break

    # Đảo ngược danh sách để kết quả mới ở dưới
    all_records.reverse()

    # Lưu dữ liệu vào CSV, ghi đè để xóa dữ liệu cũ
    if all_records:
        file_exists = os.path.exists("results_history_full.csv")
        try:
            with open("results_history_full.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["issue", "issueDate", "planDrawTime", "color", "value"])
                writer.writerows(all_records)
            print(f"[{current_time}] Saved {total_records_fetched} records to results_history_full.csv")
            return True, total_records_fetched
        except Exception as e:
            log_error_response({"error": str(e)}, "Error saving to CSV")
            return False, str(e)
    else:
        return False, "No data fetched."

def main():
    """Chạy để cập nhật dữ liệu khi bắt đầu giờ và ngay khi khởi động"""
    vietnam_tz = timezone(timedelta(hours=7))
    
    # Thực hiện cập nhật ngay khi khởi động
    current_time = datetime.now(vietnam_tz)
    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Starting initial data update...")
    success, message = fetch_historical_data(2000)
    if success:
        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Initial data update completed. Fetched {message} records.")
    else:
        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Initial data update failed: {message}")

    while True:
        current_time = datetime.now(vietnam_tz)
        next_hour = (current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        
        # Tính thời gian chờ đến đầu giờ tiếp theo
        wait_seconds = (next_hour - current_time).total_seconds()
        if wait_seconds > 0:
            print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Waiting {wait_seconds:.0f} seconds until {next_hour.strftime('%H:%M:%S')}...")
            time.sleep(wait_seconds)

        # Cập nhật dữ liệu khi bắt đầu giờ mới
        current_time = datetime.now(vietnam_tz)
        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Starting hourly data update...")
        success, message = fetch_historical_data(2000)
        if success:
            print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Hourly data update completed. Fetched {message} records.")
        else:
            print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %z')}] Hourly data update failed: {message}")

if __name__ == "__main__":
    main()
