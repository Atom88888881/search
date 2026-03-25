from flask import Flask, render_template_string, request, jsonify
import requests
import json
import os
import time
import pickle
import threading
import base64
from datetime import datetime
import re
import glob

app = Flask(__name__)

# ==================== CONFIG ====================
SHIPMILE_FILE = "shipsmile_address.json"
SHIPMILE_URL = "https://files.catbox.moe/c9f97i.json"

TRUE_USER = "17554398"
TRUE_PASS = "true123456"
TRUE_COOKIE = "true_cookies.json"
TRUE_URL = "https://sff-dealer.truecorp.co.th/mnp/"
TRUE_API = "https://sff-dealer.truecorp.co.th/profiles/customer/get"

TPMAP_API_PEOPLE = "https://api2.logbook.emenscr.in.th/people/find"
TPMAP_API_WELFARE = "https://api2.logbook.emenscr.in.th/mofwelfare/find"

# TPMAP Cookies from pickle (base64 encoded)
TPMAP_PICKLE_B64 = "gASV9AAAAAAAAABdlCh9lCiMBmRvbWFpbpSME2xvZ2Jvb2sudHBtYXAuaW4udGiUjAZleHBpcnmUStYUxGmMCGh0dHBPbmx5lImMBG5hbWWUjA5fcGtfc2VzLjIuNjM2N5SMBHBhdGiUjAEvlIwIc2FtZVNpdGWUjANMYXiUjAZzZWN1cmWUiYwFdmFsdWWUjAExlHV9lChoAowTbG9nYm9vay50cG1hcC5pbi50aJRoBEpOK8praAWJaAaMDV9wa19pZC4yLjYzNjeUaAhoCWgKjANMYXiUaAyJaA2MHDQxYzYyYzhkOGJiZGQxZDYuMTc3NDQ1NjI3MC6UdWUu"

# ==================== GAMBLING DATA MANAGER ====================
class GamblingDataManager:
    def __init__(self):
        self.data = []
        self.load_data()
    
    def find_gambling_files(self):
        possible_files = []
        for filename in ["เว็บพนัน.json", "เว็บพนัน.txt", "gambling.json", "gambling.txt", "member_data.json"]:
            if os.path.exists(filename):
                possible_files.append(filename)
        for file in glob.glob("*.json") + glob.glob("*.txt"):
            if "เว็บ" in file or "พนัน" in file or "gambling" in file:
                if file not in possible_files:
                    possible_files.append(file)
        return possible_files
    
    def convert_txt_to_json(self, txt_file):
        try:
            members = []
            with open(txt_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 11:
                            raw_phone = parts[8]
                            digits_only = re.sub(r'\D', '', raw_phone)
                            corrected_phone = '0' + digits_only if len(digits_only) == 9 else digits_only
                            
                            if len(corrected_phone) == 10:
                                if corrected_phone.startswith(('06', '08', '09')):
                                    formatted_phone = f"{corrected_phone[:3]}-{corrected_phone[3:6]}-{corrected_phone[6:]}"
                                else:
                                    formatted_phone = f"{corrected_phone[:2]}-{corrected_phone[2:6]}-{corrected_phone[6:]}"
                            else:
                                formatted_phone = corrected_phone
                            
                            member = {
                                "รหัสสมาชิก": parts[0], "รหัสกลุ่ม": parts[1], "รหัสอ้างอิง": parts[2],
                                "ประเภทการตลาด": parts[3], "ประเภทสมาชิก": parts[4], "สถานะใช้งาน": parts[5],
                                "ชื่อ": parts[6], "นามสกุล": parts[7], "เบอร์โทรศัพท์": formatted_phone,
                                "ประเภทผู้ใช้งาน": parts[9], "ธนาคาร": parts[10],
                                "เลขบัญชี": parts[11] if len(parts) > 11 else "",
                                "ชื่อ-นามสกุล": f"{parts[6]} {parts[7]}",
                                "เบอร์โทรศัพท์_raw": raw_phone, "เบอร์โทรศัพท์_10หลัก": corrected_phone,
                                "เบอร์โทรศัพท์_digits": digits_only
                            }
                            members.append(member)
            if members:
                json_file = txt_file.replace('.txt', '.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump({"total": len(members), "data": members}, f, ensure_ascii=False, indent=2)
                print(f"   Converted {len(members)} records from {txt_file}")
                return members
        except Exception as e:
            print(f"   Error converting {txt_file}: {e}")
        return []
    
    def load_data(self):
        found_files = self.find_gambling_files()
        all_members = []
        for file_path in found_files:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        members = json_data["data"] if isinstance(json_data, dict) and "data" in json_data else (json_data if isinstance(json_data, list) else [])
                        all_members.extend(members)
                        print(f"   Loaded {len(members)} records from {file_path}")
                elif file_path.endswith('.txt'):
                    members = self.convert_txt_to_json(file_path)
                    if members:
                        all_members.extend(members)
            except Exception as e:
                print(f"   Error loading {file_path}: {e}")
        self.data = all_members
        if self.data:
            print(f"   Gambling data loaded: {len(self.data)} total records")
        else:
            print(f"   No gambling data found")
        return self.data
    
    def search(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for item in self.data:
            search_fields = [
                str(item.get('รหัสสมาชิก', '')), str(item.get('ชื่อ', '')), str(item.get('นามสกุล', '')),
                str(item.get('ชื่อ-นามสกุล', '')), str(item.get('เบอร์โทรศัพท์', '')),
                str(item.get('เบอร์โทรศัพท์_raw', '')), str(item.get('เบอร์โทรศัพท์_10หลัก', '')),
                str(item.get('ธนาคาร', '')), str(item.get('เลขบัญชี', ''))
            ]
            for field in search_fields:
                if keyword_lower in field.lower():
                    results.append(item)
                    break
        return results
    
    def get_statistics(self):
        stats = {'total': len(self.data), 'by_bank': {}, 'by_status': {}, 'active_count': 0}
        for item in self.data:
            bank = item.get('ธนาคาร', 'ไม่ระบุ')
            stats['by_bank'][bank] = stats['by_bank'].get(bank, 0) + 1
            status = item.get('สถานะใช้งาน', 'ไม่ระบุ')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            if status == 'Active':
                stats['active_count'] += 1
        return stats

# ==================== SHIPMILE DATA MANAGER ====================
class ShipmileDataManager:
    def __init__(self):
        self.data = []
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(SHIPMILE_FILE):
                with open(SHIPMILE_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                print(f"Shipmile: Loaded {len(self.data)} records")
                return True
        except Exception as e:
            print(f"Shipmile load error: {e}")
        return False
    
    def download_data(self):
        url = SHIPMILE_URL
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'application/json'}
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                with open(SHIPMILE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.data = data
                print(f"Download successful: {len(data)} records")
                return True
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(3)
        return False
    
    def search(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for item in self.data:
            name = str(item.get('name', '')).lower()
            phone = str(item.get('phone', '')).lower()
            address = str(item.get('address', '')).lower()
            if (keyword_lower in name or keyword_lower in phone or keyword_lower in address):
                results.append(item)
        return results

# ==================== TRUE PORTAL ====================
class TruePortalService:
    def __init__(self):
        self.cookies = {}
        self.load_cookies()
    
    def load_cookies(self):
        try:
            if os.path.exists(TRUE_COOKIE):
                with open(TRUE_COOKIE, "r", encoding="utf-8") as f:
                    self.cookies = json.load(f)
                return True
        except:
            pass
        return False
    
    def save_cookies(self):
        try:
            with open(TRUE_COOKIE, "w", encoding="utf-8") as f:
                json.dump(self.cookies, f, indent=2)
        except:
            pass
    
    def check_session(self):
        if not self.cookies:
            return False
        try:
            test_url = f"{TRUE_API}?product-id-number=0812345678&product-id-name=msisdn"
            headers = {"channel_alias": "WHS", "employeeid": TRUE_USER}
            r = requests.get(test_url, headers=headers, cookies=self.cookies, timeout=10)
            return r.status_code == 200
        except:
            return False
    
    def search(self, keyword):
        if not keyword:
            return None
        if not self.cookies or not self.check_session():
            return None
        phone_clean = re.sub(r'\D', '', keyword)
        if phone_clean and len(phone_clean) == 10:
            url = f"{TRUE_API}?product-id-number={phone_clean}&product-id-name=msisdn"
        elif phone_clean and len(phone_clean) == 13:
            url = f"{TRUE_API}?product-id-number={phone_clean}&product-id-name=citizen-id"
        else:
            return None
        headers = {"channel_alias": "WHS", "employeeid": TRUE_USER}
        try:
            r = requests.get(url, headers=headers, cookies=self.cookies, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("response-data"):
                    return data["response-data"]
            return None
        except Exception as e:
            print(f"True API error: {e}")
            return None

# ==================== TPMAP SERVICE (ใช้ pickle cookies) ====================
class TPMAPService:
    def __init__(self):
        self.cookies = None
        self.load_cookies_from_pickle()
    
    def load_cookies_from_pickle(self):
        try:
            pickle_bytes = base64.b64decode(TPMAP_PICKLE_B64)
            cookies_list = pickle.loads(pickle_bytes)
            self.cookies = {}
            for cookie in cookies_list:
                if isinstance(cookie, dict):
                    name = cookie.get('name')
                    value = cookie.get('value')
                    if name and value:
                        self.cookies[name] = value
            if self.cookies:
                print(f"TPMAP: Loaded {len(self.cookies)} cookies")
                return True
            return False
        except Exception as e:
            print(f"TPMAP: Error loading cookies - {e}")
            return False
    
    def build_full_address(self, data):
        parts = []
        address_num = str(data.get("address_num", "")) if data.get("address_num") else ""
        if address_num and address_num != "-" and address_num != "":
            parts.append(address_num)
        moo = str(data.get("moo", "")) if data.get("moo") else ""
        if moo and moo != "-" and moo != "":
            parts.append(f"หมู่ {moo}")
        village_name = str(data.get("village_name", "")) if data.get("village_name") else ""
        if village_name and village_name != "-" and village_name != "":
            parts.append(village_name)
        tumbol_name = str(data.get("tumbol_name", "")) if data.get("tumbol_name") else ""
        if tumbol_name and tumbol_name != "-" and tumbol_name != "":
            parts.append(f"ตำบล {tumbol_name}")
        ampuhur_name = str(data.get("ampuhur_name", "")) if data.get("ampuhur_name") else ""
        if ampuhur_name and ampuhur_name != "-" and ampuhur_name != "":
            parts.append(f"อำเภอ {ampuhur_name}")
        province_name = str(data.get("province_name", "")) if data.get("province_name") else ""
        if province_name and province_name != "-" and province_name != "":
            parts.append(f"จังหวัด {province_name}")
        zipcode = str(data.get("zipcode", "")) if data.get("zipcode") else ""
        if zipcode and zipcode != "-" and zipcode != "":
            parts.append(zipcode)
        return " ".join(parts) if parts else "ไม่มีข้อมูลที่อยู่"
    
    def search(self, keyword):
        if not keyword:
            return None, None
        if not self.cookies:
            return None, None
        
        session = requests.Session()
        session.cookies.update(self.cookies)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://logbook.tpmap.in.th",
            "Referer": "https://logbook.tpmap.in.th/table",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        clean_keyword = re.sub(r'\D', '', keyword)
        payload = {
            "draw": 3, "columns[0][data]": "house_data_ID", "columns[1][data]": "village_ID",
            "columns[2][data]": "NID", "columns[3][data]": "name", "columns[4][data]": "village_name",
            "columns[5][data]": "status", "start": 0, "length": 50, "search[value]": "", "search[regex]": "false",
            "prov": "", "amp": "", "tam": "", "NID": clean_keyword if len(clean_keyword) == 13 else "",
            "fullname": keyword if not (clean_keyword and len(clean_keyword) == 13) else "", "firstname": "", "lastname": ""
        }
        try:
            people_res = session.post(TPMAP_API_PEOPLE, data=payload, headers=headers, timeout=10)
            people = people_res.json().get("data", []) if people_res.status_code == 200 else []
            welfare_res = session.post(TPMAP_API_WELFARE, data=payload, headers=headers, timeout=10)
            welfare = welfare_res.json().get("data", []) if welfare_res.status_code == 200 else []
            for person in people:
                person['formatted_address'] = self.build_full_address(person)
            return people, welfare
        except Exception as e:
            print(f"TPMAP API error: {e}")
            return None, None

# ==================== INITIALIZE SERVICES ====================
shipmile_manager = ShipmileDataManager()
true_service = TruePortalService()
tpmap_service = TPMAPService()
gambling_manager = GamblingDataManager()

def initialize_services():
    print("=" * 60)
    print("Initializing EasySearch Services")
    print("=" * 60)
    gambling_stats = gambling_manager.get_statistics()
    if gambling_stats['total'] > 0:
        print(f"\nGambling Database: {gambling_stats['total']} records loaded")
        print(f"   Active: {gambling_stats['active_count']}")
    else:
        print(f"\nGambling Database: No data (optional)")
    print("\nLoading Shipmile Data...")
    if not shipmile_manager.data:
        print("   Downloading from remote...")
        shipmile_manager.download_data()
    print(f"   Loaded {len(shipmile_manager.data)} Shipmile records")
    print("\nTrue Portal:")
    if true_service.cookies:
        print("   Cookies loaded")
    else:
        print("   No cookies found")
    print("\nTPMAP:")
    if tpmap_service.cookies:
        print(f"   Cookies loaded: {list(tpmap_service.cookies.keys())}")
    else:
        print("   No cookies found")
    print("\n" + "=" * 60)
    print("All services initialized!")
    print("=" * 60)

threading.Thread(target=initialize_services, daemon=True).start()

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    system = data.get('system', 'all')
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    results = {'keyword': keyword, 'system': system, 'timestamp': datetime.now().isoformat(), 'data': {}}
    if system == 'all' or system == 'true':
        true_data = true_service.search(keyword)
        results['data']['true_portal'] = {'status': 'success' if true_data else 'not_found', 'data': true_data}
    if system == 'all' or system == 'tpmap':
        people, welfare = tpmap_service.search(keyword)
        results['data']['tpmap'] = {'status': 'success' if people else 'not_found', 'people': people, 'welfare': welfare}
    if system == 'all' or system == 'ship':
        ship_data = shipmile_manager.search(keyword)
        results['data']['shipmile'] = {'status': 'success' if ship_data else 'not_found', 'count': len(ship_data), 'data': ship_data[:10]}
    if system == 'all' or system == 'gambling':
        gambling_data = gambling_manager.search(keyword)
        results['data']['gambling'] = {'status': 'success' if gambling_data else 'not_found', 'count': len(gambling_data), 'data': gambling_data[:50]}
    return jsonify(results)

@app.route('/api/status', methods=['GET'])
def api_status():
    gambling_stats = gambling_manager.get_statistics()
    status = {
        'shipmile': {'loaded': len(shipmile_manager.data) > 0, 'records': len(shipmile_manager.data)},
        'true_portal': {'authenticated': true_service.check_session() if true_service.cookies else False},
        'tpmap': {'authenticated': tpmap_service.cookies is not None},
        'gambling': {'loaded': len(gambling_manager.data) > 0, 'records': gambling_stats['total'], 'active': gambling_stats['active_count']},
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EasySearch Services - ระบบค้นหาข้อมูล</title>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Kanit', 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; overflow: hidden; }
        .app-container { display: flex; height: 100vh; padding: 20px; gap: 20px; }
        .left-panel { width: 480px; min-width: 420px; background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; }
        .left-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 25px; text-align: center; }
        .left-header h1 { font-size: 1.8em; margin-bottom: 8px; font-weight: 700; }
        .left-header h1 i { margin-right: 12px; }
        .left-header p { font-size: 0.95em; opacity: 0.95; }
        .search-form { padding: 25px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; }
        .system-selector { margin-bottom: 25px; }
        .system-selector label { display: block; margin-bottom: 12px; font-weight: 600; color: #495057; font-size: 1em; }
        .radio-group { display: flex; flex-wrap: wrap; gap: 12px; }
        .radio-group label { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; background: white; border-radius: 30px; font-size: 0.9em; font-weight: normal; cursor: pointer; border: 1.5px solid #dee2e6; transition: all 0.2s; margin: 0; }
        .radio-group label:hover { border-color: #667eea; background: #f0f0ff; transform: translateY(-1px); }
        .radio-group input[type="radio"] { margin: 0; width: 16px; height: 16px; cursor: pointer; }
        .search-input-group { display: flex; gap: 12px; margin-bottom: 20px; }
        .search-input { flex: 1; padding: 14px 18px; font-size: 15px; font-family: 'Kanit', sans-serif; border: 2px solid #dee2e6; border-radius: 30px; transition: all 0.3s; }
        .search-input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
        .search-btn { padding: 14px 28px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 30px; font-size: 15px; font-weight: 600; font-family: 'Kanit', sans-serif; cursor: pointer; transition: all 0.3s; display: inline-flex; align-items: center; gap: 10px; }
        .search-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102,126,234,0.4); }
        .search-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .status-bar { background: #e9ecef; padding: 12px 16px; border-radius: 12px; font-size: 13px; color: #495057; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
        .stats-mini { background: white; border-radius: 12px; padding: 15px; border: 1px solid #e9ecef; }
        .stats-mini-title { font-weight: 600; margin-bottom: 12px; color: #495057; font-size: 0.9em; }
        .stats-mini-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.85em; }
        .stats-mini-item:last-child { border-bottom: none; }
        .stats-mini-item i { width: 24px; color: #667eea; }
        .stats-value { font-weight: 600; color: #667eea; }
        .right-panel { flex: 1; background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; }
        .right-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }
        .right-header h2 { font-size: 1.3em; font-weight: 500; }
        .right-header h2 i { margin-right: 10px; }
        .result-count { background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 25px; font-size: 0.9em; font-weight: 500; }
        .results-container { flex: 1; overflow-y: auto; padding: 20px; }
        .result-card { background: white; border-radius: 12px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #e9ecef; }
        .result-header { background: #f8f9fa; padding: 14px 20px; font-weight: 600; font-size: 1em; border-bottom: 2px solid #667eea; display: flex; justify-content: space-between; align-items: center; }
        .result-header i { margin-right: 8px; color: #667eea; }
        .result-badge { background: #e9ecef; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: normal; }
        .result-body { padding: 15px 20px; }
        .member-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .member-table th, .member-table td { padding: 10px 8px; text-align: left; border-bottom: 1px solid #e9ecef; }
        .member-table th { background: #f8f9fa; font-weight: 600; color: #495057; }
        .member-table tr:hover { background: #f8f9fa; }
        .json-viewer { background: #f8f9fa; border-radius: 8px; padding: 12px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 11px; line-height: 1.5; max-height: 350px; overflow-y: auto; }
        .json-viewer pre { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
        .loading { text-align: center; padding: 60px; }
        .spinner { width: 50px; height: 50px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .info-message { background: #d1ecf1; color: #0c5460; padding: 18px; border-radius: 12px; display: flex; align-items: center; gap: 12px; font-size: 14px; }
        .error-message { background: #f8d7da; color: #721c24; padding: 18px; border-radius: 12px; display: flex; align-items: center; gap: 12px; font-size: 14px; }
        .results-container::-webkit-scrollbar { width: 8px; }
        .results-container::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
        .results-container::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        .results-container::-webkit-scrollbar-thumb:hover { background: #555; }
        @media (max-width: 900px) { .app-container { flex-direction: column; } .left-panel { width: 100%; min-width: auto; max-height: 45vh; } .right-panel { min-height: 50vh; } }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="left-panel">
            <div class="left-header">
                <h1><i class="fas fa-search"></i> AtomSearch</h1>
                <p>ระบบค้นหาข้อมูลอัจฉริยะ | รองรับ 4 ระบบ</p>
            </div>
            <div class="search-form">
                <div class="system-selector">
                    <label><i class="fas fa-cog"></i> เลือกระบบค้นหา</label>
                    <div class="radio-group">
                        <label><input type="radio" name="system" value="all" checked> <i class="fas fa-globe"></i> ค้นหาทั้งหมด</label>
                        <label><input type="radio" name="system" value="true"> <i class="fas fa-mobile-alt"></i> True CRM</label>
                        <label><input type="radio" name="system" value="tpmap"> <i class="fas fa-landmark"></i> TPMAP</label>
                        <label><input type="radio" name="system" value="ship"> <i class="fas fa-truck"></i> Shipmile</label>
                        <label><input type="radio" name="system" value="gambling"> <i class="fas fa-dice"></i> เว็บพนัน</label>
                    </div>
                </div>
                <div class="search-input-group">
                    <input type="text" id="keyword" class="search-input" placeholder="ชื่อ, เบอร์โทรศัพท์, หรือเลขบัตรประชาชน...">
                    <button id="searchBtn" class="search-btn"><i class="fas fa-search"></i> ค้นหา</button>
                </div>
                <div class="status-bar" id="statusBar"><i class="fas fa-check-circle" style="color: #28a745;"></i> พร้อมใช้งาน</div>
                <div class="stats-mini">
                    <div class="stats-mini-title"><i class="fas fa-chart-simple"></i> สถานะระบบ</div>
                    <div id="miniStats"><div class="stats-mini-item"><span><i class="fas fa-spinner fa-pulse"></i> กำลังโหลด...</span><span>...</span></div></div>
                </div>
            </div>
        </div>
        <div class="right-panel">
            <div class="right-header">
                <h2><i class="fas fa-chart-line"></i> ผลการค้นหา</h2>
                <div class="result-count" id="resultCount">รอการค้นหา</div>
            </div>
            <div class="results-container" id="resultsContainer">
                <div class="info-message"><i class="fas fa-info-circle fa-2x"></i><div><strong>เริ่มต้นการค้นหา</strong><br>กรุณากรอกข้อมูลที่ต้องการค้นหาทางด้านซ้ายมือ</div></div>
            </div>
        </div>
    </div>
    <script>
        let isSearching = false;
        document.getElementById('searchBtn').onclick = performSearch;
        document.getElementById('keyword').onkeypress = function(e) { if (e.key === 'Enter') performSearch(); };
        async function performSearch() {
            if (isSearching) return;
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) { updateStatus('กรุณากรอกข้อมูลที่ต้องการค้นหา', 'warning'); return; }
            const system = document.querySelector('input[name="system"]:checked').value;
            isSearching = true;
            const searchBtn = document.getElementById('searchBtn');
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> กำลังค้นหา...';
            const resultsContainer = document.getElementById('resultsContainer');
            resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>กำลังค้นหาข้อมูล...</p><p style="font-size:12px; margin-top:10px;">ระบบกำลังค้นหาจากทุกฐานข้อมูล</p></div>';
            updateStatus('กำลังค้นหา: ' + keyword, 'info');
            document.getElementById('resultCount').innerHTML = 'กำลังค้นหา...';
            try {
                const response = await fetch('/api/search', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({keyword, system}) });
                const data = await response.json();
                displayResults(data);
                updateStatus('ค้นหาสำเร็จ', 'success');
            } catch (error) {
                updateStatus('เกิดข้อผิดพลาด: ' + error.message, 'error');
                resultsContainer.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-triangle fa-2x"></i><div><strong>เกิดข้อผิดพลาด</strong><br>ไม่สามารถค้นหาข้อมูลได้</div></div>';
            } finally {
                isSearching = false;
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search"></i> ค้นหา';
            }
        }
        function displayResults(data) {
            const resultsContainer = document.getElementById('resultsContainer');
            let html = ''; let totalResults = 0;
            if (data.data) {
                if (data.data.gambling && data.data.gambling.data && data.data.gambling.data.length > 0) {
                    totalResults += data.data.gambling.count;
                    html += createGamblingCard(data.data.gambling);
                }
                if (data.data.true_portal && data.data.true_portal.data) {
                    totalResults += 1;
                    html += createResultCard('True CRM', data.data.true_portal.data);
                }
                if (data.data.tpmap && data.data.tpmap.people && data.data.tpmap.people.length > 0) {
                    totalResults += data.data.tpmap.people.length;
                    html += createResultCard('TPMAP', data.data.tpmap);
                }
                if (data.data.shipmile && data.data.shipmile.data && data.data.shipmile.data.length > 0) {
                    totalResults += data.data.shipmile.count;
                    html += createResultCard('Shipmile', data.data.shipmile);
                }
                if (totalResults === 0) { html = '<div class="info-message"><i class="fas fa-info-circle fa-2x"></i><div><strong>ไม่พบข้อมูล</strong><br>ไม่พบข้อมูลสำหรับ: ' + escapeHtml(data.keyword) + '</div></div>'; }
            }
            resultsContainer.innerHTML = html;
            document.getElementById('resultCount').innerHTML = `พบ ${totalResults} รายการ`;
        }
        function createGamblingCard(gamblingData) {
            let tableHtml = `<div class="result-card"><div class="result-header"><div><i class="fas fa-dice"></i> เว็บพนัน</div><span class="result-badge"><i class="fas fa-users"></i> ${gamblingData.count} รายการ</span></div><div class="result-body"><table class="member-table"><thead><tr><th>รหัสสมาชิก</th><th>ชื่อ-นามสกุล</th><th>เบอร์โทร</th><th>ธนาคาร</th><th>เลขบัญชี</th><th>สถานะ</th></tr></thead><tbody>`;
            gamblingData.data.slice(0, 20).forEach(item => {
                const statusColor = item['สถานะใช้งาน'] === 'Active' ? '#28a745' : '#dc3545';
                tableHtml += `<tr><td>${escapeHtml(item['รหัสสมาชิก'] || '-')}</td><td>${escapeHtml(item['ชื่อ-นามสกุล'] || '-')}</td><td>${escapeHtml(item['เบอร์โทรศัพท์'] || '-')}</td><td>${escapeHtml(item['ธนาคาร'] || '-')}</td><td>${escapeHtml(item['เลขบัญชี'] || '-')}</td><td><span style="color: ${statusColor}">${escapeHtml(item['สถานะใช้งาน'] || '-')}</span></td></tr>`;
            });
            if (gamblingData.count > 20) { tableHtml += `<tr><td colspan="6" style="text-align:center; color:#667eea;">... และอีก ${gamblingData.count - 20} รายการ</td></tr>`; }
            tableHtml += `</tbody></table></div></div>`;
            return tableHtml;
        }
        function createResultCard(title, data) { return `<div class="result-card"><div class="result-header"><div><i class="fas fa-database"></i> ${escapeHtml(title)}</div><span class="result-badge">JSON Response</span></div><div class="result-body"><div class="json-viewer"><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></div></div></div>`; }
        async function updateMiniStats() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                const gamblingText = status.gambling.records > 0 ? `${status.gambling.records.toLocaleString()} รายการ` : 'ไม่มีข้อมูล';
                const statsHtml = `<div class="stats-mini-item"><span><i class="fas fa-dice"></i> เว็บพนัน</span><span class="stats-value">${gamblingText}</span></div><div class="stats-mini-item"><span><i class="fas fa-truck"></i> Shipmile</span><span class="stats-value">${status.shipmile.records.toLocaleString()} รายการ</span></div><div class="stats-mini-item"><span><i class="fas fa-mobile-alt"></i> True CRM</span><span class="stats-value">${status.true_portal.authenticated ? 'พร้อมใช้งาน' : 'ไม่พร้อม'}</span></div><div class="stats-mini-item"><span><i class="fas fa-landmark"></i> TPMAP</span><span class="stats-value">${status.tpmap.authenticated ? 'พร้อมใช้งาน' : 'ไม่พร้อม'}</span></div>`;
                document.getElementById('miniStats').innerHTML = statsHtml;
            } catch(e) { console.error(e); }
        }
        function updateStatus(message, type) {
            const statusBar = document.getElementById('statusBar');
            let icon = '<i class="fas fa-info-circle"></i>'; let bgColor = '#e9ecef'; let textColor = '#495057';
            if (type === 'error') { icon = '<i class="fas fa-exclamation-circle" style="color: #dc3545;"></i>'; bgColor = '#f8d7da'; textColor = '#721c24'; }
            else if (type === 'success') { icon = '<i class="fas fa-check-circle" style="color: #28a745;"></i>'; bgColor = '#d4edda'; textColor = '#155724'; setTimeout(() => { const sb = document.getElementById('statusBar'); sb.style.background = '#e9ecef'; sb.style.color = '#495057'; sb.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i> พร้อมใช้งาน'; }, 2000); }
            else if (type === 'warning') { icon = '<i class="fas fa-exclamation-triangle" style="color: #ffc107;"></i>'; bgColor = '#fff3cd'; textColor = '#856404'; }
            statusBar.style.background = bgColor; statusBar.style.color = textColor; statusBar.innerHTML = `${icon} ${escapeHtml(message)}`;
        }
        function escapeHtml(text) { if (!text) return ''; const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }
        updateMiniStats();
        setInterval(updateMiniStats, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("EasySearch Services - Web Edition")
    print("=" * 60)
    print("Starting server at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
