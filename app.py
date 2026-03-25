# app.py
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import os
import re
from datetime import datetime

app = Flask(__name__)

# ==================== CONFIG ====================
# ใช้ GitHub Releases URLs (ไฟล์ใหญ่)
GAMBLING_DATA_URL = "https://github.com/Atom88888881/search/releases/download/v1.0/gambling_data.json"
SHIPMILE_DATA_URL = "https://github.com/Atom88888881/search/releases/download/v1.0/shipmile_address.json"

# True Portal Cookies
TRUE_COOKIES = {
    "__cf_bm": "sm5sdjrPZzFME2ro3r9q3Z5WWN5YX7dHh4Wge0QbKnk-1774457484.184885-1.0.1.1-tqPVt8B8Ae26bChgntse8FHJrNNzEzcVoxxHH1cetxaiRwJgKIOCjg9SZ3aLV0BfoccB8Sm2wCVfsS0brxs88IiGFIz9PJ9F73FSAhWsULI1siTna6cycuUVpctRI9lG",
    "_cfuvid": "7yRX5OPCgh8jFy_.dr9gadY8cB5UjvZaduerE2FyQns-1774457483.8987513-1.0.1.1-yRdomrMZO7KHAgBQTkB7qg2izFRBrdYAkYTB9bu4lt0",
    "JSESSIONID": "w8KyY+19qmYKyOdQ1At3NwDU.SFF_node6",
    "cf_clearance": "TfNusP6ofDEGGc7zhfZvWcEeKspmdBWj2IOZOjQf43U-1774457484-1.2.1.1-BgbH9yTE3IT4ddtBNidBG1qsw0yk_fEHVRIDBw_3Bu0RWDL06jP.J27peskuV_zCm109B77IpKuXFbrJL2PZPwqA_qQ9.Bhrv6SKdWZE9iRyxAGtTUZ_ln1DNQut2d8zT2oeEv4AwE80HqTNrUvZrfrZQFS6koROkeAFzOu6HDZ7r8irzzWWEc6RkxTZCg.acalATIkuUTBCv6UDWW4u_TfpB9c52CHxMeFLQ_vWOYU",
    "dealer_prod_session": "6CitXY56FZH8ZMi4k8Vgiw|1774493490|MuH0Uzd5pzj5i4jpE8bMaxOVXro",
    "NSC_WJQ_UNTBQQS-19180-19181": "ffffffffaf1baadb45525d5f4f58455e445a4a427cdd"
}

TRUE_USER = "17554398"
TRUE_API = "https://sff-dealer.truecorp.co.th/profiles/customer/get"

# TPMAP Cookies
import base64
TPMAP_COOKIES_B64 = "W3siZG9tYWluIjogImxvZ2Jvb2sudHBtYXAuaW4udGgiLCAiZXhwaXJ5IjogMTc3NDQ2MDg3MywgImh0dHBPbmx5IjogZmFsc2UsICJuYW1lIjogIl9wa19zZXMuMi42MzY3IiwgInBhdGgiOiAiLyIsICJzYW1lU2l0ZSI6ICJMYXgiLCAic2VjdXJlIjogZmFsc2UsICJ2YWx1ZSI6ICIxIn0sIHsiZG9tYWluIjogImxvZ2Jvb2sudHBtYXAuaW4udGgiLCAiZXhwaXJ5IjogMTgwODQxNDI3MywgImh0dHBPbmx5IjogZmFsc2UsICJuYW1lIjogIl9wa19pZC4yLjYzNjciLCAicGF0aCI6ICIvIiwgInNhbWVTaXRlIjogIkxheCIsICJzZWN1cmUiOiBmYWxzZSwgInZhbHVlIjogIjgyZjkxZmMwYzNhOGJkYjUuMTc3NDQ1OTA3My4ifV0="

# ==================== DATA MANAGERS (โหลดจาก URL) ====================
class GamblingDataManager:
    def __init__(self):
        self.data = []
        self.load_from_url()
    
    def load_from_url(self):
        """โหลดข้อมูลเว็บพนันจาก GitHub Releases"""
        try:
            print(f"📥 Downloading gambling data from: {GAMBLING_DATA_URL}")
            response = requests.get(GAMBLING_DATA_URL, timeout=60)
            if response.status_code == 200:
                json_data = response.json()
                if isinstance(json_data, dict) and "data" in json_data:
                    self.data = json_data["data"]
                elif isinstance(json_data, list):
                    self.data = json_data
                print(f"✅ Gambling data loaded: {len(self.data)} records")
                return True
            else:
                print(f"❌ Failed to load: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error loading gambling data: {e}")
            return False
    
    def search(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for item in self.data:
            search_fields = [
                str(item.get('รหัสสมาชิก', '')), str(item.get('ชื่อ', '')), 
                str(item.get('นามสกุล', '')), str(item.get('ชื่อ-นามสกุล', '')),
                str(item.get('เบอร์โทรศัพท์', '')), str(item.get('เบอร์โทรศัพท์_raw', '')),
                str(item.get('เบอร์โทรศัพท์_10หลัก', '')), str(item.get('ธนาคาร', '')),
                str(item.get('เลขบัญชี', ''))
            ]
            for field in search_fields:
                if keyword_lower in field.lower():
                    results.append(item)
                    break
        return results
    
    def get_statistics(self):
        stats = {'total': len(self.data), 'active_count': 0}
        for item in self.data:
            if item.get('สถานะใช้งาน') == 'Active':
                stats['active_count'] += 1
        return stats

class ShipmileDataManager:
    def __init__(self):
        self.data = []
        self.load_from_url()
    
    def load_from_url(self):
        """โหลดข้อมูล Shipmile จาก GitHub Releases"""
        try:
            print(f"📥 Downloading shipmile data from: {SHIPMILE_DATA_URL}")
            response = requests.get(SHIPMILE_DATA_URL, timeout=60)
            if response.status_code == 200:
                self.data = response.json()
                print(f"✅ Shipmile data loaded: {len(self.data)} records")
                return True
            else:
                print(f"❌ Failed to load: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error loading shipmile data: {e}")
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

# ==================== TRUE PORTAL SERVICE ====================
class TruePortalService:
    def __init__(self):
        self.cookies = TRUE_COOKIES
        self.user = TRUE_USER
    
    def search(self, keyword):
        if not keyword:
            return None
        
        phone_clean = re.sub(r'\D', '', keyword)
        if phone_clean and len(phone_clean) == 10:
            url = f"{TRUE_API}?product-id-number={phone_clean}&product-id-name=msisdn"
        elif phone_clean and len(phone_clean) == 13:
            url = f"{TRUE_API}?product-id-number={phone_clean}&product-id-name=citizen-id"
        else:
            return None
        
        headers = {"channel_alias": "WHS", "employeeid": self.user}
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

# ==================== TPMAP SERVICE ====================
class TPMAPService:
    def __init__(self):
        self.cookies = None
        self.load_cookies()
    
    def load_cookies(self):
        try:
            decoded = base64.b64decode(TPMAP_COOKIES_B64).decode('utf-8')
            cookies_list = eval(decoded)
            self.cookies = {}
            for cookie in cookies_list:
                self.cookies[cookie['name']] = cookie['value']
            print(f"✅ TPMAP cookies loaded: {len(self.cookies)} items")
            return True
        except Exception as e:
            print(f"❌ Error loading TPMAP cookies: {e}")
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
        if not keyword or not self.cookies:
            return None, None
        
        session = requests.Session()
        session.cookies.update(self.cookies)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://logbook.tpmap.in.th",
            "Referer": "https://logbook.tpmap.in.th/table",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        clean_keyword = re.sub(r'\D', '', keyword)
        payload = {
            "draw": 3,
            "columns[0][data]": "house_data_ID",
            "columns[1][data]": "village_ID",
            "columns[2][data]": "NID",
            "columns[3][data]": "name",
            "columns[4][data]": "village_name",
            "columns[5][data]": "status",
            "start": 0,
            "length": 50,
            "search[value]": "",
            "search[regex]": "false",
            "prov": "",
            "amp": "",
            "tam": "",
            "NID": clean_keyword if len(clean_keyword) == 13 else "",
            "fullname": keyword if not (clean_keyword and len(clean_keyword) == 13) else "",
            "firstname": "",
            "lastname": ""
        }
        
        try:
            people_res = session.post(
                "https://api2.logbook.emenscr.in.th/people/find",
                data=payload,
                headers=headers,
                timeout=10
            )
            people = people_res.json().get("data", []) if people_res.status_code == 200 else []
            
            welfare_res = session.post(
                "https://api2.logbook.emenscr.in.th/mofwelfare/find",
                data=payload,
                headers=headers,
                timeout=10
            )
            welfare = welfare_res.json().get("data", []) if welfare_res.status_code == 200 else []
            
            for person in people:
                person['formatted_address'] = self.build_full_address(person)
            
            return people, welfare
        except Exception as e:
            print(f"TPMAP API error: {e}")
            return None, None

# ==================== INITIALIZE SERVICES ====================
print("=" * 60)
print("Initializing EasySearch Services (with GitHub Releases)")
print("=" * 60)

gambling_manager = GamblingDataManager()
shipmile_manager = ShipmileDataManager()
true_service = TruePortalService()
tpmap_service = TPMAPService()

print(f"\n📊 System Status:")
print(f"   🎰 Gambling: {len(gambling_manager.data)} records")
print(f"   🚚 Shipmile: {len(shipmile_manager.data)} records")
print(f"   📱 True Portal: {'✅ Cookies loaded' if true_service.cookies else '❌'}")
print(f"   🏛️ TPMAP: {'✅ Cookies loaded' if tpmap_service.cookies else '❌'}")
print("=" * 60)

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
    
    results = {
        'keyword': keyword,
        'system': system,
        'timestamp': datetime.now().isoformat(),
        'data': {}
    }
    
    if system == 'all' or system == 'true':
        true_data = true_service.search(keyword)
        results['data']['true_portal'] = {
            'status': 'success' if true_data else 'not_found',
            'data': true_data
        }
    
    if system == 'all' or system == 'tpmap':
        people, welfare = tpmap_service.search(keyword)
        results['data']['tpmap'] = {
            'status': 'success' if people else 'not_found',
            'people': people,
            'welfare': welfare
        }
    
    if system == 'all' or system == 'ship':
        ship_data = shipmile_manager.search(keyword)
        results['data']['shipmile'] = {
            'status': 'success' if ship_data else 'not_found',
            'count': len(ship_data),
            'data': ship_data[:10]
        }
    
    if system == 'all' or system == 'gambling':
        gambling_data = gambling_manager.search(keyword)
        results['data']['gambling'] = {
            'status': 'success' if gambling_data else 'not_found',
            'count': len(gambling_data),
            'data': gambling_data[:50]
        }
    
    return jsonify(results)

@app.route('/api/status', methods=['GET'])
def api_status():
    gambling_stats = gambling_manager.get_statistics()
    status = {
        'shipmile': {'loaded': len(shipmile_manager.data) > 0, 'records': len(shipmile_manager.data)},
        'true_portal': {'authenticated': bool(true_service.cookies)},
        'tpmap': {'authenticated': bool(tpmap_service.cookies)},
        'gambling': {
            'loaded': len(gambling_manager.data) > 0,
            'records': gambling_stats['total'],
            'active': gambling_stats['active_count']
        },
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

# HTML Template (ย่อเพื่อความยาว - ใช้ template เดิมได้)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EasySearch - ระบบค้นหาข้อมูล</title>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Kanit', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .search-box { background: white; border-radius: 20px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .radio-group { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; }
        .radio-group label { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: #f0f0f0; border-radius: 30px; cursor: pointer; }
        .search-input-area { display: flex; gap: 15px; margin-bottom: 20px; }
        .search-input { flex: 1; padding: 15px 20px; border: 2px solid #ddd; border-radius: 30px; font-size: 16px; font-family: 'Kanit', sans-serif; }
        .search-btn { padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 30px; cursor: pointer; font-size: 16px; font-weight: 600; }
        .status { padding: 15px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
        .results { background: white; border-radius: 20px; padding: 20px; min-height: 400px; }
        .result-card { border: 1px solid #e0e0e0; border-radius: 10px; margin-bottom: 20px; overflow: hidden; }
        .result-header { background: #f8f9fa; padding: 15px 20px; font-weight: 600; border-bottom: 2px solid #667eea; }
        .result-body { padding: 20px; overflow-x: auto; }
        .member-table { width: 100%; border-collapse: collapse; }
        .member-table th, .member-table td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
        .json-viewer { background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: monospace; font-size: 12px; }
        .loading { text-align: center; padding: 50px; }
        .spinner { width: 50px; height: 50px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-search"></i> AtomSearch</h1>
            <p>ระบบค้นหาข้อมูลอัจฉริยะ | รองรับ 4 ระบบ</p>
        </div>
        
        <div class="search-box">
            <div class="radio-group">
                <label><input type="radio" name="system" value="all" checked> ค้นหาทั้งหมด</label>
                <label><input type="radio" name="system" value="true"> True CRM</label>
                <label><input type="radio" name="system" value="tpmap"> TPMAP</label>
                <label><input type="radio" name="system" value="ship"> Shipmile</label>
                <label><input type="radio" name="system" value="gambling"> เว็บพนัน</label>
            </div>
            <div class="search-input-area">
                <input type="text" id="keyword" class="search-input" placeholder="ชื่อ, เบอร์โทรศัพท์, หรือเลขบัตรประชาชน...">
                <button id="searchBtn" class="search-btn"><i class="fas fa-search"></i> ค้นหา</button>
            </div>
            <div class="status" id="statusBar">
                <i class="fas fa-check-circle" style="color: #28a745;"></i> พร้อมใช้งาน
            </div>
            <div class="stats" id="statsArea">
                <div class="stat-card">กำลังโหลดข้อมูล...</div>
            </div>
        </div>
        
        <div class="results">
            <h3><i class="fas fa-chart-line"></i> ผลการค้นหา</h3>
            <div id="resultCount" style="margin: 10px 0; color: #666;">รอการค้นหา</div>
            <div id="resultsContainer">
                <div style="text-align: center; padding: 50px; color: #999;">
                    <i class="fas fa-info-circle fa-3x"></i>
                    <p>กรุณากรอกข้อมูลที่ต้องการค้นหา</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let isSearching = false;
        
        document.getElementById('searchBtn').onclick = performSearch;
        document.getElementById('keyword').onkeypress = function(e) {
            if (e.key === 'Enter') performSearch();
        };
        
        async function performSearch() {
            if (isSearching) return;
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) {
                updateStatus('กรุณากรอกข้อมูล', 'warning');
                return;
            }
            const system = document.querySelector('input[name="system"]:checked').value;
            isSearching = true;
            const searchBtn = document.getElementById('searchBtn');
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> กำลังค้นหา...';
            document.getElementById('resultsContainer').innerHTML = '<div class="loading"><div class="spinner"></div><p>กำลังค้นหาข้อมูล...</p></div>';
            updateStatus('กำลังค้นหา: ' + keyword, 'info');
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({keyword, system})
                });
                const data = await response.json();
                displayResults(data);
                updateStatus('ค้นหาสำเร็จ', 'success');
            } catch (error) {
                updateStatus('เกิดข้อผิดพลาด', 'error');
            } finally {
                isSearching = false;
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search"></i> ค้นหา';
            }
        }
        
        function displayResults(data) {
            const container = document.getElementById('resultsContainer');
            let html = ''; let total = 0;
            
            if (data.data) {
                if (data.data.gambling?.data?.length) {
                    total += data.data.gambling.count;
                    html += createGamblingCard(data.data.gambling);
                }
                if (data.data.true_portal?.data) {
                    total += 1;
                    html += createResultCard('True CRM', data.data.true_portal.data);
                }
                if (data.data.tpmap?.people?.length) {
                    total += data.data.tpmap.people.length;
                    html += createResultCard('TPMAP', data.data.tpmap);
                }
                if (data.data.shipmile?.data?.length) {
                    total += data.data.shipmile.count;
                    html += createResultCard('Shipmile', data.data.shipmile);
                }
                if (total === 0) html = '<div style="text-align:center; padding:50px;">ไม่พบข้อมูล</div>';
            }
            container.innerHTML = html;
            document.getElementById('resultCount').innerHTML = `พบ ${total} รายการ`;
        }
        
        function createGamblingCard(data) {
            let html = `<div class="result-card"><div class="result-header">🎰 เว็บพนัน (${data.count} รายการ)</div><div class="result-body"><table class="member-table"><thead><tr><th>รหัส</th><th>ชื่อ-นามสกุล</th><th>เบอร์โทร</th><th>ธนาคาร</th><th>เลขบัญชี</th></tr></thead><tbody>`;
            data.data.slice(0, 20).forEach(item => {
                html += `<tr><td>${item['รหัสสมาชิก'] || '-'}</td><td>${item['ชื่อ-นามสกุล'] || '-'}</td><td>${item['เบอร์โทรศัพท์'] || '-'}</td><td>${item['ธนาคาร'] || '-'}</td><td>${item['เลขบัญชี'] || '-'}</td></tr>`;
            });
            html += `</tbody></table></div></div>`;
            return html;
        }
        
        function createResultCard(title, data) {
            return `<div class="result-card"><div class="result-header">${title}</div><div class="result-body"><div class="json-viewer"><pre>${JSON.stringify(data, null, 2)}</pre></div></div></div>`;
        }
        
        async function loadStats() {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                document.getElementById('statsArea').innerHTML = `
                    <div class="stat-card">🎰 เว็บพนัน: ${status.gambling.records.toLocaleString()} รายการ</div>
                    <div class="stat-card">🚚 Shipmile: ${status.shipmile.records.toLocaleString()} รายการ</div>
                    <div class="stat-card">📱 True CRM: ${status.true_portal.authenticated ? '✅ พร้อม' : '⚠️ ไม่พร้อม'}</div>
                    <div class="stat-card">🏛️ TPMAP: ${status.tpmap.authenticated ? '✅ พร้อม' : '⚠️ ไม่พร้อม'}</div>
                `;
            } catch(e) {}
        }
        
        function updateStatus(msg, type) {
            const bar = document.getElementById('statusBar');
            const icon = type === 'error' ? 'exclamation-circle' : 'info-circle';
            bar.innerHTML = `<i class="fas fa-${icon}"></i> ${msg}`;
        }
        
        loadStats();
        setInterval(loadStats, 60000);
    </script>
</body>
</html>
'''

app.debug = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)