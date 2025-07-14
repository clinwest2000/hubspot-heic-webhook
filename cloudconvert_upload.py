import cloudconvert
import requests
from io import BytesIO
import os

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")

# Configure CloudConvert
cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)


def convert_heic_to_jpg_cloudconvert(file_url, file_name):
    print(f"🔗 Converting from URL: {file_url}")
    print(f"Converting {file_name} via CloudConvert...")

    # STEP 1: Download file WITHOUT authorization (HubSpot URL is already signed)
    print(f"⬇️  Downloading from {file_url} with auth header", flush=True)
    headers = {'Authorization': f'Bearer {HUBSPOT_API_KEY}'}
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()
    file_data = response.content

    # STEP 2: Upload to CloudConvert via direct file upload
    upload_task = cloudconvert.Task.create_upload()
    upload_url = upload_task["result"]["form"]["url"]
    upload_params = upload_task["result"]["form"]["parameters"]

    files = {
        'file': (file_name, file_data)
    }

    upload_response = requests.post(upload_url, data=upload_params, files=files)
    upload_response.raise_for_status()

    # STEP 3: Create conversion job
    job = cloudconvert.Job.create(payload={
        "tasks": {
            "import-upload": {
                "operation": "import/upload",
                "task": upload_task["id"]
            },
            "convert-my-file": {
                "operation": "convert",
                "input": "import-upload",
                "output_format": "jpg"
            },
            "export-my-file": {
                "operation": "export/url",
                "input": "convert-my-file"
            }
        }
    })

    # STEP 4: Wait for conversion and download result
    job = cloudconvert.Job.wait(id=job['id'])
    export_task = [task for task in job["tasks"] if task["name"] == "export-my-file"][0]
    converted_file_url = export_task['result']['files'][0]['url']

    jpg_response = requests.get(converted_file_url)
    jpg_response.raise_for_status()

    return BytesIO(jpg_response.content), file_name.replace('.heic', '.jpg')


def upload_file_to_hubspot(file_data, file_name):
    print(f"Uploading {file_name} to HubSpot...")
    url = 'https://api.hubapi.com/files/v3/files'
    headers = {'Authorization': f'Bearer {HUBSPOT_API_KEY}'}
    files = {
        'file': (file_name, file_data, 'image/jpeg'),
    }
    data = {
        "options": '{"access": "PUBLIC_INDEXABLE"}',
        "name": file_name,
        "ttl": "P3M"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json()
