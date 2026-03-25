from flask import Flask, render_template_string, request, jsonify
import requests
import json
import re
from datetime import datetime

app = Flask(__name__)

# ==================== CONFIG ====================
GAMBLING_DATA_URL = "https://github.com/Atom88888881/search/releases/download/w/gambling_data.json"
SHIPMILE_DATA_URL = "https://github.com/Atom88888881/search/releases/download/w/shipsmile_address.json"

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
TPMAP_COOKIES = {
    "_pk_ses.2.6367": "1",
    "_pk_id.2.6367": "13b47b74aa573555.1774459253."
}

# ==================== DATA MANAGERS ====================
class GamblingDataManager:
    def __init__(self):
        self.data = []
        self.load_from_url()
    
    def load_from_url(self):
        try:
            print(f"📥 Downloading gambling data...")
            response = requests.get(GAMBLING_DATA_URL, timeout=60)
            if response.status_code == 200:
                json_data = response.json()
                if isinstance(json_data, dict) and "data" in json_data:
                    self.data = json_data["data"]
                elif isinstance(json_data, list):
                    self.data = json_data
                print(f"✅ Gambling: {len(self.data)} records")
        except Exception as e:
            print(f"❌ Gambling error: {e}")
    
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

class ShipmileDataManager:
    def __init__(self):
        self.data = []
        self.load_from_url()
    
    def load_from_url(self):
        try:
            print(f"📥 Downloading shipmile data...")
            response = requests.get(SHIPMILE_DATA_URL, timeout=60)
            if response.status_code == 200:
                self.data = response.json()
                print(f"✅ Shipmile: {len(self.data)} records")
        except Exception as e:
            print(f"❌ Shipmile error: {e}")
    
    def search(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for item in self.data:
            name = str(item.get('name', '')).lower()
            phone = str(item.get('phone', '')).lower()
            address = str(item.get('address', '')).lower()
            if keyword_lower in name or keyword_lower in phone or keyword_lower in address:
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
        self.cookies = TPMAP_COOKIES
    
    def build_full_address(self, data):
        parts = []
        address_num = str(data.get("address_num", "")) if data.get("address_num") else ""
        if address_num and address_num != "-":
            parts.append(address_num)
        moo = str(data.get("moo", "")) if data.get("moo") else ""
        if moo and moo != "-":
            parts.append(f"หมู่ {moo}")
        village_name = str(data.get("village_name", "")) if data.get("village_name") else ""
        if village_name and village_name != "-":
            parts.append(village_name)
        tumbol_name = str(data.get("tumbol_name", "")) if data.get("tumbol_name") else ""
        if tumbol_name and tumbol_name != "-":
            parts.append(f"ต.{tumbol_name}")
        ampuhur_name = str(data.get("ampuhur_name", "")) if data.get("ampuhur_name") else ""
        if ampuhur_name and ampuhur_name != "-":
            parts.append(f"อ.{ampuhur_name}")
        province_name = str(data.get("province_name", "")) if data.get("province_name") else ""
        if province_name and province_name != "-":
            parts.append(f"จ.{province_name}")
        zipcode = str(data.get("zipcode", "")) if data.get("zipcode") else ""
        if zipcode and zipcode != "-":
            parts.append(zipcode)
        return " ".join(parts) if parts else "ไม่มีข้อมูลที่อยู่"
    
    def search(self, keyword):
        if not keyword:
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
            people = []
            if people_res.status_code == 200:
                people_data = people_res.json()
                people = people_data.get("data", [])
            
            welfare_res = session.post(
                "https://api2.logbook.emenscr.in.th/mofwelfare/find",
                data=payload,
                headers=headers,
                timeout=10
            )
            welfare = []
            if welfare_res.status_code == 200:
                welfare_data = welfare_res.json()
                welfare = welfare_data.get("data", [])
            
            for person in people:
                person['formatted_address'] = self.build_full_address(person)
            
            return people, welfare
        except Exception as e:
            print(f"❌ TPMAP error: {e}")
            return None, None

# ==================== INITIALIZE ====================
gambling_manager = GamblingDataManager()
shipmile_manager = ShipmileDataManager()
true_service = TruePortalService()
tpmap_service = TPMAPService()

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    results = {
        'keyword': keyword,
        'timestamp': datetime.now().isoformat(),
        'data': {}
    }
    
    # True CRM
    true_data = true_service.search(keyword)
    results['data']['true_portal'] = true_data if true_data else None
    
    # TPMAP
    people, welfare = tpmap_service.search(keyword)
    results['data']['tpmap'] = {
        'people': people if people else [],
        'welfare': welfare if welfare else []
    }
    
    # Shipmile
    ship_data = shipmile_manager.search(keyword)
    results['data']['shipmile'] = {
        'count': len(ship_data),
        'data': ship_data[:10]
    }
    
    # Gambling
    gambling_data = gambling_manager.search(keyword)
    results['data']['gambling'] = {
        'count': len(gambling_data),
        'data': gambling_data[:50]
    }
    
    return jsonify(results)

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes, viewport-fit=cover">
    <title>ระบบค้นหาข้อมูลส่วนบุคคล</title>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: 'Kanit', sans-serif;
            background: #0a0a0a;
            min-height: 100vh;
            padding: 16px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* Header */
        .header {
            text-align: center;
            color: white;
            margin-bottom: 24px;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.7;
            color: #aaa;
        }
        
        /* Search Box */
        .search-box {
            background: #1a1a1a;
            border-radius: 24px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 1px solid #2a2a2a;
        }
        
        .search-input-area {
            display: flex;
            gap: 12px;
            margin-bottom: 0;
        }
        
        .search-input {
            flex: 1;
            padding: 14px 18px;
            border: 2px solid #2a2a2a;
            border-radius: 50px;
            font-size: 16px;
            font-family: 'Kanit', sans-serif;
            background: #0a0a0a;
            color: white;
            transition: all 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-input::placeholder {
            color: #555;
        }
        
        .search-btn {
            padding: 14px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            font-family: 'Kanit', sans-serif;
            transition: transform 0.2s;
        }
        
        .search-btn:active {
            transform: scale(0.97);
        }
        
        .search-btn:disabled {
            opacity: 0.7;
            transform: none;
        }
        
        /* Results */
        .results {
            background: #1a1a1a;
            border-radius: 24px;
            padding: 20px;
            min-height: 400px;
            border: 1px solid #2a2a2a;
        }
        
        .results-header {
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid #2a2a2a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .results-header h3 {
            font-size: 18px;
            font-weight: 600;
            color: white;
        }
        
        .result-count {
            color: #aaa;
            font-size: 14px;
            background: #0a0a0a;
            padding: 4px 12px;
            border-radius: 20px;
        }
        
        /* Result Cards */
        .result-card {
            border: 1px solid #2a2a2a;
            border-radius: 16px;
            margin-bottom: 20px;
            overflow: hidden;
            background: #0f0f0f;
        }
        
        .result-header {
            background: linear-gradient(135deg, #1f1f2f 0%, #15151f 100%);
            padding: 14px 18px;
            font-weight: 600;
            font-size: 16px;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
            color: white;
        }
        
        .result-header i {
            font-size: 20px;
        }
        
        .result-body {
            padding: 16px;
        }
        
        /* Info Row */
        .info-row {
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .info-label {
            font-weight: 600;
            color: #aaa;
            font-size: 13px;
            margin-bottom: 4px;
        }
        
        .info-value {
            font-size: 15px;
            color: white;
            word-break: break-word;
        }
        
        /* Table for Gambling/Shipmile */
        .data-table {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .data-table table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        .data-table th {
            background: #0a0a0a;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            color: #aaa;
            border-bottom: 1px solid #2a2a2a;
        }
        
        .data-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #2a2a2a;
            color: #ddd;
        }
        
        /* Person Card for TPMAP */
        .person-card {
            background: #0a0a0a;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            border: 1px solid #2a2a2a;
        }
        
        .person-card:last-child {
            margin-bottom: 0;
        }
        
        /* Loading */
        .loading {
            text-align: center;
            padding: 50px 20px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #2a2a2a;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 50px 20px;
            color: #666;
        }
        
        .empty-state i {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        
        /* Status Bar */
        .status-bar {
            background: #0a0a0a;
            padding: 10px 16px;
            border-radius: 12px;
            margin-top: 12px;
            font-size: 13px;
            color: #aaa;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Mobile Optimizations */
        @media (max-width: 600px) {
            body {
                padding: 12px;
            }
            
            .search-input-area {
                flex-direction: column;
            }
            
            .search-btn {
                width: 100%;
            }
            
            .result-header {
                font-size: 14px;
                padding: 12px 14px;
            }
            
            .result-body {
                padding: 12px;
            }
            
            .data-table th,
            .data-table td {
                padding: 8px 6px;
                font-size: 12px;
            }
        }
        
        /* Badge */
        .badge {
            display: inline-block;
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }
        
        /* Welfare Section */
        .welfare-section {
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid #2a2a2a;
        }
        
        .welfare-title {
            font-weight: 600;
            font-size: 13px;
            color: #aaa;
            margin-bottom: 8px;
        }
        
        .json-preview {
            background: #0a0a0a;
            padding: 10px;
            border-radius: 8px;
            font-size: 11px;
            font-family: monospace;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
            color: #aaa;
            border: 1px solid #2a2a2a;
        }
        
        /* Popup Modal */
        .popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }
        
        .popup-modal {
            background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
            border-radius: 32px;
            padding: 32px 24px;
            max-width: 320px;
            width: 85%;
            text-align: center;
            border: 1px solid rgba(102, 126, 234, 0.3);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            animation: slideUp 0.3s ease;
        }
        
        .popup-icon {
            font-size: 64px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
        }
        
        .popup-modal h2 {
            color: white;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .popup-modal p {
            color: #aaa;
            font-size: 14px;
            margin-bottom: 24px;
            line-height: 1.5;
        }
        
        .follow-btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: linear-gradient(135deg, #E4405F 0%, #D62976 100%);
            color: white;
            padding: 14px 28px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            font-family: 'Kanit', sans-serif;
            transition: transform 0.2s;
            margin-bottom: 16px;
        }
        
        .follow-btn:active {
            transform: scale(0.97);
        }
        
        .follow-btn i {
            font-size: 20px;
        }
        
        .skip-btn {
            background: transparent;
            border: none;
            color: #666;
            font-size: 13px;
            cursor: pointer;
            font-family: 'Kanit', sans-serif;
            padding: 8px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-search"></i>
                AtomSearch
            </h1>
            <p>ค้นหาข้อมูลส่วนบุคคล ใช้งานฟรี</p>
        </div>
        
        <div class="search-box">
            <div class="search-input-area">
                <input type="text" id="keyword" class="search-input" placeholder="ชื่อ, เบอร์โทรศัพท์, หรือเลขบัตรประชาชน..." autocomplete="off">
                <button id="searchBtn" class="search-btn">
                    <i class="fas fa-search"></i> ค้นหา
                </button>
            </div>
            <div class="status-bar" id="statusBar">
                <i class="fas fa-check-circle" style="color: #28a745;"></i>
                <span>พร้อมใช้งาน</span>
            </div>
        </div>
        
        <div class="results">
            <div class="results-header">
                <h3><i class="fas fa-chart-line"></i> ผลการค้นหา</h3>
                <span class="result-count" id="resultCount">รอการค้นหา</span>
            </div>
            <div id="resultsContainer">
                <div class="empty-state">
                    <i class="fas fa-info-circle"></i>
                    <p>กรุณากรอกข้อมูลที่ต้องการค้นหา</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let isSearching = false;
        
        const searchBtn = document.getElementById('searchBtn');
        const keywordInput = document.getElementById('keyword');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultCountSpan = document.getElementById('resultCount');
        const statusBar = document.getElementById('statusBar');
        
        // Popup Instagram
        function showPopup() {
            const popup = document.createElement('div');
            popup.className = 'popup-overlay';
            popup.id = 'igPopup';
            popup.innerHTML = `
                <div class="popup-modal">
                    <div class="popup-icon">
                        <i class="fab fa-instagram"></i>
                    </div>
                    <h2>ติดตามก่อนใช้งาน</h2>
                    <p>กรุณากดติดตามด้วยไอสัส</p>
                    <a href="https://www.instagram.com/eedok.4/" target="_blank" class="follow-btn" id="followBtn">
                        <i class="fab fa-instagram"></i>
                        ติดตามบน Instagram
                    </a>
                    <br>
                </div>
            `;
            document.body.appendChild(popup);
            
            const followBtn = document.getElementById('followBtn');
            const skipBtn = document.getElementById('skipBtn');
            
            followBtn.addEventListener('click', function() {
                localStorage.setItem('ig_followed', 'true');
                setTimeout(() => {
                    popup.remove();
                }, 500);
            });
            
            skipBtn.addEventListener('click', function() {
                popup.remove();
            });
        }
        
        // ตรวจสอบว่ากดติดตามแล้วหรือยัง
        if (!localStorage.getItem('ig_followed')) {
            showPopup();
        }
        
        searchBtn.onclick = performSearch;
        keywordInput.onkeypress = function(e) {
            if (e.key === 'Enter') performSearch();
        };
        
        function updateStatus(msg, isError = false) {
            statusBar.innerHTML = `
                <i class="fas fa-${isError ? 'exclamation-circle' : 'check-circle'}" style="color: ${isError ? '#dc3545' : '#28a745'}"></i>
                <span>${msg}</span>
            `;
        }
        
        async function performSearch() {
            if (isSearching) return;
            
            const keyword = keywordInput.value.trim();
            if (!keyword) {
                updateStatus('กรุณากรอกข้อมูล', true);
                return;
            }
            
            isSearching = true;
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> กำลังค้นหา...';
            resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>กำลังค้นหาข้อมูล...</p></div>';
            resultCountSpan.textContent = 'กำลังค้นหา...';
            updateStatus('กำลังค้นหา: ' + keyword);
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({keyword})
                });
                const data = await response.json();
                displayResults(data);
                updateStatus('ค้นหาสำเร็จ');
            } catch (error) {
                console.error(error);
                resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>เกิดข้อผิดพลาด กรุณาลองใหม่</p></div>';
                updateStatus('เกิดข้อผิดพลาด', true);
            } finally {
                isSearching = false;
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search"></i> ค้นหา';
            }
        }
        
        function displayResults(data) {
            let html = '';
            let total = 0;
            
            // True CRM
            if (data.data.true_portal) {
                total++;
                html += createTrueCard(data.data.true_portal);
            }
            
            // TPMAP
            if (data.data.tpmap.people && data.data.tpmap.people.length > 0) {
                total += data.data.tpmap.people.length;
                html += createTPMAPCard(data.data.tpmap);
            }
            
            // Shipmile
            if (data.data.shipmile.data && data.data.shipmile.data.length > 0) {
                total += data.data.shipmile.count;
                html += createShipmileCard(data.data.shipmile);
            }
            
            // Gambling
            if (data.data.gambling.data && data.data.gambling.data.length > 0) {
                total += data.data.gambling.count;
                html += createGamblingCard(data.data.gambling);
            }
            
            if (total === 0) {
                html = '<div class="empty-state"><i class="fas fa-user-slash"></i><p>ไม่พบข้อมูล</p></div>';
                resultCountSpan.textContent = 'ไม่พบข้อมูล';
            } else {
                resultCountSpan.textContent = `พบ ${total} รายการ`;
            }
            
            resultsContainer.innerHTML = html;
        }
        
        function createTrueCard(data) {
            let html = `<div class="result-card">
                <div class="result-header">
                    <i class="fas fa-mobile-alt" style="color: #0066cc;"></i>
                    <span>📱 True CRM</span>
                </div>
                <div class="result-body">`;
            
            if (Array.isArray(data)) {
                data.forEach(item => {
                    html += `<div class="info-row">
                        <div class="info-label">ชื่อ-นามสกุล</div>
                        <div class="info-value">${item['display-name-th'] || item['full-name'] || '-'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">เบอร์โทรศัพท์</div>
                        <div class="info-value">${item['msisdn'] || '-'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">เลขบัตรประชาชน</div>
                        <div class="info-value">${item['citizen-id'] || '-'}</div>
                    </div>`;
                });
            } else {
                html += `<div class="info-row">
                    <div class="info-label">ข้อมูล</div>
                    <div class="json-preview">${JSON.stringify(data, null, 2)}</div>
                </div>`;
            }
            
            html += `</div></div>`;
            return html;
        }
        
        function createTPMAPCard(data) {
            let html = `<div class="result-card">
                <div class="result-header">
                    <i class="fas fa-landmark" style="color: #28a745;"></i>
                    <span>🏛️ TPMAP (${data.people.length} คน)</span>
                </div>
                <div class="result-body">`;
            
            data.people.forEach((person, idx) => {
                html += `<div class="person-card">
                    <div class="info-row">
                        <div class="info-label">ชื่อ-นามสกุล</div>
                        <div class="info-value"><strong>${person.name || '-'}</strong></div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">เลขบัตรประชาชน</div>
                        <div class="info-value">${person.NID || '-'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">ที่อยู่</div>
                        <div class="info-value">${person.formatted_address || '-'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">สถานะ</div>
                        <div class="info-value"><span class="badge">${person.status || '-'}</span></div>
                    </div>`;
                
                if (person.house_data_ID) {
                    html += `<div class="info-row">
                        <div class="info-label">รหัสบ้าน</div>
                        <div class="info-value">${person.house_data_ID}</div>
                    </div>`;
                }
                html += `</div>`;
            });
            
            if (data.welfare && data.welfare.length > 0) {
                html += `<div class="welfare-section">
                    <div class="welfare-title"><i class="fas fa-hand-holding-heart"></i> ข้อมูลสวัสดิการ (${data.welfare.length} รายการ)</div>
                    <div class="json-preview">${JSON.stringify(data.welfare, null, 2)}</div>
                </div>`;
            }
            
            html += `</div></div>`;
            return html;
        }
        
        function createShipmileCard(data) {
            let html = `<div class="result-card">
                <div class="result-header">
                    <i class="fas fa-truck" style="color: #ff9800;"></i>
                    <span>🚚 Shipmile (${data.count} รายการ)</span>
                </div>
                <div class="result-body">
                    <div class="data-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>ชื่อ</th>
                                    <th>เบอร์โทร</th>
                                    <th>ที่อยู่</th>
                                </tr>
                            </thead>
                            <tbody>`;
            
            data.data.forEach(item => {
                html += `<tr>
                    <td>${escapeHtml(item.name || '-')}</td>
                    <td>${item.phone || '-'}</td>
                    <td>${escapeHtml(item.address || '-')}</td>
                </tr>`;
            });
            
            html += `</tbody>
                        </table>
                    </div>
                </div>
            </div>`;
            return html;
        }
        
        function createGamblingCard(data) {
            let html = `<div class="result-card">
                <div class="result-header">
                    <i class="fas fa-dice" style="color: #9c27b0;"></i>
                    <span>🎰 เว็บพนัน (${data.count} รายการ)</span>
                </div>
                <div class="result-body">
                    <div class="data-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>รหัส</th>
                                    <th>ชื่อ-สกุล</th>
                                    <th>เบอร์โทร</th>
                                    <th>ธนาคาร</th>
                                    <th>เลขบัญชี</th>
                                </tr>
                            </thead>
                            <tbody>`;
            
            data.data.slice(0, 30).forEach(item => {
                html += `<tr>
                    <td>${item['รหัสสมาชิก'] || '-'}</td>
                    <td>${item['ชื่อ-นามสกุล'] || '-'}</td>
                    <td>${item['เบอร์โทรศัพท์'] || item['เบอร์โทรศัพท์_10หลัก'] || '-'}</td>
                    <td>${item['ธนาคาร'] || '-'}</td>
                    <td>${item['เลขบัญชี'] || '-'}</td>
                </tr>`;
            });
            
            if (data.count > 30) {
                html += `<tr><td colspan="5" style="text-align:center; color:#666;">แสดง 30 จาก ${data.count} รายการ</td></tr>`;
            }
            
            html += `</tbody>
                        </table>
                    </div>
                </div>
            </div>`;
            return html;
        }
        
        function escapeHtml(str) {
            if (!str) return '-';
            return str.replace(/[&<>]/g, function(m) {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
