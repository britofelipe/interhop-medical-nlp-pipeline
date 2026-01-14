import requests
import os
import time

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def check_health():
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return resp.status_code == 200
    except:
        return False

def upload_document(file_bytes, filename, content_type):
    files = {"file": (filename, file_bytes, content_type)}
    response = requests.post(f"{BACKEND_URL}/documents/upload", files=files)
    response.raise_for_status()
    return response.json() # Returns doc info with ID

def get_document_list(validated=None):
    params = {}
    if validated is not None:
        params["validated"] = str(validated).lower()
        
    resp = requests.get(f"{BACKEND_URL}/documents/", params=params)
    resp.raise_for_status()
    return resp.json()

def get_document_file_bytes(document_id):
    resp = requests.get(f"{BACKEND_URL}/documents/{document_id}/file")
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type")

def poll_status(document_id):
    """Loops until status is completed or failed."""
    while True:
        resp = requests.get(f"{BACKEND_URL}/documents/{document_id}/status")
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data["status"] == "completed":
            return data
        if data["status"] == "failed":
            raise Exception("Le traitement du document a échoué.")
        
        
        time.sleep(1) # Wait 1 second before checking again

def get_document_status_simple(document_id):
    """Checks status once (non-blocking)."""
    try:
        resp = requests.get(f"{BACKEND_URL}/documents/{document_id}/status", timeout=2)
        if resp.status_code == 200:
            return resp.json()["status"]
    except:
        pass
    return None

def get_results(document_id):
    resp = requests.get(f"{BACKEND_URL}/documents/{document_id}/result")
    resp.raise_for_status()
    return resp.json()

def validate_results(document_id, correct_data):
    resp = requests.put(f"{BACKEND_URL}/documents/{document_id}/validate", json={"structured_json": correct_data, "is_validated": True})
    resp.raise_for_status()
    return resp.json()

