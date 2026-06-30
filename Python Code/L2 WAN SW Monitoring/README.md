POP Monitoring Tool using Python
Overview

This Python-based NOC monitoring tool checks the reachability of dual WAN/VLAN IPs for POP locations using multithreaded ping operations.

The script:
Monitors VLAN 51 (Jio) and VLAN 52 (BSNL)
Calculates POP health status
Extracts response time (RTT)
Detects packet loss
Generates professional Excel reports
Creates multiple sheets in a single Excel file

Features
✅ Dual VLAN Monitoring
✅ Multithreaded Fast Ping
✅ POP Health Status Detection
✅ RTT (Latency) Monitoring
✅ Packet Loss Monitoring
✅ Color Formatted Excel Reports
✅ Down POP Filtering
✅ Summary Dashboard Sheet
✅ Auto Timestamp Report Generation
✅ Auto Column Width Formatting
✅ Freeze Header Row
✅ Invalid IP Handling

POP Status Logic

VLAN51 Status	VLAN52 Status	POP Status
Reachable	    Reachable	    POP Up
Reachable	    Unreachable	    POP Partially Up
Unreachable	    Reachable	    POP Partially Up
Unreachable	    Unreachable	    POP Down

Input Excel     Format
Create an Excel file:All-L2-Switch-IP.xlsx

Required columns:
District	Block	VLAN 51 - Jio	VLAN 52-BSNL
Agarmalwa	Agarmalwa	172.30.224.44	10.101.64.117
Alirajpur	Alirajpur	172.30.224.52	10.101.64.125
Output Report

Generated Excel file contains 3 sheets:

1. POP_Status
Complete POP monitoring report.

District	Block	VLAN51 Status	VLAN51 RTT	VLAN51 Loss	VLAN52 Status	VLAN52 RTT	VLAN52 Loss	POP Status
2. Down_POPs
Contains only:

POP Down
POP Partially Up
3. Summary

Dashboard-style summary.

Metric	Count
Total POP	400
POP Up	350
POP Partially Up	30
POP Down	20
Folder Structure

Installation
Clone Repository
git clone https://github.com/your-username/NOC-Monitoring.git

Install Required Packages
pip install -r requirements.txt

requirements.txt
pandas
openpyxl

Configuration
Update input file path inside script:

input_file = r"E:\NOC\IP Addresses\All-L2-Switch-IP.xlsx"

Update output folder path:
output_folder = Path(r"E:\NOC\Output")

Run Script
python pop_ping_monitor.py

Technologies Used
Python 3
Pandas
OpenPyXL
Multithreading
Windows Ping Utility
Performance
Supports large-scale POP monitoring
Optimized using multithreading
Can monitor hundreds of IPs within minutes

Future Enhancements
Telegram Alert Integration
Email Notifications
Historical Data Logging
Flask Web Dashboard
Database Integration
ISP Health Analytics
Scheduled Monitoring
Live NOC Dashboard

Author: Tulsi R Chouhan

License: This project is licensed under the MIT License.