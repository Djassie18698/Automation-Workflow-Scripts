import requests, json, os, random, string

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

API_URL = "https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/"
API_KEY = "5489d9fc169ae40148a2cfbf1644a130f891e37f964d34e60f22fb50c5272289"

JSON_PAYLOAD_FILE = os.path.join(DATA_DIR, "workspace_config_surftest_no_storage.json")
NAME_LOG_FILE = os.path.join(DATA_DIR, "last_workspace_names.txt")
LAST_COMMIT_FILE = os.path.join(DATA_DIR, "last_commit.txt")

HEADERS = {
    "accept": "application/json;Compute",
    "authorization": f"{API_KEY}",
    "Content-Type": "application/json;Compute"
}

def generate_random_name(prefix="surftest", length=5):
    return f"{prefix}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def log_workspace_name(name):
    old = ""
    if os.path.exists(NAME_LOG_FILE):
        with open(NAME_LOG_FILE, "r") as f:
            old = f.read()
    with open(NAME_LOG_FILE, "w") as f:
        f.write(name + "\n" + old)

def write_placeholder_commit():
    with open(LAST_COMMIT_FILE, "w") as f:
        f.write("manual-test-placeholder")

def send_workspace_request():
    try:
        with open(JSON_PAYLOAD_FILE, "r") as f:
            payload = json.load(f)
        name = generate_random_name()
        payload["meta"]["host_name"] = name
        payload["name"] = name
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code in [200, 201, 202]:
            log_workspace_name(name)
            write_placeholder_commit()
            print(f"\n✅ Workspace '{name}' created.\n")
        else:
            print(f"\n❌ Failed to create workspace '{name}'")
            print("Details:", response.status_code, response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_workspace_request()
