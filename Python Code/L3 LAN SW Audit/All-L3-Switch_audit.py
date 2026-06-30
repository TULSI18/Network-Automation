from netmiko import ConnectHandler
from getpass import getpass
import pandas as pd
import re
from datetime import datetime

# =====================================================
# USER INPUT
# =====================================================

username = input("Enter Username: ")
password = getpass("Enter Password: ")

# =====================================================
# READ EXCEL
# =====================================================

input_file = r"E:\NOC\IP Addresses\All-L3-Switch-IP.xlsx"

df = pd.read_excel(input_file)

# Clean column names
df.columns = df.columns.str.strip().str.lower()

print("Columns Found:", df.columns.tolist())

ip_list = df['ip'].dropna().astype(str).tolist()

# =====================================================
# SAVE TO EXCEL
# =====================================================

output_file = (
    r"E:\NOC\Output\switch_audit_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
)

# =====================================================
# OUTPUT LISTS
# =====================================================

summary_data = []
vlan_data = []
interface_data = []
cdp_data = []

# =====================================================
# START LOOP
# =====================================================

for switch_ip in ip_list:

    print("\n" + "=" * 70)
    print(f"Connecting to Switch : {switch_ip}")
    print("=" * 70)

    device = {
        'device_type': 'cisco_ios',
        'host': switch_ip,
        'username': username,
        'password': password,
        'fast_cli': False
    }

    try:

        conn = ConnectHandler(**device)

        hostname = conn.find_prompt().replace("#", "").strip()

        print(f"✅ Login Success : {hostname}")

        # =================================================
        # SHOW VERSION
        # =================================================

        version_output = conn.send_command(
            "show version",
            read_timeout=60
        )

        # =================================================
        # RAM DETAILS
        # =================================================

        ram = "N/A"

        ram_match = re.search(
            r"with (.+?) bytes of memory",
            version_output
        )

        if ram_match:
            ram = ram_match.group(1)

        # =================================================
        # FLASH DETAILS
        # =================================================

        flash_output = conn.send_command(
            "dir flash:",
            read_timeout=60
        )

        total_flash = "N/A"
        free_flash = "N/A"

        total_match = re.search(
            r"(\d+) bytes total",
            flash_output
        )

        free_match = re.search(
            r"(\d+) bytes free",
            flash_output
        )

        if total_match:
            total_flash = round(
                int(total_match.group(1)) / (1024 ** 3),
                2
            )

        if free_match:
            free_flash = round(
                int(free_match.group(1)) / (1024 ** 3),
                2
            )

        # =================================================
        # VLAN DETAILS
        # =================================================

        print("Collecting VLAN Details...")

        vlan_output = conn.send_command(
            "show vlan brief",
            read_timeout=60
        )

        for line in vlan_output.splitlines():

            line = line.strip()

            # Skip unwanted lines
            if (
                line.startswith("VLAN") or
                line.startswith("----") or
                line == ""
            ):
                continue

            parts = re.split(r"\s+", line)

            if len(parts) >= 2 and parts[0].isdigit():

                vlan_id = parts[0]
                vlan_name = parts[1]

                vlan_data.append({
                    'Switch IP': switch_ip,
                    'Hostname': hostname,
                    'VLAN ID': vlan_id,
                    'VLAN Name': vlan_name
                })

        # =================================================
        # TRUNK PORTS
        # =================================================

        print("Collecting Trunk Details...")

        trunk_output = conn.send_command(
            "show interfaces trunk",
            read_timeout=60
        )

        trunk_ports = []

        for line in trunk_output.splitlines():

            line = line.strip()

            if re.search(r"^(Gi|Te|Fa|Fo|Hu|Eth)", line):

                interface = line.split()[0]

                trunk_ports.append(interface)

        # =================================================
        # INTERFACE DETAILS
        # =================================================

        print("Collecting Interface Details...")

        int_output = conn.send_command(
            "show interfaces description",
            read_timeout=60
        )

        for line in int_output.splitlines():

            line = line.strip()

            if re.search(r"^(Gi|Te|Fa|Fo|Hu|Eth)", line):

                parts = re.split(r"\s+", line)

                interface = parts[0]

                status = parts[1] if len(parts) > 1 else ""

                protocol = parts[2] if len(parts) > 2 else ""

                description = (
                    " ".join(parts[3:])
                    if len(parts) > 3
                    else "No Description"
                )

                mode = (
                    "TRUNK"
                    if interface in trunk_ports
                    else "ACCESS"
                )

                interface_data.append({
                    'Switch IP': switch_ip,
                    'Hostname': hostname,
                    'Interface': interface,
                    'Mode': mode,
                    'Status': status,
                    'Protocol': protocol,
                    'Description': description
                })

        # =================================================
        # CDP NEIGHBOR DETAILS
        # =================================================

        print("Collecting CDP Neighbor Details...")

        cdp_output = conn.send_command(
            "show cdp neighbors detail",
            read_timeout=90
        )

        neighbors = re.split(r'-{5,}', cdp_output)

        for neighbor in neighbors:

            neighbor_device = ""
            neighbor_ip = ""
            local_interface = ""
            remote_interface = ""
            platform = ""

            # Device ID
            device_match = re.search(
                r"Device ID:\s*(.+)",
                neighbor
            )

            if device_match:
                neighbor_device = device_match.group(1).strip()

            # Neighbor IP
            ip_match = re.search(
                r"IP address:\s*(.+)",
                neighbor
            )

            if ip_match:
                neighbor_ip = ip_match.group(1).strip()

            # Local Interface
            local_match = re.search(
                r"Interface:\s*([^,]+)",
                neighbor
            )

            if local_match:
                local_interface = local_match.group(1).strip()

            # Remote Interface
            remote_match = re.search(
                r"Port ID.*?:\s*(.+)",
                neighbor
            )

            if remote_match:
                remote_interface = remote_match.group(1).strip()

            # Platform
            platform_match = re.search(
                r"Platform:\s*([^,]+)",
                neighbor
            )

            if platform_match:
                platform = platform_match.group(1).strip()

            # Save only valid data
            if neighbor_device:

                cdp_data.append({
                    'Switch IP': switch_ip,
                    'Hostname': hostname,
                    'Local Interface': local_interface,
                    'Neighbor Device': neighbor_device,
                    'Neighbor IP': neighbor_ip,
                    'Remote Interface': remote_interface,
                    'Platform': platform
                })

        # =================================================
        # SUMMARY
        # =================================================

        summary_data.append({
            'Switch IP': switch_ip,
            'Hostname': hostname,
            'RAM': ram,
            'Total Flash GB': total_flash,
            'Free Flash GB': free_flash,
            'Status': 'SUCCESS'
        })

        conn.disconnect()

        print(f"✅ Completed : {hostname}")

    except Exception as e:

        print(f"❌ Failed : {switch_ip}")
        print(f"Error : {e}")

        summary_data.append({
            'Switch IP': switch_ip,
            'Hostname': 'N/A',
            'RAM': 'N/A',
            'Total Flash GB': 'N/A',
            'Free Flash GB': 'N/A',
            'Status': f'FAILED : {e}'
        })

# =====================================================
# CREATE DATAFRAMES
# =====================================================

summary_df = pd.DataFrame(summary_data)

vlan_df = pd.DataFrame(vlan_data)

interface_df = pd.DataFrame(interface_data)

cdp_df = pd.DataFrame(cdp_data)

# =====================================================
# SAVE TO EXCEL
# =====================================================

output_file = (
    f"switch_audit_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
)

with pd.ExcelWriter(
    output_file,
    engine='xlsxwriter'
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name='Summary',
        index=False
    )

    vlan_df.to_excel(
        writer,
        sheet_name='VLANs',
        index=False
    )

    interface_df.to_excel(
        writer,
        sheet_name='Interfaces',
        index=False
    )

    cdp_df.to_excel(
        writer,
        sheet_name='CDP_Neighbors',
        index=False
    )

    # =================================================
    # AUTO COLUMN WIDTH
    # =================================================

    workbook = writer.book

    for sheet_name in writer.sheets:

        worksheet = writer.sheets[sheet_name]

        df_sheet = {
            'Summary': summary_df,
            'VLANs': vlan_df,
            'Interfaces': interface_df,
            'CDP_Neighbors': cdp_df
        }[sheet_name]

        for idx, col in enumerate(df_sheet.columns):

            max_len = max(
                df_sheet[col].astype(str).map(len).max(),
                len(col)
            ) + 5

            worksheet.set_column(idx, idx, max_len)

print("\n" + "=" * 70)
print("✅ AUDIT COMPLETED SUCCESSFULLY")
print(f"✅ Output File : {output_file}")
print("=" * 70)