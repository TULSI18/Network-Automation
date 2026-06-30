import customtkinter as ctk
import psutil
import threading
import time
import queue

from tkinter import ttk
from datetime import datetime

from core.bot_engine import BotEngine


# ---------------- THEME ----------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ---------------- MAIN WINDOW ----------------

class Dashboard(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Window Setup

        self.title(
            "SWAN NOC Automation Dashboard"
        )

        self.geometry(
            "1600x900"
        )

        self.minsize(
            1400,
            800
        )

        self.resizable(
            True,
            True
        )

        self.after(
            100,
            lambda: self.state("zoomed")
        )

        # Background Color
        self.configure(fg_color="#1a1a1a")

        # Create Layout
        self.create_layout()

        self.update_datetime()

        # Start CPU/RAM Monitoring
        self.update_system_stats()


        self.bot_running = False

        self.gui_queue = queue.Queue()

        self.table_rows = {}

 
        # ---------- Dashboard Counters ----------

        self.completed_count = 0

        self.failed_count = 0

        self.processing_count = 0

        self.queued_count = 0

       

        self.add_log("Dashboard Initialized", "INFO")
        self.add_log("GUI Loaded Successfully", "SUCCESS")
        self.add_log("Waiting For Bot Start...", "INFO")

        self.process_queue()

        self.add_log("CPU Monitoring Started", "SUCCESS")
        self.add_log("No Active Tickets", "WARNING")
        self.add_log("Sample Error Detected", "ERROR")

    # ---------------- MAIN LAYOUT ----------------

    def create_layout(self):

        # ================= TOP BAR =================

        self.topbar = ctk.CTkFrame(
            self,
            height=40,
            corner_radius=0,
            fg_color="#111111"
        )

        self.topbar.pack(fill="x")

        # Title
        title = ctk.CTkLabel(
            self.topbar,
            text="SWAN NOC AUTOMATION DASHBOARD",
            font=("Arial", 20, "bold")
        )

        title.pack(
            pady=(8, 2)
        )

        self.datetime_label = ctk.CTkLabel(
            self.topbar,
            text="",
            font=("Arial", 12, "bold"),
            text_color="#00bfff"
        )

        self.datetime_label.pack(
            pady=(0, 5)
        )


        # ================= MAIN CONTENT =================

        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="#1a1a1a"
        )

        self.main_frame.pack(fill="both", expand=True)


        # ================= SIDEBAR =================

        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            width=180,
            fg_color="#111111",
            corner_radius=0
        )

        self.sidebar.pack(side="left", fill="y")


        # Sidebar Title
        sidebar_title = ctk.CTkLabel(
            self.sidebar,
            text="CONTROL PANEL",
            font=("Arial", 16, "bold")
        )

        sidebar_title.pack(pady=20)

        # ================= LOGIN SECTION =================

        ctk.CTkLabel(
            self.sidebar,
            text="MASTER PASSWORD",
            font=("Arial", 10, "bold")
        ).pack(
            pady=(10, 2)
        )

        self.master_password_entry = ctk.CTkEntry(
            self.sidebar,
            width=160,
            show="*"
        )

        self.master_password_entry.pack(
            pady=5
        )

        ctk.CTkLabel(
            self.sidebar,
            text="USERNAME",
            font=("Arial", 10, "bold")
        ).pack(
            pady=(10, 2)
        )

        self.username_entry = ctk.CTkEntry(
            self.sidebar,
            width=160
        )

        self.username_entry.pack(
            pady=5
        )

        ctk.CTkLabel(
            self.sidebar,
            text="PASSWORD",
            font=("Arial", 10, "bold")
        ).pack(
            pady=(10, 2)
        )

        self.password_entry = ctk.CTkEntry(
            self.sidebar,
            width=160,
            show="*"
        )

        self.password_entry.pack(
            pady=5
        )

        # ================= BUTTONS =================

        start_btn = ctk.CTkButton(
            self.sidebar,
            text="START BOT",
            width=160,
            height=35,
            font=("Arial", 14),
            command=self.start_bot
        )

        start_btn.pack(pady=5)


        stop_btn = ctk.CTkButton(
            self.sidebar,
            text="STOP BOT",
            width=160,
            height=35,
            font=("Arial", 14),
            command=self.stop_bot
        )

        stop_btn.pack(pady=5)


        restart_btn = ctk.CTkButton(
            self.sidebar,
            text="RESTART",
            width=160,
            height=35,
            font=("Arial", 14),
            command=self.restart_bot
        )

        restart_btn.pack(pady=5)


        screenshot_btn = ctk.CTkButton(
            self.sidebar,
            text="SCREENSHOT",
            width=160,
            height=35,
            font=("Arial", 14)
        )

        screenshot_btn.pack(pady=5)


        settings_btn = ctk.CTkButton(
            self.sidebar,
            text="SETTINGS",
            width=160,
            height=35,
            font=("Arial", 14)
        )

        settings_btn.pack(pady=5)


        exit_btn = ctk.CTkButton(
            self.sidebar,
            text="EXIT",
            width=160,
            height=35,
            font=("Arial", 14),
            fg_color="red",
            hover_color="#aa0000",
            command=self.exit_app
        )

        exit_btn.pack(pady=5)


        # ================= RIGHT PANEL =================

        self.content_area = ctk.CTkFrame(
            self.main_frame,
            fg_color="#1f1f1f"
        )

        self.content_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


                # ================= STATUS CARDS =================

        self.cards_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )

        self.cards_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )


        # ---------- CARD 1 : BOT STATUS ----------

        self.card1 = ctk.CTkFrame(
            self.cards_frame,
            width=180,
            height=90,
            fg_color="#252525"
        )

        self.card1.pack(side="left", padx=10)

        self.card1.pack_propagate(False)

        ctk.CTkLabel(
            self.card1,
            text="BOT STATUS",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))

        self.bot_status = ctk.CTkLabel(
            self.card1,
            text="READY",
            font=("Arial", 14, "bold"),
            text_color="green"
        )

        self.bot_status.pack()


        # ---------- CARD 2 : TOTAL PROCESSED ----------

        self.card2 = ctk.CTkFrame(
            self.cards_frame,
            width=180,
            height=90,
            fg_color="#252525"
        )

        self.card2.pack(side="left", padx=10)

        self.card2.pack_propagate(False)

        ctk.CTkLabel(
            self.card2,
            text="TOTAL PROCESSED",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))

        self.total_processed = ctk.CTkLabel(
            self.card2,
            text="0",
            font=("Arial", 14, "bold"),
            text_color="#00bfff"
        )

        self.total_processed.pack()


        # ---------- CARD 3 : CPU USAGE ----------

        self.card3 = ctk.CTkFrame(
            self.cards_frame,
            width=180,
            height=90,
            fg_color="#252525"
        )

        self.card3.pack(side="left", padx=10)

        self.card3.pack_propagate(False)

        ctk.CTkLabel(
            self.card3,
            text="CPU USAGE",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))

        self.cpu_usage = ctk.CTkLabel(
            self.card3,
            text="0%",
            font=("Arial", 14, "bold"),
            text_color="orange"
        )

        self.cpu_usage.pack()


        # ---------- CARD 4 : RAM USAGE ----------

        self.card4 = ctk.CTkFrame(
            self.cards_frame,
            width=180,
            height=90,
            fg_color="#252525"
        )

        self.card4.pack(side="left", padx=10)

        self.card4.pack_propagate(False)

        ctk.CTkLabel(
            self.card4,
            text="RAM USAGE",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))

        self.ram_usage = ctk.CTkLabel(
            self.card4,
            text="0%",
            font=("Arial", 14, "bold"),
            text_color="red"
        )

        self.ram_usage.pack()

        # ---------- CARD 5 : LOGGED USER ----------

        self.card5 = ctk.CTkFrame(
            self.cards_frame,
            width=180,
            height=90,
            fg_color="#252525"
        )

        self.card5.pack(
            side="left",
            padx=10
        )

        self.card5.pack_propagate(False)

        ctk.CTkLabel(
            self.card5,
            text="LOGGED USER",
            font=("Arial", 16, "bold")
        ).pack(
            pady=(15, 2)
        )

        self.logged_user = ctk.CTkLabel(
            self.card5,
            text="Not Logged In",
            font=("Arial", 12, "bold"),
            text_color="#00bfff"
        )

        self.logged_user.pack()

        # ================= DASHBOARD COUNTERS =================

        self.stats_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )

        self.stats_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        self.completed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Completed : 0",
            font=("Arial", 18, "bold"),
            text_color="green"
        )

        self.completed_label.pack(
            side="left",
            padx=20
        )

        self.failed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Failed : 0",
            font=("Arial", 18, "bold"),
            text_color="red"
        )

        self.failed_label.pack(
            side="left",
            padx=20
        )

        self.processing_label = ctk.CTkLabel(
            self.stats_frame,
            text="Processing : 0",
            font=("Arial", 18, "bold"),
            text_color="orange"
        )

        self.processing_label.pack(
            side="left",
            padx=20
        )

        self.queued_label = ctk.CTkLabel(
            self.stats_frame,
            text="Queued : 0",
            font=("Arial", 18, "bold"),
            text_color="#00bfff"
        )

        self.queued_label.pack(
            side="left",
            padx=20
        )

        # ================= TICKET TABLE =================

        table_title = ctk.CTkLabel(
            self.content_area,
            text="LIVE TICKET MONITOR",
            font=("Arial", 22, "bold")
        )

        table_title.pack(pady=(10, 5))


        # ---------- TABLE FRAME ----------

        self.table_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="#1f1f1f"
        )

        self.table_frame.pack_propagate(
            False
        )

        self.table_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.table_frame.configure(
            height=180
        )


        # ---------- STYLE ----------

        style = ttk.Style()

        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            rowheight=35,
            font=("Segoe UI", 12)
        )

        style.configure(
            "Treeview.Heading",
            background="#111111",
            foreground="#00bfff",
            font=("Segoe UI", 13, "bold")
        )

        style.map(
            "Treeview",
            background=[
                ("selected", "#1f6aa5")
            ],
            foreground=[
                ("selected", "white")
            ]
        )


        # ---------- TABLE ----------

        columns = (
            "Ticket ID",
            "Domain",
            "Status",
            "Assignee"
        )

        self.ticket_table = ttk.Treeview(
            self.table_frame,
            columns=columns,
            show="headings",
            height=4
        )


        # ---------- HEADINGS ----------

        for col in columns:

            self.ticket_table.heading(col, text=col)

            self.ticket_table.column(
                col,
                anchor="center",
                width=200
            )


        self.ticket_table.pack(
            fill="both",
            expand=True,
            pady=10
        )


        

        # ================= LOG AREA =================

        self.log_box = ctk.CTkTextbox(
            self.content_area,
            font=("Consolas", 12)
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        ) 
       
    # ---------------- SYSTEM MONITOR ----------------

    def update_system_stats(self):

        # CPU Usage
        cpu = psutil.cpu_percent()

        # RAM Usage
        ram = psutil.virtual_memory().percent

        # Update Labels
        self.cpu_usage.configure(text=f"{cpu}%")
        self.ram_usage.configure(text=f"{ram}%")

        # Refresh every 2 sec
        self.after(2000, self.update_system_stats)

           # ---------------- START BOT ----------------

    def start_bot(self):

        if self.bot_running:

            self.add_log(
                "Bot Already Running",
                "WARNING"
            )

            return

        username = (
            self.username_entry.get().strip()
        )

        password = (
            self.password_entry.get().strip()
        )
        master_password = (
            self.master_password_entry.get().strip()
        )

        if not master_password:

            self.add_log(
                "Master Password Required",
                "ERROR"
            )

            return

        if not username:

            self.add_log(
                "Username Required",
                "ERROR"
            )

            return

        if not password:

            self.add_log(
                "Password Required",
                "ERROR"
            )

            return

        self.bot_engine = BotEngine(
            self.gui_queue,
            username,
            password,
            master_password
        )
        self.bot_running = True

        self.logged_user.configure(
            text=username
        )

        self.bot_status.configure(
            text="RUNNING",
            text_color="green"
        )

        self.add_log(
            "Launching Bot Engine",
            "SUCCESS"
        )

        # ---------- START THREAD ----------

        selenium_thread = threading.Thread(
            target=self.bot_engine.start,
            daemon=True
        )

        selenium_thread.start()


            # ---------------- STOP BOT ----------------

    def stop_bot(self):

        self.bot_running = False

        self.bot_engine.stop()

        self.bot_status.configure(
            text="STOPPED",
            text_color="red"
        )

        self.logged_user.configure(
            text="Not Logged In"
        )

        self.add_log(
            "Bot Stopped",
            "WARNING"
        )


    # ---------------- RESTART BOT ----------------

    def restart_bot(self):

        self.bot_status.configure(
            text="RESTARTING",
            text_color="orange"
        )

        self.add_log("Restarting Bot...", "INFO")

        # 2 sec later
        self.after(2000, self.finish_restart)


    def finish_restart(self):

        self.bot_status.configure(
            text="RUNNING",
            text_color="green"
        )

        self.add_log("Bot Restarted Successfully", "SUCCESS")


    # ---------------- EXIT APP ----------------

    def exit_app(self):

        self.add_log("Closing Dashboard...", "INFO")

        self.after(1000, self.destroy)

    # ---------------- PROCESS GUI QUEUE ----------------

    def process_queue(self):

        while not self.gui_queue.empty():

            task = self.gui_queue.get()

            task_type = task[0]


            # ---------- LOG ----------

            if task_type == "log":

                message = task[1]
                level = task[2]

                self.add_log(message, level)


            # ---------- TICKET COUNT ----------

            elif task_type == "ticket_count":

                pass

            # ---------- STATS ----------

            elif task_type == "stats":

                stats = task[1]

                self.completed_label.configure(
                    text=f"Completed : {stats['completed']}"
                )

                self.failed_label.configure(
                    text=f"Failed : {stats['failed']}"
                )

                self.processing_label.configure(
                    text=f"Processing : {stats['processing']}"
                )

                self.queued_label.configure(
                    text=f"Queued : {stats['queued']}"
                )

                total_processed = (
                    stats["completed"]
                    + stats["failed"]
                )

                self.total_processed.configure(
                    text=str(
                        total_processed
                    )
                )


            # ---------- TABLE INSERT ----------

            # ---------- TABLE UPDATE ----------

            elif task_type == "table":

                values = task[1]

                ticket_id = values[0]

                if ticket_id in self.table_rows:

                    row_id = self.table_rows[ticket_id]

                    self.ticket_table.item(
                        row_id,
                        values=values
                    )

                else:

                    row_id = self.ticket_table.insert(
                        "",
                        "end",
                        values=values
                    )

                    self.table_rows[ticket_id] = row_id


        # Run Again After 100ms
        self.after(100, self.process_queue)

       # ---------------- BOT LOOP ----------------

    def bot_loop(self):

        counter = 1

        while self.bot_running:

            # Send Log To Queue
            self.gui_queue.put(
                (
                    "log",
                    f"Processing Ticket #{counter}",
                    "INFO"
                )
            )

            # Send Ticket Count
            self.gui_queue.put(
                (
                    "ticket_count",
                    counter
                )
            )

            # Send Table Data
            self.gui_queue.put(
                (
                    "table",
                    (
                        f"44{500 + counter}",
                        "Jio",
                        "Processing",
                        "swanjio"
                    )
                )
            )

            counter += 1

            time.sleep(3)

    # ---------------- DATE TIME ----------------

    def update_datetime(self):

        current_time = datetime.now().strftime(
            "%A | %d-%b-%Y | %H:%M:%S"
        )

        self.datetime_label.configure(
            text=current_time
        )

        self.after(
            1000,
            self.update_datetime
        )

    # ---------------- LIVE LOGGER ----------------

    def add_log(self, message, level="INFO"):

        # Current Time
        current_time = datetime.now().strftime("%H:%M:%S")

        # Final Log Line
        log_message = f"[{current_time}] {level:<8} {message}\n"

        # Insert Into Log Box
        self.log_box.insert("end", log_message)

        # Auto Scroll Bottom
        self.log_box.see("end")

# ---------------- RUN APP ----------------

if __name__ == "__main__":

    app = Dashboard()

    app.mainloop()