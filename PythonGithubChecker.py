import requests
import json
import time
import os
import random
import string

# === CONFIGURATION ===
GITHUB_FILE_URL = "https://api.github.com/repos/Djassie18698/AnsibleTest/commits?path=done.txt&sha=main"
API_URL = "https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/"
API_KEY = "5489d9fc169ae40148a2cfbf1644a130f891e37f964d34e60f22fb50c5272289"
JSON_PAYLOAD_FILE = "workspace_config_surftest_no_storage.json"
LAST_COMMIT_FILE = "last_commit.txt"
NAME_LOG_FILE = "last_workspace_names.txt"
CHECK_INTERVAL = 10  # seconds

HEADERS = {
    "accept": "application/json;Compute",
    "authorization": f"{API_KEY}",
    "Content-Type": "application/json;Compute"
}

def get_latest_commit_hash():
    try:
        response = requests.get(GITHUB_FILE_URL)
        response.raise_for_status()
        return response.json()[0]["sha"]
    except Exception as e:
        print(f"❌ Failed to fetch commit for done.txt: {e}")
        return None

def read_last_commit():
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, "r") as f:
            return f.read().strip()
    return ""

def write_last_commit(commit_hash):
    with open(LAST_COMMIT_FILE, "w") as f:
        f.write(commit_hash)

def generate_random_name(prefix="surftest", length=5):
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}-{random_suffix}"

def log_workspace_name(name):
    old_content = ""
    if os.path.exists(NAME_LOG_FILE):
        with open(NAME_LOG_FILE, "r") as f:
            old_content = f.read()
    with open(NAME_LOG_FILE, "w") as f:
        f.write(name + "\n" + old_content)

def send_workspace_request():
    try:
        with open(JSON_PAYLOAD_FILE, "r") as json_file:
            payload = json.load(json_file)

        random_name = generate_random_name()
        payload["meta"]["host_name"] = random_name
        payload["name"] = random_name

        response = requests.post(API_URL, headers=HEADERS, json=payload)

        print(f"🖥️  Sent workspace: {random_name}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(response.text)

        log_workspace_name(random_name)

    except Exception as e:
        print(f"❌ Error sending workspace request: {e}")

def main():
    print("🔍 Monitoring done.txt on GitHub for changes... (press Ctrl+C to stop)")
    try:
        while True:
            latest_commit = get_latest_commit_hash()
            if latest_commit:
                last_commit = read_last_commit()
                if latest_commit != last_commit:
                    print(f"🆕 New commit detected: {latest_commit}")
                    send_workspace_request()
                    write_last_commit(latest_commit)
                else:
                    print("⏸ No new update.")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n👋 Script stopped by user (Ctrl+C)")

if __name__ == "__main__":
    main()
