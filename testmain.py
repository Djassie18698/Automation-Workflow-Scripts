import os
import subprocess
from pathlib import Path

# === CONFIG ===
ROOT = Path(__file__).parent.resolve()
SSH_KEY = Path.home() / ".ssh" / "surfspotkey"
SSH_PUB = SSH_KEY.with_suffix(".pub")
INVENTORY = ROOT / "inventory.ini"
PLAYBOOK = ROOT / "setup_vm.yml"
DATA_DIR = ROOT / "data"
IDFINDER = ROOT / "IDFinder_basic.py"

# === PRE-FILLED TEST VALUES ===
ssh_user = "dnellessen"
github_user = "Djassie18698"
github_token = "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"
surf_api_key = "5489d9fc169ae40148a2cfbf1644a130f891e37f964d34e60f22fb50c5272289"

# === Step 1: Ensure SSH key exists
def ensure_ssh_key():
    if SSH_KEY.exists() and SSH_PUB.exists():
        print("✅ SSH key already exists.")
        return
    print("🔐 Generating SSH key: surfspotkey")
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", str(SSH_KEY), "-N", ""])
    print("\n📋 Public key (upload to SURFspot):\n")
    with open(SSH_PUB, "r") as f:
        print(f.read())
    input("📥 Press Enter after uploading your key...")

# === Step 2: Run IDFinder
def run_idfinder():
    print("🔍 Running IDFinder...")
    env = os.environ.copy()
    env["ANSIBLE_SSH_USER"] = ssh_user
    result = subprocess.run(["python3", str(IDFINDER)], env=env)
    if result.returncode != 0:
        print("❌ IDFinder failed.")
        exit(1)

# === Step 3: Extract last IP from inventory
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
                ip = line.split()[0]  # just the IP
    if not ip:
        print("❌ No IP found.")
        exit(1)
    return ip

# === Step 4: Run Ansible
def run_ansible(ip):
    print(f"🚀 Running Ansible on {ip} as {ssh_user}...")
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
        print("✅ Playbook completed.")
    else:
        print("❌ Playbook failed.")

# === MAIN ENTRY ===
def main():
    ensure_ssh_key()
    run_idfinder()
    ip = get_last_ip_from_inventory()
    run_ansible(ip)

if __name__ == "__main__":
    main()
