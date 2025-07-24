import requests
import time

RAPIDAPI_KEY = "014231d572mshc403b5b906f78e5p1e4285jsnc9ce7e6b871f"

API_URL = "https://judge0-ce.p.rapidapi.com/submissions"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "Content-Type": "application/json"
}

def submit_code(source_code, language_id, stdin=""):
    payload = {
        "language_id": language_id,
        "source_code": source_code,
        "stdin": stdin
    }

    response = requests.post(API_URL + "?base64_encoded=false&wait=false", headers=HEADERS, json=payload)
    
    if response.status_code == 201:
        token = response.json()["token"]
    else:
        raise Exception("Submission failed: " + response.text)

    for _ in range(10):
        result_response = requests.get(f"{API_URL}/{token}?base64_encoded=false", headers=HEADERS)
        result = result_response.json()
        if result.get("status", {}).get("description") not in ["In Queue", "Processing"]:
            return result
        time.sleep(1)

    raise TimeoutError("Execution took too long.")


def get_language_id(language):
    mapping = {
        "python": 71,
        "cpp": 54,
        "java": 62,
        "javascript": 63
    }
    return mapping.get(language)
