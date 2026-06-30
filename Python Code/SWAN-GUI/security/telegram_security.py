import os
import json
import time
import threading


from datetime import datetime, timedelta

import telebot

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

BOT_TOKEN = "8278899748:AAEjeWaa_fG_DePLnTo9g9Jbu_6dhhn-D48"

CHAT_ID = 943794870

MASTER_PASSWORD = "noc@123"

SESSION_FILE = "session.json"

approved = False

bot = telebot.TeleBot(
    BOT_TOKEN
)


# ================= SESSION CHECK =================

def is_session_valid():

    if not os.path.exists(
        SESSION_FILE
    ):
        return False

    try:

        with open(
            SESSION_FILE,
            "r"
        ) as f:

            data = json.load(f)

        expiry = datetime.fromisoformat(
            data["expiry"]
        )

        return (
            datetime.now() < expiry
        )

    except:

        return False


# ================= SAVE SESSION =================

def save_session():

    expiry = (
        datetime.now()
        + timedelta(hours=24)
    )

    with open(
        SESSION_FILE,
        "w"
    ) as f:

        json.dump(
            {
                "expiry":
                expiry.isoformat()
            },
            f
        )


# ================= SEND REQUEST =================

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

    markup.add(
        approve_btn,
        deny_btn
    )

    bot.send_message(
        CHAT_ID,
        "🔐 SWAN GUI BOT LOGIN REQUEST",
        reply_markup=markup
    )

    print(
        "📲 Approval request sent to Telegram"
    )


# ================= BUTTON HANDLER =================

@bot.callback_query_handler(
    func=lambda call: True
)
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


# ================= START LISTENER =================

def start_telegram_listener():

    telegram_thread = threading.Thread(
        target=bot.infinity_polling,
        daemon=True
    )

    telegram_thread.start()


# ================= SECURITY CHECK =================

def security_check(
    entered_password
):

    global approved

    if is_session_valid():

        print(
            "✅ Trusted session active"
        )

        return True

    if (
        entered_password
        != MASTER_PASSWORD
    ):

        print(
            "❌ Wrong Master Password"
        )

        return False

    send_approval_request()

    print(
        "⏳ Waiting for Network-Admin approval..."
    )

    timeout = 120

    start = time.time()

    while not approved:

        if (
            time.time() - start
            > timeout
        ):

            print(
                "❌ Approval timeout"
            )

            return False

        time.sleep(1)

    print(
        "✅ Network-Admin approval received"
    )

    return True