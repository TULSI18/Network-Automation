# $language = "python3"
# $interface = "1.0"

import os
import csv
import re
import subprocess
from datetime import datetime

credentials = [
    ("tulsi", "tul$!@2020"),
    ("admin", "Dr3@mB1gg@2026")
]

input_csv_path = r"E:\NOC\IP Addresses\All-L2-Switch-IP.csv"
output_dir = r"E:\NOC\Output\L2_WAN_Switch_Output"

def build_sheet_xml(sheet_name, headers, rows):

    xml = '  <Worksheet ss:Name="{}">\n    <Table>\n'.format(sheet_name)

    xml += '      <Row>'
    for h in headers:
        xml += '<Cell><Data ss:Type="String">{}</Data></Cell>'.format(h)
    xml += '</Row>\n'

    for row in rows:

        xml += '      <Row>'

        for cell in row:
            value = str(cell).replace("&", "&amp;")
            xml += '<Cell><Data ss:Type="String">{}</Data></Cell>'.format(value)

        xml += '</Row>\n'

    xml += '    </Table>\n  </Worksheet>\n'

    return xml

def main():

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    screen = crt.Screen
    screen.Synchronous = True

    with open(input_csv_path, "r") as f:
        rows = list(csv.reader(f))

    summary_rows = []
    inventory_rows = []
    vlan_rows = []
    ip_rows = []
    cdp_rows = []

    found_working_switch = False
    successful_switches = 0

    for row in rows[1:]:

        ip_list = []

        if len(row) > 2 and row[2].strip():
            ip_list.append(row[2].strip())

        if len(row) > 3 and row[3].strip():
            ip_list.append(row[3].strip())

        if not ip_list:
            continue

        ip = None

        for candidate_ip in ip_list:

            ping_result = subprocess.call(
                ["ping", "-n", "1", "-w", "500", candidate_ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if ping_result == 0:
                ip = candidate_ip
                break

        if not ip:
            summary_rows.append([ip_list[0], "N/A", "N/A", "FAILED", "Both Jio and BSNL Ping Failed"])
            continue

        authenticated_user = "N/A"

        try:

            login_success = False

            for username, password in credentials:

                try:

                    crt.Session.Connect("/SSH2 /L " + username + " " + ip)

                    if screen.WaitForString("User Name:", 3):
                        screen.Send(username + "\r")

                    if screen.WaitForString("Password:", 3):
                        screen.Send(password + "\r")

                    if screen.WaitForStrings(["#", ">"], 5):
                        authenticated_user = username
                        login_success = True
                        break

                    crt.Session.Disconnect()

                except:
                    try:
                        crt.Session.Disconnect()
                    except:
                        pass

            if not login_success:

                summary_rows.append([ip, "N/A", "N/A", "FAILED", "Login Failed (Both Credentials)"])
                continue

            screen.Send("terminal datadump\r")
            screen.WaitForString("#", 5)

            hostname = "Unknown"

            screen.Send("show running-config | include ^hostname\r")
            host_out = screen.ReadString("#")

            for line in host_out.splitlines():
                line = line.strip()

                if line.startswith("hostname"):
                    parts = line.split()

                    if len(parts) >= 2:
                        hostname = parts[1]

                    break

            model = ""
            serial = ""
            uptime = ""

            screen.Send("show inventory\r")
            inv_out = screen.ReadString("#")

            for line in inv_out.splitlines():

                if "PID:" in line and not model:

                    m = re.search(r"PID:\s*([^\s]+)", line)

                    if m:
                        model = m.group(1)

                if "SN:" in line and not serial:

                    s = re.search(r"SN:\s*([A-Za-z0-9]+)", line)

                    if s:
                        serial = s.group(1)

                if model and serial:
                    break

            screen.Send("show system\r")
            sys_out = screen.ReadString("#")

            m = re.search(
                r'System Up Time \(days,hour:min:sec\):\s*([0-9,:]+)',
                sys_out
            )

            if m:
                uptime = m.group(1).strip()
            else:
                uptime = ""

            inventory_rows.append([
                ip,
                hostname,
                model,
                serial,
                uptime
            ])

            screen.Send("show vlan\r")
            vlan_out = screen.ReadString("#")

            for line in vlan_out.splitlines():

                line = line.rstrip()

                m = re.match(
                    r'^\s*(\d+)\s+(\S+)\s+(.*?)\s{2,}(.*?)\s{2,}',
                    line
                )

                if m:

                    vlan_rows.append([
                        ip,
                        hostname,
                        m.group(1),
                        m.group(2),
                        m.group(3).strip(),
                        m.group(4).strip()
                    ])

            screen.Send("show ip interface\r")
            ip_out = screen.ReadString("#")

            for line in ip_out.splitlines():

                line = line.strip()

                m = re.match(
                    r'^(\d+\.\d+\.\d+\.\d+\/\d+)\s+(vlan\s+\d+)',
                    line,
                    re.IGNORECASE
                )

                if m:

                    ip_rows.append([
                        ip,
                        hostname,
                        m.group(2),
                        m.group(1)
                    ])

            screen.Send("show cdp neighbors detail\r")
            cdp_out = screen.ReadString("#")

            neighbors = cdp_out.split(
                "---------------------------------------------"
            )

            for nb in neighbors:

                device_id = ""
                mgmt_ip = ""
                platform = ""
                local_int = ""
                remote_int = ""

                m = re.search(r'Device-ID:\s*(.*)', nb)
                if m:
                    device_id = m.group(1).strip()

                m = re.search(r'Platform:\s*(.*)', nb)
                if m:
                    platform = m.group(1).strip()

                m = re.search(
                    r'Interface:\s*(.*?),\s*Port ID \(outgoing port\):\s*(.*)',
                    nb
                )

                if m:
                    local_int = m.group(1).strip()
                    remote_int = m.group(2).strip()

                m = re.search(r'IP\s+(\d+\.\d+\.\d+\.\d+)', nb)
                if m:
                    mgmt_ip = m.group(1)

                if device_id:

                    cdp_rows.append([
                        ip,
                        device_id,
                        mgmt_ip,
                        platform,
                        local_int,
                        remote_int
                    ])

            summary_rows.append([
                ip,
                hostname,
                authenticated_user,
                "SUCCESS",
                "Online"
            ])

            crt.Session.Disconnect()

            found_working_switch = True

            successful_switches += 1

            if successful_switches >= 5:
                break

        except Exception as e:

            summary_rows.append([
                ip,
                "N/A",
                authenticated_user,
                "FAILED",
                str(e)
            ])

            try:
                crt.Session.Disconnect()
            except:
                pass

            continue

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(
        output_dir,
        "L2_Switch_Audit_" + ts + ".xls"
    )

    with open(output_file, "w") as f:

        f.write(
            '<?xml version="1.0"?>'
            '<Workbook '
            'xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
            'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n'
        )

        f.write(build_sheet_xml(
            "Summary",
            ["IP","Hostname","Authenticated User","Status","Connectivity"],
            summary_rows
        ))

        f.write(build_sheet_xml(
            "Inventory",
            ["IP","Hostname","Model","Serial","Uptime"],
            inventory_rows
        ))

        f.write(build_sheet_xml(
            "VLAN_Port_Map",
            [
                "IP",
                "Hostname",
                "VLAN ID",
                "VLAN Name",
                "Tagged Ports",
                "Untagged Ports"
            ],
            vlan_rows
        ))

        f.write(build_sheet_xml(
            "VLAN_IPs",
            [
                "Switch IP",
                "Hostname",
                "VLAN",
                "IP Address"
            ],
            ip_rows
        ))

        f.write(build_sheet_xml(
            "CDP_Details",
            [
                "Switch IP",
                "Device ID",
                "Mgmt IP",
                "Platform",
                "Local Interface",
                "Remote Interface"
            ],
            cdp_rows
        ))

        f.write("</Workbook>")

    crt.Dialog.MessageBox(
        "Audit Completed.\n\nSaved:\n" + output_file
    )

main()
