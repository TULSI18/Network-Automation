from config.settings import (
    PORTAL_URL,
    MONITOR_INTERVAL
)

from core.logger import EnterpriseLogger
from core.selenium_manager import SeleniumManager
from core.login_manager import LoginManager
from core.ticket_monitor import TicketMonitor
from core.ticket_processor import TicketProcessor
from security.telegram_security import (
    security_check,
    start_telegram_listener
)

import time


class BotEngine:

    def __init__(
        self,
        gui_queue,
        username,
        password,
        master_password
    ):

        self.gui_queue = gui_queue

        self.username = username

        self.password = password

        self.master_password = (
            master_password
        )

        self.logger = EnterpriseLogger(gui_queue)

        self.driver = None

        self.running = False

        self.selenium = SeleniumManager(
            self.logger
        )

        # ---------- Dashboard Counters ----------

        self.completed_count = 0

        self.failed_count = 0

        self.processing_count = 0

        self.queued_count = 0

    # ---------------- START BOT ----------------

    def start(self):

        self.running = True

        start_telegram_listener()

        if not security_check(
            self.master_password
        ):

            self.logger.error(
                "Security Validation Failed"
            )

            return

        self.logger.info(
            "Starting Selenium Engine"
        )

        try:

            # ---------- START DRIVER ----------

            self.driver = self.selenium.start_driver()

            if not self.driver:

                self.logger.error(
                    "Driver Initialization Failed"
                )

                return

            # ---------- LOGIN MANAGER ----------

            login_manager = LoginManager(
                self.driver,
                self.logger
            )

            # ---------- LOGIN ----------

            login_success = login_manager.login(
                portal_url=PORTAL_URL,
                username=self.username,
                password=self.password
            )

            # ---------- LOGIN FAILED ----------

            if not login_success:

                self.logger.error(
                    "Stopping Bot Due To Login Failure"
                )

                self.running = False

                return



            # ---------- TICKET MONITOR ----------

            ticket_monitor = TicketMonitor(
                self.driver,
                self.logger
            )

            ticket_processor = TicketProcessor(
                self.driver,
                self.logger
            )

            # Connect processor with monitor

            ticket_processor.ticket_monitor = ticket_monitor

            while self.running:

                self.logger.info(
                    "Starting Monitoring Cycle"
                )

                # ---------- DRIVER HEALTH CHECK ----------

                if not self.selenium.is_alive():

                    self.logger.warning(
                        "Driver Lost... Restarting Chrome"
                    )

                    self.driver = self.selenium.start_driver()

                    if not self.driver:

                        self.logger.error(
                            "Driver Recovery Failed"
                        )

                        time.sleep(10)

                        continue

                    self.logger.success(
                        "Driver Recovered Successfully"
                    )

                    ticket_monitor.driver = self.driver

                    ticket_processor.driver = self.driver

                # ---------- NORMAL MONITORING ----------



                # ---------- CHECK SESSION ----------

                session_ok = login_manager.is_logged_in()

                if not session_ok:

                    self.logger.warning(
                        "Session Expired"
                    )

                    self.logger.info(
                        "Trying Auto Re-Login"
                    )

                    login_success = login_manager.login(
                        portal_url=PORTAL_URL,
                        username=self.username,
                        password=self.password
                    )

                    if not login_success:

                        self.logger.error(
                            "Re-Login Failed"
                        )

                        self.running = False

                        break

                    self.logger.success(
                        "Re-Login Successful"
                    )

                # ---------- CHECK TICKETS ----------

                new_tickets = (
                    ticket_monitor.wait_for_new_tickets()
                )

                
                # ---------- PROCESS TICKETS ----------

                if new_tickets:

                    self.gui_queue.put(
                        (
                            "ticket_count",
                            len(new_tickets)
                        )
                    )

                    self.logger.success(
                        f"{len(new_tickets)} "
                        f"Tickets Ready For Processing"
                    )

                    ticket = new_tickets[0]

                    # ---------- ADD ROW TO TABLE ----------

                    self.gui_queue.put(
                        (
                            "table",
                            (
                                ticket.get("ticket_id", ""),
                                ticket.get("domain", "Unknown"),
                                "Processing",
                                ticket.get("assignee", "-")
                            )
                        )
                    )

                   
                    # ---------- START PROCESSING COUNTER ----------

                    self.processing_count += 1

                    self.queued_count = len(
                        ticket_monitor.ticket_queue
                    )

                    self.gui_queue.put(
                        (
                            "stats",
                            {
                                "completed": self.completed_count,
                                "failed": self.failed_count,
                                "processing": self.processing_count,
                                "queued": self.queued_count
                            }
                        )
                    )
                    success = ticket_processor.process_ticket(
                        ticket
                    )

                    if success:

                        ticket["status"] = "Completed"

                    else:

                        ticket["status"] = "Failed"

                    self.processing_count -= 1

                    if success:

                        self.completed_count += 1

                    else:

                        self.failed_count += 1

                    # ---------- UPDATE LIVE QUEUE COUNT ----------

                    self.queued_count = len(
                        ticket_monitor.ticket_queue
                    )

                    self.gui_queue.put(
                        (
                            "stats",
                            {
                                "completed": self.completed_count,
                                "failed": self.failed_count,
                                "processing": self.processing_count,
                                "queued": self.queued_count
                            }
                        )
                    )



                    self.logger.info(
                        f"TICKET DATA AFTER PROCESS = {ticket}"
                    )

                    self.gui_queue.put(
                        (
                            "table",
                            (
                                ticket.get("ticket_id", ""),
                                ticket.get("domain", "Unknown"),
                                ticket["status"],
                                ticket.get("assignee", "-")
                            )
                        )
                    )

                
                time.sleep(5)

        except Exception as e:

            self.logger.error(
                f"Selenium Error: {str(e)}"
            )

    # ---------------- STOP BOT ----------------

    def stop(self):

        self.running = False

        try:

            self.selenium.close_driver()

            self.logger.warning(
                "Bot Stopped"
            )

        except Exception as e:

            self.logger.error(
                f"Close Error: {str(e)}"
            )

   