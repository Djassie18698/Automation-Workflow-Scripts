import requests
import json
import os
import time
from datetime import datetime, timezone
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# === CONFIGURATION ===
API_URL = "https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/"
API_KEY = "5489d9fc169ae40148a2cfbf1644a130f891e37f964d34e60f22fb50c5272289"
NAME_LOG_FILE = "last_workspace_names.txt"
OUTPUT_LOG_FILE = "workspace_ip_lookup.json"
INVENTORY_FILE = "/home/dean/ansible/inventory.ini"
INVENTORY_GROUP = "myhosts"

HEADERS = {
    "accept": "application/json;Compute",
    "authorization": f"{API_KEY}"
}

# === FUNCTIONS ===

def get_last_workspace_name():
    try:
        with open(NAME_LOG_FILE, "r") as f:
            return f.readline().strip()
    except Exception as e:
        print(Fore.RED + f"❌ Could not read workspace name: {e}")
        return None

def find_workspace_info(name):
    try:
        params = {
            "application_type": "Compute",
            "deleted": "false"
        }
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        for ws in response.json().get("results", []):
            if ws.get("name") == name:
                return {
                    "id": ws["id"],
                    "status": ws["status"],
                    "created": ws["time_created"],
                    "fqdn": ws["meta"].get("workspace_fqdn", ""),
                    "name": ws["name"]
                }
        return None
    except Exception as e:
        print(Fore.RED + f"❌ Error finding workspace info: {e}")
        return None

def get_ip_by_id(workspace_id, max_retries=30, delay=20):
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_URL}{workspace_id}/", headers=HEADERS)
            response.raise_for_status()
            ip = response.json().get("resource_meta", {}).get("ip", "")
            if ip:
                return ip
            else:
                print(Fore.YELLOW + f"⏳ IP not yet assigned. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(delay)
        except Exception as e:
            print(Fore.RED + f"❌ Error fetching IP (attempt {attempt + 1}): {e}")
            time.sleep(delay)
    print(Fore.RED + "❌ Max retries reached. IP was not assigned.")
    return ""

def save_json(data):
    try:
        with open(OUTPUT_LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(Fore.GREEN + f"📝 Output saved to: {OUTPUT_LOG_FILE}")
    except Exception as e:
        print(Fore.RED + f"❌ Failed to save JSON: {e}")

def print_summary(data):
    print(Fore.CYAN + "\n📦 Workspace Summary:")
    print(Fore.YELLOW + f"  Name:         {Fore.WHITE}{data['name']}")
    print(Fore.YELLOW + f"  ID:           {Fore.WHITE}{data['workspace_id']}")
    print(Fore.YELLOW + f"  Status:       {Fore.WHITE}{data['status']}")
    print(Fore.YELLOW + f"  Created:      {Fore.WHITE}{data['created']}")
    print(Fore.YELLOW + f"  FQDN:         {Fore.WHITE}{data['fqdn']}")
    print(Fore.YELLOW + f"  IP Address:   {Fore.WHITE}{data['ip']}")
    print(Fore.YELLOW + f"  Logged at:    {Fore.WHITE}{data['timestamp']}")

def append_ip_to_inventory(ip, group=INVENTORY_GROUP, path=INVENTORY_FILE):
    try:
        # Check if IP is already listed
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
                if ip in content:
                    print(Fore.BLUE + f"ℹ️  IP {ip} already in inventory.")
                    return

        lines = []
        if os.path.exists(path):
            with open(path, "r") as f:
                lines = f.readlines()

        # Ensure group header exists
        if not any(line.strip() == f"[{group}]" for line in lines):
            lines.append(f"\n[{group}]\n")

        lines.append(f"{ip}\n")

        with open(path, "w") as f:
            f.writelines(lines)

        print(Fore.GREEN + f"📋 IP {ip} added to inventory: {path}")
    except Exception as e:
        print(Fore.RED + f"❌ Failed to update inventory: {e}")

# === MAIN ===

if __name__ == "__main__":
    name = get_last_workspace_name()
    if name:
        ws_info = find_workspace_info(name)
        if ws_info:
            ip = get_ip_by_id(ws_info["id"], max_retries=30, delay=20)
            log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": ws_info["name"],
                "workspace_id": ws_info["id"],
                "status": ws_info["status"],
                "created": ws_info["created"],
                "fqdn": ws_info["fqdn"],
                "ip": ip or "Not yet assigned"
            }
            save_json(log)
            print_summary(log)
            if ip:
                append_ip_to_inventory(ip)
        else:
            print(Fore.RED + "❌ Workspace info not found.")
    else:
        print(Fore.RED + "❌ No workspace name available.")
