# app.py - EasySearch (TPMAP, Shipmile, Gambling)
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import re
from datetime import datetime

app = Flask(__name__)

# ==================== CONFIG ====================
# GitHub Releases URLs
GAMBLING_DATA_URL = "https://github.com/Atom88888881/search/releases/download/w/gambling_data.json"
SHIPMILE_DATA_URL = "https://github.com/Atom88888881/search/releases/download/w/shipsmile_address.json"

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
            print(f"📥 Downloading gambling data from: {GAMBLING_DATA_URL}")
            response = requests.get(GAMBLING_DATA_URL, timeout=60)
            if response.status_code == 200:
                json_data = response.json()
                if isinstance(json_data, dict) and "data" in json_data:
                    self.data = json_data["data"]
                elif isinstance(json_data, list):
                    self.data = json_data
                print(f"✅ Gambling data loaded: {len(self.data)} records")
            else:
                print(f"❌ Failed to load: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error loading gambling data: {e}")
    
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
        return {'total': len(self.data)}

class ShipmileDataManager:
    def __init__(self):
        self.data = []
        self.load_from_url()
    
    def load_from_url(self):
        try:
            print(f"📥 Downloading shipmile data from: {SHIPMILE_DATA_URL}")
            response = requests.get(SHIPMILE_DATA_URL, timeout=60)
            if response.status_code == 200:
                self.data = response.json()
                print(f"✅ Shipmile data loaded: {len(self.data)} records")
        except Exception as e:
            print(f"❌ Error loading shipmile data: {e}")
    
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
            parts.append(f"ตำบล {tumbol_name}")
        ampuhur_name = str(data.get("ampuhur_name", "")) if data.get("ampuhur_name") else ""
        if ampuhur_name and ampuhur_name != "-":
            parts.append(f"อำเภอ {ampuhur_name}")
        province_name = str(data.get("province_name", "")) if data.get("province_name") else ""
        if province_name and province_name != "-":
            parts.append(f"จังหวัด {province_name}")
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
            print(f"❌ TPMAP API error: {e}")
            return None, None

# ==================== INITIALIZE SERVICES ====================
gambling_manager = GamblingDataManager()
shipmile_manager = ShipmileDataManager()
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

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'shipmile': {'records': len(shipmile_manager.data)},
        'gambling': {'records': gambling_manager.get_statistics()['total']},
        'tpmap': {'configured': True},
        'timestamp': datetime.now().isoformat()
    })

# HTML Template
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
        .search-input-area { display: flex; gap: 15px; margin-bottom: 20px; }
        .search-input { flex: 1; padding: 15px 20px; border: 2px solid #ddd; border-radius: 30px; font-size: 16px; font-family: 'Kanit', sans-serif; }
        .search-btn { padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 30px; cursor: pointer; font-size: 16px; font-weight: 600; }
        .status { padding: 15px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px; }
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
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-search"></i> AtomSearch</h1>
            <p>ระบบค้นหาข้อมูลอัจฉริยะ | TPMAP | Shipmile | เว็บพนัน</p>
        </div>
        
        <div class="search-box">
            <div class="search-input-area">
                <input type="text" id="keyword" class="search-input" placeholder="ชื่อ, เบอร์โทรศัพท์, หรือเลขบัตรประชาชน...">
                <button id="searchBtn" class="search-btn"><i class="fas fa-search"></i> ค้นหา</button>
            </div>
            <div class="status" id="statusBar">
                <i class="fas fa-check-circle"></i> พร้อมใช้งาน
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
                    body: JSON.stringify({keyword})
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
            let html = '';
            let total = 0;
            
            // TPMAP
            if (data.data.tpmap.people && data.data.tpmap.people.length) {
                total += data.data.tpmap.people.length;
                html += createTPMAPCard(data.data.tpmap);
            }
            
            // Shipmile
            if (data.data.shipmile.data && data.data.shipmile.data.length) {
                total += data.data.shipmile.count;
                html += createShipmileCard(data.data.shipmile);
            }
            
            // Gambling
            if (data.data.gambling.data && data.data.gambling.data.length) {
                total += data.data.gambling.count;
                html += createGamblingCard(data.data.gambling);
            }
            
            if (total === 0) {
                html = '<div style="text-align:center; padding:50px;">ไม่พบข้อมูล</div>';
            }
            
            container.innerHTML = html;
            document.getElementById('resultCount').innerHTML = `พบ ${total} รายการ`;
        }
        
        function createTPMAPCard(data) {
            let html = `<div class="result-card"><div class="result-header">🏛️ TPMAP (${data.people.length} คน)</div><div class="result-body">`;
            data.people.forEach(p => {
                html += `<div style="margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #eee;">
                            <strong>ชื่อ:</strong> ${p.name || '-'}<br>
                            <strong>เลขบัตร:</strong> ${p.NID || '-'}<br>
                            <strong>ที่อยู่:</strong> ${p.formatted_address || '-'}<br>
                            <strong>สถานะ:</strong> ${p.status || '-'}
                         </div>`;
            });
            if (data.welfare && data.welfare.length) {
                html += `<div style="margin-top: 20px;"><strong>ข้อมูลสวัสดิการ:</strong><pre style="background:#f0f0f0;padding:10px;margin-top:5px;">${JSON.stringify(data.welfare, null, 2)}</pre></div>`;
            }
            html += `</div></div>`;
            return html;
        }
        
        function createShipmileCard(data) {
            let html = `<div class="result-card"><div class="result-header">🚚 Shipmile (${data.count} รายการ)</div><div class="result-body"><table class="member-table"><thead><tr><th>ชื่อ</th><th>เบอร์โทร</th><th>ที่อยู่</th></tr></thead><tbody>`;
            data.data.forEach(item => {
                html += `<tr><td>${item.name || '-'}</td><td>${item.phone || '-'}</td><td>${item.address || '-'}</td></tr>`;
            });
            html += `</tbody></table></div></div>`;
            return html;
        }
        
        function createGamblingCard(data) {
            let html = `<div class="result-card"><div class="result-header">🎰 เว็บพนัน (${data.count} รายการ)</div><div class="result-body"><table class="member-table"><thead><tr><th>รหัสสมาชิก</th><th>ชื่อ-นามสกุล</th><th>เบอร์โทร</th><th>ธนาคาร</th><th>เลขบัญชี</th></tr></thead><tbody>`;
            data.data.slice(0, 20).forEach(item => {
                html += `<tr>
                            <td>${item['รหัสสมาชิก'] || '-'}</td>
                            <td>${item['ชื่อ-นามสกุล'] || '-'}</td>
                            <td>${item['เบอร์โทรศัพท์'] || '-'}</td>
                            <td>${item['ธนาคาร'] || '-'}</td>
                            <td>${item['เลขบัญชี'] || '-'}</td>
                         </tr>`;
            });
            html += `</tbody></table></div></div>`;
            return html;
        }
        
        async function loadStats() {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                document.getElementById('statsArea').innerHTML = `
                    <div class="stat-card">🎰 เว็บพนัน: ${status.gambling.records.toLocaleString()} รายการ</div>
                    <div class="stat-card">🚚 Shipmile: ${status.shipmile.records.toLocaleString()} รายการ</div>
                    <div class="stat-card">🏛️ TPMAP: พร้อมใช้งาน</div>
                `;
            } catch(e) {}
        }
        
        function updateStatus(msg, type) {
            const bar = document.getElementById('statusBar');
            bar.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i> ${msg}`;
        }
        
        loadStats();
        setInterval(loadStats, 60000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
