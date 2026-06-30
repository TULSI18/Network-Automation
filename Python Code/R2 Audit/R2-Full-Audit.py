# =========================================================
# CISCO SDWAN AUDIT TOOL - PRODUCTION PRODUCTION VERSION (ALL IPs)
# =========================================================

import pandas as pd
import paramiko
import socket
import time
import re
import os

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================================================
# INPUT / OUTPUT
# =========================================================

INPUT_FILE = r"E:\NOC\IP Addresses\All-R2-IP.xlsx"
OUTPUT_FOLDER = r"E:\NOC\Output"
timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, f"R2_SDWAN_Audit_Report_{timestamp}.xlsx")

# =========================================================
# SSH CREDENTIALS & SCALING CONFIG
# =========================================================

CREDENTIALS = [
    ("tulsi", "tul$!@2020"),
    ("admin", "Dr3@mB1gg@2026")
]

SSH_TIMEOUT = 15
MAX_THREADS = 40  # 400 routers ke liye parallel processing threads badha diye hain

# =========================================================
# COMMANDS
# =========================================================

COMMANDS = {
    "version": "show version",
    "cpu": "show processes cpu",
    "interfaces": "show ip interface brief",
    "interface_stats": "show interfaces",
    "running_config": "show running-config",
    "vrrp": "show vrrp all",
    "utd_status": "show utd engine status",
    "url_filter": "show running-config | section urlfilter",
    "ips_policy": "show running-config | include ips",
    "bgp_summary": "show ip bgp summary",
    "default_route": "show running-config | include ^ip route",
    "cdp_neighbors": "show cdp neighbors detail"
}

# =========================================================
# READ EXCEL (ALL ROWS - NO HEAD(5) LIMIT)
# =========================================================

df = pd.read_excel(INPUT_FILE)
df.columns = df.columns.str.strip()

# NOTE: 'df = df.head(5)' line ko permanently hata diya gaya hai taaki saari locations scan hon.

def convert_size(size_bytes):
    try:
        size_bytes = float(size_bytes)
        if size_bytes >= 1024 ** 4: return f"{round(size_bytes / (1024 ** 4), 2)} TB"
        elif size_bytes >= 1024 ** 3: return f"{round(size_bytes / (1024 ** 3), 2)} GB"
        elif size_bytes >= 1024 ** 2: return f"{round(size_bytes / (1024 ** 2), 2)} MB"
        elif size_bytes >= 1024: return f"{round(size_bytes / 1024, 2)} KB"
        else: return f"{round(size_bytes, 2)} Bytes"
    except:
        return ""

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
                banner_timeout=15,
                auth_timeout=15,
                look_for_keys=False,
                allow_agent=False
            )
            return client
        except:
            continue
    return None

# =========================================================
# SMART DYNAMIC COMMAND EXECUTION (FASTER WORK)
# =========================================================
def run_command(shell, command, max_wait=20):
    shell.send(command + "\n")
    time.sleep(0.4)  # Small buffer for router to respond
    
    output = ""
    start_time = time.time()
    
    while True:
        if shell.recv_ready():
            output += shell.recv(65535).decode(errors="ignore")
            start_time = time.time()  # Reset timeout timer on data receipt
        else:
            time.sleep(0.1)
            
        # Router prompt (# or >) detect hote hi loop break ho jayega (No blind sleep)
        lines = output.splitlines()
        if lines:
            last_line = lines[-1].strip()
            if last_line.endswith("#") or last_line.endswith(">"):
                break
                
        if time.time() - start_time > max_wait:
            break
            
    return output

# =========================================================
# PARSERS
# =========================================================

def parse_version(output):
    hostname, model, serial, ios, uptime, ram, nvram, flash = "", "", "", "", "", "", "", ""
    for line in output.splitlines():
        line = line.strip()
        if " uptime is " in line:
            hostname = line.split(" uptime is ")[0].strip()
            uptime = line.split(" uptime is ")[1].strip()
        if "Cisco IOS XE Software" in line:
            ios = line
        model_match = re.search(r'cisco\s+([A-Z0-9\-]+)', line, re.IGNORECASE)
        if model_match:
            detected_model = model_match.group(1)
            if detected_model.upper() not in ["IOS", "ISR", "XE", "SYSTEM", "ROUTER"]:
                model = f"Cisco {detected_model}"
        if "Processor board ID" in line:
            serial = line.split("Processor board ID")[-1].strip()
        if "bytes of memory" in line.lower():
            nums = re.findall(r'(\d+)', line)
            if nums:
                try: ram = convert_size(int(nums[0]) * 1024)
                except: pass
        if "non-volatile configuration memory" in line.lower():
            nums = re.findall(r'(\d+)', line)
            if nums:
                try:
                    val = int(nums[0])
                    nvram = convert_size(val * 1024 if "k bytes" in line.lower() else val * 1024 * 1024 if "m bytes" in line.lower() else val)
                except: pass
        if "bytes of physical memory" in line.lower():
            nums = re.findall(r'(\d+)', line)
            if nums:
                try: flash = convert_size(int(nums[0]) * 1024)
                except: pass
    return hostname, model, serial, ios, uptime, ram, nvram, flash

def parse_cpu(output):
    for line in output.splitlines():
        if "five minutes:" in line.lower():
            match = re.search(r'five minutes:\s*(\d+)%?', line, re.IGNORECASE)
            if match: return match.group(1) + "%"
    return ""

def check_utd(output):
    return "ON" if "engine is running" in output.lower() else "OFF"

def check_url_filter(output):
    return "Configured" if "urlfilter" in output.lower() else "Not Configured"

def check_ips(output):
    return "Configured" if "ips" in output.lower() else "Not Configured"

def parse_vrrp(vrrp_output):
    vrrp_map = {}
    current_interface = ""
    for line in vrrp_output.splitlines():
        line = line.strip()
        if line.startswith(("GigabitEthernet", "Vlan", "Port-channel")):
            current_interface = line.split()[0]
            if current_interface not in vrrp_map:
                vrrp_map[current_interface] = {"gateway": "", "role": ""}
        if "Master" in line and current_interface:
            vrrp_map[current_interface]["role"] = "MASTER"
        elif "Backup" in line and current_interface:
            vrrp_map[current_interface]["role"] = "BACKUP"
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
        if ip_match and current_interface:
            vrrp_map[current_interface]["gateway"] = ip_match.group(1)
    return vrrp_map

# =========================================================
# ROBUST INTERFACE & BANDWIDTH UTILIZATION PARSER
# =========================================================
def parse_interfaces(interface_output, run_output, interface_stats_output, vrrp_map):
    interface_data = []
    ip_map = {}
    status_map = {}
    utilization_map = {}

    # 1. Map Interface IPs and Statuses
    for line in interface_output.splitlines():
        parts = line.split()
        if len(parts) >= 6:
            iface = parts[0]
            ip_map[iface] = parts[1]
            status_map[iface] = f"{parts[4]}/{parts[5]}"

    # 2. Line-by-Line Parsing for Bandwidth and Traffic Rates
    current_iface = None
    bandwidth_bps = 0
    input_rate = 0
    output_rate = 0

    for line in interface_stats_output.splitlines():
        line_str = line.strip()
        
        if "is up" in line_str or "is down" in line_str or "administratively down" in line_str:
            parts = line_str.split()
            if parts:
                current_iface = parts[0]
                bandwidth_bps = 0
                input_rate = 0
                output_rate = 0

        if current_iface:
            bw_match = re.search(r'BW\s+(\d+)\s+Kbit', line_str)
            if bw_match:
                bandwidth_bps = int(bw_match.group(1)) * 1000
                
            in_match = re.search(r'5 minute input rate\s+(\d+)\s+bits/sec', line_str)
            if in_match:
                input_rate = int(in_match.group(1))
                
            out_match = re.search(r'5 minute output rate\s+(\d+)\s+bits/sec', line_str)
            if out_match:
                output_rate = int(out_match.group(1))
                
                # Calculate Utilization % instantly when rates are captured
                if bandwidth_bps > 0:
                    total_rate = input_rate + output_rate
                    util = round((total_rate / bandwidth_bps) * 100, 2)
                    utilization_map[current_iface] = f"{util}%"
                else:
                    utilization_map[current_iface] = "0.0%"

    # 3. Process Configuration Blocks
    blocks = run_output.split("interface ")
    for block in blocks:
        block = block.strip()
        if not block: continue
        lines = block.splitlines()
        interface_name = lines[0].strip()

        ignore_interfaces = ["Loopback", "Tunnel", "Null", "NVI", "Virtual-Template", "vasileft", "vasiright", 
                             "AppGigabitEthernet", "VirtualPortGroup", "Embedded-Service-Engine", "BDI", "EOBC"]
        if any(interface_name.startswith(item) for item in ignore_interfaces):
            continue

        description, bandwidth, vrf = "", "Default", "Global"

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("description"):
                description = line.replace("description", "").strip()
            elif re.search(r'^\s*bandwidth\s+\d+', line):
                bandwidth_match = re.search(r'bandwidth\s+(\d+)', line)
                if bandwidth_match:
                    bw_kbps = int(bandwidth_match.group(1))
                    bandwidth = f"{round(bw_kbps/1000000,2)} Gbps" if bw_kbps >= 1000000 else f"{round(bw_kbps/1000,2)} Mbps" if bw_kbps >= 1000 else f"{bw_kbps} Kbps"
            elif "vrf forwarding" in line:
                vrf = line.replace("vrf forwarding", "").strip()

        vrrp_gateway = vrrp_map.get(interface_name, {}).get("gateway", "")
        vrrp_role = vrrp_map.get(interface_name, {}).get("role", "")

        interface_data.append({
            "Interface": interface_name,
            "VRF": vrf,
            "Status": status_map.get(interface_name, "N/A"),
            "Configured IP": ip_map.get(interface_name, "unassigned"),
            "Description": description,
            "Bandwidth": bandwidth,
            "Utilization %": utilization_map.get(interface_name, "N/A"),
            "VRRP Gateway": vrrp_gateway,
            "VRRP Role": vrrp_role
        })

    return interface_data

# =========================================================
# ROUTE, BGP, CDP PARSERS
# =========================================================

def parse_bgp(output, district, block, hostname):
    bgp_data = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith(("Neighbor", "BGP", "Total", "For address family")) or line == "": continue
        parts = line.split()
        if len(parts) >= 9:
            try:
                neighbor_ip, remote_as, last_value = parts[0], parts[2], parts[-1]
                bgp_status, received_prefix = ("Established", last_value) if last_value.isdigit() else (last_value, "0")
                bgp_data.append({
                    "District": district, "Block": block, "Hostname": hostname,
                    "Neighbor IP": neighbor_ip, "Remote AS": remote_as, "BGP Status": bgp_status, "Received Prefix": received_prefix
                })
            except: pass
    return bgp_data

def parse_default_route(output, district, block, hostname):
    route_data = []
    found = False
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("ip route 0.0.0.0 0.0.0.0"):
            found = True
            parts = line.split()
            next_hop = parts[4] if len(parts) >= 5 else ""
            interface = parts[5] if len(parts) >= 6 else ""
            route_data.append({
                "District": district, "Block": block, "Hostname": hostname,
                "Default Route": "Configured", "Next Hop": next_hop, "Outgoing Interface": interface, "Config Line": line
            })
    if not found:
        route_data.append({
            "District": district, "Block": block, "Hostname": hostname,
            "Default Route": "Not Configured", "Next Hop": "", "Outgoing Interface": "", "Config Line": ""
        })
    return route_data

def parse_cdp(output, district, block, hostname):
    cdp_data = []
    device, local_int, remote_int, mgmt_ip, platform = "", "", "", "", ""
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Device ID:"): device = line.replace("Device ID:", "").strip()
        elif "IP address:" in line: mgmt_ip = line.split(":")[-1].strip()
        elif "Platform:" in line:
            try: platform = line.split("Platform:")[1].split(",")[0].strip()
            except: pass
        elif "Interface:" in line:
            try:
                local_int = line.split("Interface:")[1].split(",")[0].strip()
                remote_int = line.split("Port ID (outgoing port):")[1].strip()
            except: pass
            cdp_data.append({
                "District": district, "Block": block, "Hostname": hostname, "Local Interface": local_int,
                "Neighbor Device": device, "Neighbor IP": mgmt_ip, "Remote Port": remote_int, "Platform": platform
            })
    return cdp_data

def generate_wan_summary(district, block, hostname, interface_data):
    wan_data = []
    g000_ip, g001_ip = "", ""
    for item in interface_data:
        if item["Interface"] == "GigabitEthernet0/0/0": g000_ip = item["Configured IP"]
        elif item["Interface"] == "GigabitEthernet0/0/1": g001_ip = item["Configured IP"]
    
    missing = [iface for iface, ip in [("GigabitEthernet0/0/0", g000_ip), ("GigabitEthernet0/0/1", g001_ip)] if ip in ["", "unassigned"]]
    if missing:
        wan_data.append({
            "District": district, "Block": block, "Hostname": hostname,
            "GigabitEthernet0/0/0 IP": g000_ip, "GigabitEthernet0/0/1 IP": g001_ip, "Missing Interface": ", ".join(missing)
        })
    return wan_data

# =========================================================
# DATA COLLECTION WORKER
# =========================================================

def collect_data(row):
    district, block = row['District'], row['Block']
    ip_sequence = [row['GigEth0/0/0-Jio'], row['GigEth0/0/1-BSNL'], row['GigEth0/0/2-NIC']]
    ip_labels = ["Jio", "BSNL", "NIC"]

    summary = {
        "District": district, "Block": block, "Connected IP": "", "Connected Via": "", "Hostname": "",
        "Model": "", "Serial": "", "IOS Version": "", "Uptime": "", "RAM": "", "NVRAM": "", "FLASH": "",
        "CPU 5 Min": "", "UTD Engine": "", "URL Filtering": "", "IPS": "", "Login Status": "Failed"
    }

    interface_sheet, bgp_sheet, default_route_sheet, cdp_sheet, wan_summary_sheet = [], [], [], [], []

    for idx, ip in enumerate(ip_sequence):
        if pd.isna(ip): continue
        ip = str(ip).strip()
        if ip in ["", "-"]: continue

        print(f"Connecting -> {district} | {block} | {ip}")
        if not check_ssh(ip): continue

        client = ssh_login(ip)
        if client is None: continue

        try:
            shell = client.invoke_shell()
            time.sleep(1)
            while shell.recv_ready(): shell.recv(65535)

            run_command(shell, "terminal length 0", 5)
            outputs = {}

            for key, cmd in COMMANDS.items():
                outputs[key] = run_command(shell, cmd, max_wait=30 if key in ["running_config", "interface_stats"] else 12)

            hostname, model, serial, ios, uptime, ram, nvram, flash = parse_version(outputs["version"])
            cpu = parse_cpu(outputs["cpu"])
            vrrp_map = parse_vrrp(outputs["vrrp"])
            interface_data = parse_interfaces(outputs["interfaces"], outputs["running_config"], outputs["interface_stats"], vrrp_map)

            for item in interface_data:
                item.update({"District": district, "Block": block, "Hostname": hostname})
                interface_sheet.append(item)

            wan_summary_sheet.extend(generate_wan_summary(district, block, hostname, interface_data))
            bgp_sheet.extend(parse_bgp(outputs["bgp_summary"], district, block, hostname))
            default_route_sheet.extend(parse_default_route(outputs["default_route"], district, block, hostname))
            cdp_sheet.extend(parse_cdp(outputs["cdp_neighbors"], district, block, hostname))

            summary.update({
                "Connected IP": ip, "Connected Via": ip_labels[idx], "Hostname": hostname, "Model": model,
                "Serial": serial, "IOS Version": ios, "Uptime": uptime, "RAM": ram, "NVRAM": nvram, "FLASH": flash,
                "CPU 5 Min": cpu, "UTD Engine": check_utd(outputs["utd_status"]), "URL Filtering": check_url_filter(outputs["url_filter"]),
                "IPS": check_ips(outputs["ips_policy"]), "Login Status": "Success"
            })
            client.close()
            break
        except Exception as e:
            summary["Login Status"] = f"Error : {e}"
            print(f"ERROR on {ip} : {e}")
            try: client.close()
            except: pass

    return summary, interface_sheet, bgp_sheet, default_route_sheet, cdp_sheet, wan_summary_sheet

# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    start_time = time.time()
    summary_results, interface_results, bgp_results, default_route_results, cdp_results, wan_summary_results = [], [], [], [], [], []

    print("\n=======================================================")
    print("CISCO SDWAN AUDIT STARTED - SCALED FOR 400+ ROUTERS")
    print("=======================================================\n")

    # High Thread Pool Utilization for fast execution
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(collect_data, row) for _, row in df.iterrows()]
        for future in as_completed(futures):
            try:
                summary, interfaces, bgp_data, default_data, cdp_data, wan_summary = future.result()
                summary_results.append(summary)
                interface_results.extend(interfaces)
                bgp_results.extend(bgp_data)
                default_route_results.extend(default_data)
                cdp_results.extend(cdp_data)
                wan_summary_results.extend(wan_summary)
            except Exception as e:
                print(f"THREAD ERROR : {e}")

    # Create DataFrames
    summary_df = pd.DataFrame(summary_results)
    interface_df = pd.DataFrame(interface_results)
    bgp_df = pd.DataFrame(bgp_results)
    default_route_df = pd.DataFrame(default_route_results)
    cdp_df = pd.DataFrame(cdp_results)
    wan_summary_df = pd.DataFrame(wan_summary_results)

    if not interface_df.empty:
        interface_column_order = ["District", "Block", "Hostname", "Interface", "VRF", "Status", "Configured IP", "Description", "Bandwidth", "Utilization %", "VRRP Gateway", "VRRP Role"]
        interface_df = interface_df[interface_column_order]

    # Export to multi-sheet Excel
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        interface_df.to_excel(writer, sheet_name="Interfaces", index=False)
        bgp_df.to_excel(writer, sheet_name="BGP_Status", index=False)
        default_route_df.to_excel(writer, sheet_name="Default_Route", index=False)
        cdp_df.to_excel(writer, sheet_name="CDP_Neighbors", index=False)
        wan_summary_df.to_excel(writer, sheet_name="WAN_Link_Summary", index=False)

    end_time = time.time()
    print("\n=======================================================")
    print(f"PRODUCTION REPORT GENERATED : {OUTPUT_FILE}")
    print(f"TOTAL DEVICES PROCESSED : {len(summary_results)}")
    print(f"EXECUTION COMPLETED IN : {round((end_time - start_time)/60, 2)} Minutes")
    print("=======================================================\n")

if __name__ == "__main__":
    main()