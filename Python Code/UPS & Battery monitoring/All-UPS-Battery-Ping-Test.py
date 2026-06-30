import pandas as pd
import subprocess
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# INPUT FILE
# ==========================================

INPUT_FILE = r"E:\NOC\IP Addresses\All-UPS-Battery-IP.xlsx"

# ==========================================
# OUTPUT FOLDER
# ==========================================

OUTPUT_FOLDER = Path(r"E:\NOC\Output\UPS_Battery_Report")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# ==========================================
# PING FUNCTION
# ==========================================

def ping_ip(ip):

    if pd.isna(ip):
        return "Invalid IP"

    ip = str(ip).strip()

    try:

        result = subprocess.run(
            ["ping", "-n", "2", "-w", "1000", ip],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return "Reachable"
        else:
            return "Unreachable"

    except:
        return "Error"

# ==========================================
# LOAD EXCEL
# ==========================================

print("Reading Excel...")

df = pd.read_excel(INPUT_FILE)

df.columns = df.columns.str.strip()

required_cols = [
    "District",
    "Block",
    "UPS",
    "Battery"
]

for col in required_cols:

    if col not in df.columns:
        raise Exception(f"Missing Column: {col}")

print(f"Total Records : {len(df)}")

# ==========================================
# CREATE TASKS
# ==========================================

tasks = []

for index, row in df.iterrows():

    tasks.append(("UPS", index, row["UPS"]))
    tasks.append(("Battery", index, row["Battery"]))

# ==========================================
# MULTITHREAD PING
# ==========================================

results = {}

def worker(task):

    device_type, index, ip = task

    status = ping_ip(ip)

    return device_type, index, status

print("Pinging IPs...")

with ThreadPoolExecutor(max_workers=100) as executor:

    for device_type, index, status in executor.map(worker, tasks):

        if index not in results:
            results[index] = {}

        results[index][device_type] = status

# ==========================================
# PREPARE OUTPUT
# ==========================================

ups_status = []
battery_status = []
pop_status = []

for index in df.index:

    ups = results[index].get("UPS", "Error")
    battery = results[index].get("Battery", "Error")

    ups_status.append(ups)
    battery_status.append(battery)

    if ups == "Reachable" and battery == "Reachable":
        pop_status.append("POP Up")

    elif ups == "Reachable" or battery == "Reachable":
        pop_status.append("POP Partially Up")

    else:
        pop_status.append("POP Down")

# ==========================================
# ADD RESULT COLUMNS
# ==========================================

df["UPS Status"] = ups_status
df["Battery Status"] = battery_status
df["POP Status"] = pop_status

# ==========================================
# DOWN POP SHEET
# ==========================================

down_df = df[df["POP Status"] != "POP Up"]

# ==========================================
# SUMMARY
# ==========================================

summary_df = pd.DataFrame({

    "Metric": [
        "Total POP",
        "POP Up",
        "POP Partially Up",
        "POP Down"
    ],

    "Count": [
        len(df),
        len(df[df["POP Status"] == "POP Up"]),
        len(df[df["POP Status"] == "POP Partially Up"]),
        len(df[df["POP Status"] == "POP Down"])
    ]
})

# ==========================================
# SAVE EXCEL
# ==========================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

output_file = OUTPUT_FOLDER / f"UPS_Battery_Report_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

    df.to_excel(writer,
                sheet_name="All_POPs",
                index=False)

    down_df.to_excel(writer,
                     sheet_name="Down_POPs",
                     index=False)

    summary_df.to_excel(writer,
                        sheet_name="Summary",
                        index=False)

print("\n====================================")
print("REPORT GENERATED SUCCESSFULLY")
print("====================================")
print(f"Output File:\n{output_file}")