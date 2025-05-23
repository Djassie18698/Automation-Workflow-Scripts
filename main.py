import os
import subprocess
import getpass
from pathlib import Path

# === CONFIG ===
ROOT = Path(__file__).parent.resolve()
SSH_KEY = Path.home() / ".ssh" / "surfspotkey"
SSH_PUB = SSH_KEY.with_suffix(".pub")
INVENTORY = ROOT / "inventory.ini"
PLAYBOOK = ROOT / "setup_vm.yml"
DATA_DIR = ROOT / "data"
IDFINDER = ROOT / "IDFinder_basic.py"

# === Globals (passed to Ansible)
ssh_user = ""
github_user = ""
github_token = ""
surf_api_key = ""

# === Step 1: Ask for all credentials
def ask_credentials():
    global ssh_user, github_user, github_token, surf_api_key
    ssh_user = input("👤 Enter your SSH username for the VM (e.g. dean): ").strip()
    github_user = input("🐙 Enter your GitHub username: ").strip()
    github_token = getpass.getpass("🔐 Enter your GitHub token: ").strip()
    surf_api_key = getpass.getpass("🔐 Enter your SURF API key: ").strip()

# === Step 2: Ensure SSH key exists (generate if not)
def ensure_ssh_key():
    if SSH_KEY.exists() and SSH_PUB.exists():
        print("✅ SSH key already exists.")
        return
    print("🔐 Generating new SSH key: surfspotkey")
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", str(SSH_KEY), "-N", ""])
    print("\n📋 Your public key (upload this to SURFspot):\n")
    with open(SSH_PUB, "r") as f:
        print(f.read())
    input("📥 Press Enter after uploading your key...")

# === Step 3: Run IDFinder to get IP + update inventory
def run_idfinder():
    print("🔍 Running IDFinder...")
    env = os.environ.copy()
    env["ANSIBLE_SSH_USER"] = ssh_user
    result = subprocess.run(["python3", str(IDFINDER)], env=env)
    if result.returncode != 0:
        print("❌ IDFinder failed.")
        exit(1)


# === Step 4: Extract last IP from inventory.ini
def get_last_ip_from_inventory():
    if not INVENTORY.exists():
        print("❌ inventory.ini not found.")
        exit(1)
    ip = None
    with open(INVENTORY, "r") as f:
        capture = False
        for line in f:
            line = line.strip()
            if line == "[myhosts]":
                capture = True
                continue
            if capture and line:
                ip = line
    if not ip:
        print("❌ No IP found in inventory.")
        exit(1)
    return ip

# === Step 5: Run Ansible playbook
def run_ansible(ip):
    print(f"🚀 Running Ansible playbook on {ip} as {ssh_user}...")
    cmd = [
        "ansible-playbook",
        "-i", str(INVENTORY),
        str(PLAYBOOK),
        "-u", ssh_user,
        "--private-key", str(SSH_KEY),
        "-e", f"github_user={github_user}",
        "-e", f"github_token={github_token}",
        "-e", f"surf_api_key={surf_api_key}"
    ]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("✅ Ansible playbook completed successfully.")
    else:
        print("❌ Ansible playbook failed.")

# === MAIN ENTRY POINT ===
def main():
    ask_credentials()
    ensure_ssh_key()
    run_idfinder()
    ip = get_last_ip_from_inventory()
    run_ansible(ip)

if __name__ == "__main__":
    main()
