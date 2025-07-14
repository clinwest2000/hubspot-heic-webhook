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

def get_download_url(file_id):
    """
    Returns a signed, public URL for any HubSpot file (even note attachments).
    """
    url = f"{API_BASE}/files/v3/files/{file_id}/url"
    headers = {
        'Authorization': f'Bearer {HUBSPOT_API_KEY}',
        'Content-Type': 'application/json'
    }
    res = requests.post(url, headers=headers)
    res.raise_for_status()
    return res.json().get("url")


@app.route("/hubspot-webhook", methods=["POST"])
def handle_note_created():
    print("🔥 /hubspot-webhook was hit!", flush=True)
    print("📦 Raw payload:", request.data, flush=True)
    print("📦 Parsed JSON:", request.get_json(silent=True), flush=True)

    data = request.get_json(silent=True) or []

    for event in data:
        note_id = event.get("objectId")
        if not note_id:
            continue

        print(f"📩 Received webhook for Note ID: {note_id}", flush=True)

        try:
            note = get_note_by_id(note_id)
            attachment_ids = note.get("properties", {}).get("hs_attachment_ids", "")
            if not attachment_ids:
                print("No attachments found.", flush=True)
                continue

            for file_id in attachment_ids.split(';'):
                file_id = file_id.strip()
                metadata = get_file_metadata(file_id)
                filename = metadata.get('name', '').lower()
                mime_type = metadata.get("mimeType", "")

                is_heic = (
                    filename.endswith('.heic')
                    or mime_type in ['image/heic', 'image/heif']
                    or ('.' not in filename and len(filename) == 36)
                )

                if not is_heic:
                    continue

                file_url = get_download_url(file_id)
                print(f"📝 Converting {filename} from {file_url}", flush=True)
                converted_file, new_file_name = convert_heic_to_jpg_cloudconvert(file_url, filename)
                upload_result = upload_file_to_hubspot(converted_file, new_file_name)
                print(f"✅ Uploaded JPG: {upload_result['url']}", flush=True)

        except Exception as e:
            print(f"❌ Error processing note {note_id}: {str(e)}", flush=True)

    return jsonify({"status": "ok"})



if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"🛠 Flask is starting on port: {port}")
    app.run(host="0.0.0.0", port=port)
