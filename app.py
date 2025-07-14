from flask import Flask, request, jsonify
import requests
from cloudconvert_upload import convert_heic_to_jpg_cloudconvert, upload_file_to_hubspot
import os

import os

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")

app = Flask(__name__)

API_BASE = 'https://api.hubapi.com'

HEADERS = {
    'Authorization': f'Bearer {HUBSPOT_API_KEY}',
    'Content-Type': 'application/json'
}

def get_note_by_id(note_id):
    url = f"{API_BASE}/crm/v3/objects/notes/{note_id}"
    params = {"properties": "hs_attachment_ids", "associations": "contact,deal,company"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_file_metadata(file_id):
    url = f"{API_BASE}/files/v3/files/{file_id}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()

def get_download_url_legacy(file_id):
    url = f"{API_BASE}/filemanager/api/v2/files/{file_id}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    meta = res.json()
    return meta.get("url")

@app.route("/hubspot-webhook", methods=["POST"])
def handle_note_created():
    print("🔥 /hubspot-webhook HIT", flush=True)

    try:
        print("📦 Raw body:", request.data, flush=True)
        json_data = request.get_json(force=True)
        print("📦 Parsed JSON:", json_data, flush=True)
    except Exception as e:
        print("❌ Failed to parse JSON:", str(e), flush=True)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"🛠 Flask is starting on port: {port}")
    app.run(host="0.0.0.0", port=port)
