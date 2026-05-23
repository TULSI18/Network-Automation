# =========================================================
# FINAL STABLE NETWORK DISCOVERY + SSH AUDIT TOOL (FINAL VERSION)
# =========================================================

import ipaddress
import socket
import pandas as pd
import paramiko
import time
import warnings

from icmplib import ping
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings(action="ignore")

NETWORK = "10.101.64.0/20"

CREDENTIALS = [
    ("tulsi", "tul$!@2020"),
    ("admin", "Dr3@mB1gg@2026")
]

OUTPUT_FILE = "network_discovery_report-BSNL.xlsx"

PING_TIMEOUT = 1
SSH_TIMEOUT = 15
MAX_THREADS = 20

def ping_host(ip):
    try:
        result = ping(str(ip), count=1, timeout=PING_TIMEOUT)
        return result.is_alive
    except:
        return False

def check_ssh(ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((str(ip), 22))
        sock.close()
        return result == 0
    except:
        return False

def ssh_login(ip):
    for username, password in CREDENTIALS:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=str(ip),
                username=username,
                password=password,
                timeout=SSH_TIMEOUT,
                banner_timeout=20,
                auth_timeout=20,
                look_for_keys=False,
                allow_agent=False
            )
            return client, username
        except Exception:
            continue
    return None, None

def get_device_info(client):
    try:
        shell = client.invoke_shell()
        time.sleep(3)

        while shell.recv_ready():
            shell.recv(65535).decode(errors="ignore")

        shell.send("terminal length 0\n")
        time.sleep(2)
        while shell.recv_ready():
            shell.recv(65535).decode(errors="ignore")

        # Show version
        shell.send("show version\n")
        time.sleep(5)
        version_output = ""
        while shell.recv_ready():
            version_output += shell.recv(65535).decode(errors="ignore")

        # Hostname
        shell.send("show running-config | include hostname\n")
        time.sleep(3)
        hostname_output = ""
        while shell.recv_ready():
            hostname_output += shell.recv(65535).decode(errors="ignore")

        # Interfaces
        shell.send("show ip interface brief\n")
        time.sleep(3)
        int_output = ""
        while shell.recv_ready():
            int_output += shell.recv(65535).decode(errors="ignore")

        # Inventory for model
        shell.send("show inventory\n")
        time.sleep(5)
        inventory_output = ""
        while shell.recv_ready():
            inventory_output += shell.recv(65535).decode(errors="ignore")

        # Detect device type
        combined_output = (version_output + hostname_output).lower()
        device_type = "Unknown"
        if any(x in combined_output for x in ["router","isr","asr","csr","ios xe","cisco ios"]):
            device_type = "Router"
        elif any(x in combined_output for x in ["switch","catalyst","nexus","2960","3560","3750","3850","9300","9400"]):
            device_type = "Switch"
        elif any(x in combined_output for x in ["linux","ubuntu","debian","centos","redhat"]):
            device_type = "Linux"

        # Hostname detection
        hostname = "Unknown"
        for line in hostname_output.splitlines():
            line = line.strip()
            if line.lower().startswith("hostname"):
                parts = line.split()
                if len(parts) >= 2:
                    hostname = parts[1]
                    break
        if hostname == "Unknown":
            for line in reversed(version_output.splitlines()):
                line = line.strip()
                if line.endswith("#"):
                    hostname = line.replace("#", "").strip()
                    if len(hostname) < 50 and " " not in hostname:
                        break

        # Parse interfaces including subinterfaces
        interfaces = {
            "GigabitEthernet0/0/0": {"IP": "", "Status": ""},
            "GigabitEthernet0/0/1": {"IP": "", "Status": ""},
            "GigabitEthernet0/0/2": {"IP": "", "Status": ""},
            "GigabitEthernet0/0/1.51": {"IP": "", "Status": ""},
            "GigabitEthernet0/0/1.52": {"IP": "", "Status": ""}
        }
        for line in int_output.splitlines():
            parts = line.split()
            if len(parts) >= 6:
                iface, ip, _, _, _, status = parts[:6]
                if iface in interfaces:
                    interfaces[iface]["IP"] = ip
                    interfaces[iface]["Status"] = status

        # Parse model from inventory
        model = "Unknown"
        for line in inventory_output.splitlines():
            line = line.strip()
            if "PID:" in line and "VID:" in line:
                parts = line.split(",")
                for p in parts:
                    if p.strip().startswith("PID:"):
                        model = p.replace("PID:", "").strip()
                        break
                if model != "Unknown":
                    break

        return device_type, hostname, interfaces, model

    except Exception as e:
        print(f"Device Info Error : {e}")
        return "Unknown", "Unknown", {}, "Unknown"

def process_ip(ip):
    ip = str(ip)
    result = {
        "IP Address": ip,
        "Ping Status": "Down",
        "SSH Status": "No",
        "Login Status": "Failed",
        "Username Used": "",
        "Device Type": "",
        "Hostname": "",
        "GigabitEthernet0/0/0 IP": "",
        "GigabitEthernet0/0/0 Status": "",
        "GigabitEthernet0/0/1 IP": "",
        "GigabitEthernet0/0/1 Status": "",
        "GigabitEthernet0/0/2 IP": "",
        "GigabitEthernet0/0/2 Status": "",
        "GigabitEthernet0/0/1.51 IP": "",
        "GigabitEthernet0/0/1.51 Status": "",
        "GigabitEthernet0/0/1.52 IP": "",
        "GigabitEthernet0/0/1.52 Status": "",
        "Model Number": ""
    }

    print(f"Checking {ip}")

    if not ping_host(ip):
        return result
    result["Ping Status"] = "Alive"

    if not check_ssh(ip):
        return result
    result["SSH Status"] = "Enabled"

    client, username = ssh_login(ip)
    if client is None:
        return result
    result["Login Status"] = "Success"
    result["Username Used"] = username

    device_type, hostname, interfaces, model = get_device_info(client)
    result["Device Type"] = device_type
    result["Hostname"] = hostname
    if interfaces:
        for iface, data in interfaces.items():
            result[f"{iface} IP"] = data["IP"]
            result[f"{iface} Status"] = data["Status"]
    result["Model Number"] = model

    client.close()
    return result

def main():
    print("\n================================================")
    print(f"SCANNING NETWORK : {NETWORK}")
    print("================================================\n")

    network = ipaddress.ip_network(NETWORK, strict=False)
    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_ip, ip) for ip in network.hosts()]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error : {e}")

    df = pd.DataFrame(results)
    df = df.sort_values(by=["Ping Status", "SSH Status"], ascending=False)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
        print("\n================================================")
        print(f"REPORT SAVED : {OUTPUT_FILE}")
        print("================================================")
    except PermissionError:
        print("\n================================================")
        print("ERROR : Excel File Already Open")
        print("Please Close Excel File First")
        print("================================================")

    end_time = time.time()
    print(f"\nTotal IPs Checked : {len(results)}")
    print(f"Time Taken : {round(end_time - start_time, 2)} Seconds")
    print("\n================================================")

if __name__ == "__main__":
    main()
