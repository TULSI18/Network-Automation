from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

from webdriver_manager.chrome import ChromeDriverManager

import time
import getpass
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import json
import os
from datetime import datetime, timedelta

# ================= URL =================

URL = "https://10.124.4.55:8080/"

import os

# ================= WELCOME BANNER =================
def show_banner():
    # Terminal saaf karne ke liye
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Raw string use kiya gaya hai taaki backslashes error na dein
    banner = r"""
*******************************************************************************
*                                                                             *
*                    WELCOME TO MPSWAN NOC Automation Portal                  *
*                                                                             *
*******************************************************************************
*                                                                             *
*   SYSTEM NAME : SWAN Ticket Automation & Monitoring Engine                  *
*   ACCESS      : Authorized Personnel Only                                   *
*   SECURITY    : Master Password + Network-Admin Approval Enabled             *
*                                                                             *
*******************************************************************************
*                                                                             *
*                    NETWORK ADMINISTRATOR CONTACT                            *
*                                                                             *
*   👤 Name     : Tulsi R Chouhan                                             *
*   📞 Mobile   : +91-9039563983                                              *
*   📧 Email    : tchouhan@omnilink.net.in                                     *
*                                                                             *
*   📲 Contact Network Administrator for approval access.                     *
*                                                                             *
*******************************************************************************
*                    INITIALIZING SECURE LOGIN PORTAL...                      *
*******************************************************************************
"""
    print(banner)

# Is function ko test karne ke liye call karein:
if __name__ == "__main__":
    show_banner()

# ================= TELEGRAM SECURITY =================

BOT_TOKEN = "8278899748:AAEjeWaa_fG_DePLnTo9g9Jbu_6dhhn-D48"

CHAT_ID = 943794870

MASTER_PASSWORD = "noc@123"

SESSION_FILE = "session.json"

approved = False

bot = telebot.TeleBot(BOT_TOKEN)

# ================= SESSION CHECK =================

def is_session_valid():

    if not os.path.exists(SESSION_FILE):
        return False

    try:

        with open(SESSION_FILE, "r") as f:
            data = json.load(f)

        expiry = datetime.fromisoformat(data["expiry"])

        return datetime.now() < expiry

    except:
        return False


# ================= SAVE SESSION =================

def save_session():

    expiry = datetime.now() + timedelta(hours=24)

    with open(SESSION_FILE, "w") as f:

        json.dump(
            {
                "expiry": expiry.isoformat()
            },
            f
        )


# ================= SEND TELEGRAM APPROVAL =================

def send_approval_request():

    markup = InlineKeyboardMarkup()

    approve_btn = InlineKeyboardButton(
        "✅ APPROVE",
        callback_data="approve"
    )

    deny_btn = InlineKeyboardButton(
        "❌ DENY",
        callback_data="deny"
    )

    markup.add(approve_btn, deny_btn)

    bot.send_message(
        CHAT_ID,
        "🔐 SWAN Ticket-Agent LOGIN REQUEST",
        reply_markup=markup
    )

    print("📲 Approval request sent to Telegram")


# ================= BUTTON HANDLER =================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    global approved

    if call.data == "approve":

        approved = True

        save_session()

        bot.answer_callback_query(
            call.id,
            "Approved"
        )

        bot.send_message(
            CHAT_ID,
            "✅ BOT APPROVED"
        )

  

    elif call.data == "deny":

        approved = False

        bot.answer_callback_query(
            call.id,
            "Denied"
        )

        bot.send_message(
            CHAT_ID,
            "❌ BOT DENIED"
        )

        print("❌ Denied from Telegram")


# ================= START TELEGRAM LISTENER =================

telegram_thread = threading.Thread(
    target=bot.infinity_polling,
    daemon=True
)

telegram_thread.start()

# ================= SECURITY CHECK =================

def security_check():

    global approved

    # ===== TRUSTED SESSION =====

    if is_session_valid():

        print("✅ Trusted session active")

        return

    # ===== MASTER PASSWORD =====

    entered = getpass.getpass(
        "Enter Master Password: "
    )

    if entered != MASTER_PASSWORD:

        print("❌ Wrong Master Password")

        exit()

    # ===== TELEGRAM APPROVAL =====

    send_approval_request()

    print("⏳ Waiting for Network-Admin approval...")

    timeout = 120

    start = time.time()

    while not approved:

        if time.time() - start > timeout:

            print("❌ Approval timeout")

            exit()

        time.sleep(1)

    print("✅ Network-Admin approval received")


# ================= CHROME SETUP =================

options = Options()

options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

options.add_argument("--ignore-certificate-errors")
options.add_argument("--allow-insecure-localhost")
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-dev-shm-usage")

options.add_experimental_option(
    "excludeSwitches",
    ["enable-automation"]
)

options.add_experimental_option(
    "useAutomationExtension",
    False
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.set_page_load_timeout(60)

wait = WebDriverWait(driver, 25)

# ================= HELPERS =================

def js_click(element):

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        element
    )

    time.sleep(0.5)

    driver.execute_script(
        "arguments[0].click();",
        element
    )


def open_new_tab():

    new_tile = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//a[contains(@onclick,'status == new')]"
            )
        )
    )

    js_click(new_tile)

    print("✅ NEW tickets opened")

    time.sleep(3)


def safe_select(by, locator, text, field_name):

    dropdown = wait.until(
        EC.presence_of_element_located((by, locator))
    )

    select = Select(dropdown)

    options_text = [
        o.text.strip()
        for o in select.options
    ]

    if text not in options_text:

        raise Exception(
            f"{field_name} option not found. Available: {options_text}"
        )

    select.select_by_visible_text(text)

    time.sleep(1)

    print(f"✅ {field_name}: {text}")


def get_domain():

    try:

        domain = driver.find_element(
            By.XPATH,
            "//label[contains(normalize-space(),'Domain')]/following::p[1]"
        ).text.strip().replace(":", "").strip()

        return domain

    except:

        return ""


# ================= DOMAIN RULES =================

def apply_domain_rules(domain):

    print(f"🌐 Domain detected: {domain}")

    try:

        # ================= JIO MANAGED =================

        if domain == "Jio_Managed_Services":

            safe_select(
                By.NAME,
                "cat",
                "Jio Managed Links",
                "Category"
            )

            safe_select(
                By.ID,
                "ticket_type_select_comp",
                "Horizontal",
                "Ticket Type"
            )

            safe_select(
                By.ID,
                "assignee",
                "swanjio - Live",
                "Ticket Assignee"
            )

            safe_select(
                By.NAME,
                "priority",
                "Low",
                "Priority"
            )

            safe_select(
                By.NAME,
                "2_cusID",
                "Link Down",
                "RCA Initial"
            )

        # ================= AIRTEL MANAGED =================

        elif domain == "Airtel_Managed_Services":

            safe_select(
                By.NAME,
                "cat",
                "Airtel",
                "Category"
            )

            safe_select(
                By.ID,
                "ticket_type_select_comp",
                "Horizontal",
                "Ticket Type"
            )

            safe_select(
                By.ID,
                "assignee",
                "Airtel - Live",
                "Ticket Assignee"
            )

            safe_select(
                By.NAME,
                "priority",
                "Low",
                "Priority"
            )

            safe_select(
                By.NAME,
                "2_cusID",
                "Link Down",
                "RCA Initial"
            )

        # ================= BSNL MANAGED =================

        elif domain == "Bsnl_Maneged_Services":

            safe_select(
                By.NAME,
                "cat",
                "Bsnl Managed Links",
                "Category"
            )

            safe_select(
                By.ID,
                "ticket_type_select_comp",
                "Horizontal",
                "Ticket Type"
            )

            safe_select(
                By.ID,
                "assignee",
                "Bsnl_Managed - Live",
                "Ticket Assignee"
            )

            safe_select(
                By.NAME,
                "priority",
                "Low",
                "Priority"
            )

            safe_select(
                By.NAME,
                "2_cusID",
                "Link Down",
                "RCA Initial"
            )

        # ================= NORMAL BSNL =================

        elif domain == "Bsnl":

            safe_select(
                By.NAME,
                "cat",
                "Bsnl",
                "Category"
            )

        # ================= NORMAL JIO =================

        elif domain == "Jio":

            safe_select(
                By.NAME,
                "cat",
                "Jio",
                "Category"
            )

        else:

            print("ℹ️ No domain rule matched")

        # ================= STATUS =================

        safe_select(
            By.ID,
            "status",
            "In Progress",
            "Status"
        )

    except Exception as e:

        print(f"⚠️ Domain rule apply failed: {e}")


# ================= TICKET DETAILS =================

def get_ticket_details():

    try:

        ticket_id = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//span[contains(text(),'Ticket ID')]"
                )
            )
        ).text.replace("Ticket ID :", "").strip()

    except:

        ticket_id = "Unknown"

    try:

        title_raw = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//h5[contains(@class,'form-section')]"
                )
            )
        ).text.strip()

        ticket_title = title_raw.split(": Added by")[0].strip()

    except:

        ticket_title = "Unknown"

    return ticket_id, ticket_title


# ================= VALID ROWS =================

def get_valid_rows():

    rows = driver.find_elements(
        By.XPATH,
        "//table[@id='ticketsTable']/tbody/tr"
    )

    valid_rows = []

    for row in rows:

        cols = row.find_elements(By.TAG_NAME, "td")

        if len(cols) >= 3:

            valid_rows.append(row)

    return valid_rows


# ================= MONITORING =================

def wait_for_new_tickets():

    print("\n⏳ Monitoring mode ON... checking every 2 minutes\n")

    while True:

        try:

            print("🔄 Refreshing dashboard...")

            driver.get(URL + "controller/Home")

            time.sleep(5)

            open_new_tab()

            time.sleep(3)

            valid_rows = get_valid_rows()

            ticket_count = len(valid_rows)

            if ticket_count > 0:

                print(f"🆕 New ticket detected: {ticket_count} ticket(s)")

                return

            print("⌛ No new tickets found")

            print("😴 Waiting 2 minutes...\n")

            time.sleep(120)

        except Exception as e:

            print(f"⚠️ Monitoring error: {e}")

            time.sleep(120)


# ================= LOGIN =================

def login():

    username = input("Enter Username: ")

    password = getpass.getpass("Enter Password: ")

    driver.get(URL)

    time.sleep(2)

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@type='text']"
            )
        )
    ).send_keys(username)

    driver.find_element(
        By.XPATH,
        "//input[@type='password']"
    ).send_keys(password)

    driver.find_element(
        By.XPATH,
        "//button[contains(text(),'Login')]"
    ).click()

    print("✅ Login done")

    time.sleep(5)


# ================= MAIN =================

try:

    # ================= SECURITY =================

    security_check()

    # ================= LOGIN =================

    login()

    # ================= OPEN NEW TAB =================

    driver.get(URL + "controller/Home")

    time.sleep(4)

    open_new_tab()

    while True:

        try:

            valid_rows = get_valid_rows()

            # ================= NO TICKETS =================

            if len(valid_rows) == 0:

                print("🎯 No tickets left")

                print("⏳ Bot is idle... monitoring for new tickets")

                wait_for_new_tickets()

                continue

            # ================= OPEN FIRST TICKET =================

            first_row = valid_rows[0]

            ticket_link = first_row.find_element(
                By.XPATH,
                "./td[3]//a"
            )

            js_click(ticket_link)

            time.sleep(3)

            ticket_id, ticket_title = get_ticket_details()

            print(
                f"➡️ Opening Ticket | ID: {ticket_id} | Title: {ticket_title}"
            )

            # ================= UPDATE PAGE =================

            edit_btn = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//button[normalize-space()='Update']"
                    )
                )
            )

            js_click(edit_btn)

            print("✅ Ticket Update page opened")

            time.sleep(3)

            # ================= APPLY RULES =================

            domain = get_domain()

            apply_domain_rules(domain)

            # ================= SAVE =================

            update_btn = wait.until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "btnUpdateClickSave"
                    )
                )
            )

            js_click(update_btn)

            print(f"💾 Ticket updated Done | ID: {ticket_id}")

            time.sleep(5)

            # ================= RETURN DASHBOARD =================

            print("🏠 Returning to dashboard...")

            driver.get(URL + "controller/Home")

            time.sleep(5)

            open_new_tab()

        except (
            TimeoutException,
            StaleElementReferenceException,
            WebDriverException
        ) as e:

            print("❌ Recoverable error:", e)

            try:

                driver.get(URL + "controller/Home")

                time.sleep(5)

                open_new_tab()

            except Exception as inner_error:

                print("⚠️ Recovery failed:", inner_error)

            continue

        except Exception as e:

            print("❌ Error:", e)

            try:

                driver.get(URL + "controller/Home")

                time.sleep(5)

                open_new_tab()

            except Exception as inner_error:

                print("⚠️ Recovery failed:", inner_error)

            continue

except Exception as e:

    print("🔥 Main error:", e)

finally:

    try:
        driver.quit()
    except:
        pass

input("Press Enter to exit...")