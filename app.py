from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re
import base64

app = Flask(__name__)
CORS(app)

groq_client = None
workbook = None

try:
    from groq import Groq
    groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
except:
    pass

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ.get('GCP_CREDENTIALS', '{}')),
        ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    )
    workbook = gspread.authorize(creds).open(os.environ.get('SPREADSHEET_NAME', 'Sales-CRM-Database'))
except:
    pass

@app.route('/')
def home():
    return jsonify({'status': 'ok'})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ai_ready': groq_client is not None,
        'sheets_connected': workbook is not None
    })

@app.route('/api/extract', methods=['POST'])
def extract():
    try:
        text = request.json.get('text', '')
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": 'Extract as JSON: {"contact_name":"","organization":"","phone":"","email":"","products":"","quantity":"","budget":"","timeline":"","next_action":"","next_action_date":"","notes":""}'},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        result = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            result = match.group()
        data = json.loads(result)
        if data.get('products'):
            data['products'] = re.sub(r'\d+\s*[x×]\s*', '', data['products']).strip()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    try:
        audio = request.json.get('audio', '').split(',')[1] if ',' in request.json.get('audio', '') else request.json.get('audio', '')
        with open('/tmp/a.wav', 'wb') as f:
            f.write(base64.b64decode(audio))
        with open('/tmp/a.wav', 'rb') as f:
            text = groq_client.audio.transcriptions.create(file=f, model="whisper-large-v3", response_format="text")
        os.remove('/tmp/a.wav')
        return jsonify({'success': True, 'text': text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save():
    try:
        from datetime import datetime
        data = request.json
        sheet = workbook.worksheet('Leads')
        lead_id = f"L-{datetime.now().year}-{len(sheet.get_all_values()):03d}"
        lead = data.get('lead_data', {})
        sheet.append_row([
            lead_id, datetime.now().strftime("%d-%b-%y"), datetime.now().strftime("%I:%M %p"),
            data.get('sales_rep', 'Unknown'), lead.get('contact_name', ''), lead.get('organization', ''),
            lead.get('phone', ''), lead.get('email', ''), lead.get('products', ''), lead.get('quantity', ''),
            lead.get('budget', ''), lead.get('timeline', ''), 'New', lead.get('next_action', ''),
            lead.get('next_action_date', ''), lead.get('notes', ''), 'Web'
        ])
        return jsonify({'success': True, 'lead_id': lead_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def stats():
    try:
        total = len(workbook.worksheet('Leads').get_all_values()) - 1
        return jsonify({'success': True, 'total_leads': total})
    except:
        return jsonify({'success': True, 'total_leads': 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
```

6. Click **"Commit changes"**

---

## **ABOUT PYTHON 3 SETTING:**

**YES, Python 3 is correct!** ✅

Docker was wrong. Python 3 is what you need.

---

## **NOW WAIT:**

Render will auto-redeploy in 3-4 minutes.

Watch the logs. Should see:
```
==> Build successful
==> Starting service
[INFO] Listening at: http://0.0.0.0:10000
