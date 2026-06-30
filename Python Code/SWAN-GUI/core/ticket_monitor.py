from config.settings import (
    MONITOR_REFRESH_INTERVAL,
    DASHBOARD_URL
)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)

import time


class TicketMonitor:

    def __init__(
        self,
        driver,
        logger
    ):

        self.driver = driver

        self.logger = logger

        self.wait = WebDriverWait(
            self.driver,
            20
        )

        self.seen_ticket_ids = set()

        self.ticket_queue = []

    # --------------------------------------------------
    # UPDATE DRIVER
    # --------------------------------------------------

    def update_driver(
        self,
        driver
    ):

        self.driver = driver

        self.wait = WebDriverWait(
            self.driver,
            20
        )

    # --------------------------------------------------
    # SAFE REFRESH
    # --------------------------------------------------

    def safe_refresh(self):

        for attempt in range(1, 4):

            try:

                self.logger.info(
                    f"Refreshing Dashboard ({attempt}/3)"
                )

                self.driver.get(
                    DASHBOARD_URL
                )

                WebDriverWait(
                    self.driver,
                    30
                ).until(

                    lambda d:
                    d.execute_script(
                        "return document.readyState"
                    ) == "complete"

                )

                return True

            except Exception as e:

                self.logger.warning(
                    f"Refresh Failed ({attempt}/3)"
                )

                time.sleep(2)

        return False

    # --------------------------------------------------
    # OPEN NEW TAB
    # --------------------------------------------------

    def open_new_tab(self):

        for attempt in range(1, 4):

            try:

                self.logger.info(
                    "Opening NEW Ticket Tab"
                )

                new_tile = self.wait.until(

                    EC.element_to_be_clickable(

                        (
                            By.XPATH,
                            "//a[contains(@onclick,'status == new')]"
                        )

                    )

                )

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    new_tile
                )

                time.sleep(1)

                self.driver.execute_script(
                    "arguments[0].click();",
                    new_tile
                )

                self.logger.success(
                    "NEW Tickets Tab Opened"
                )

                return True

            except Exception as e:

                self.logger.warning(
                    f"Open Tab Retry {attempt}/3"
                )

                time.sleep(2)

        self.logger.error(
            "Unable To Open NEW Ticket Tab"
        )

        return False

    # --------------------------------------------------
    # GET VALID ROWS
    # --------------------------------------------------

    def get_valid_rows(self):

        for attempt in range(1, 4):

            try:

                rows = self.driver.find_elements(

                    By.XPATH,

                    "//table[@id='ticketsTable']/tbody/tr"

                )

                valid_rows = []

                for row in rows:

                    cols = row.find_elements(
                        By.TAG_NAME,
                        "td"
                    )

                    if len(cols) >= 3:

                        valid_rows.append(row)

                self.logger.info(
                    f"Valid Rows Found: {len(valid_rows)}"
                )

                return valid_rows

            except (
                TimeoutException,
                StaleElementReferenceException,
                WebDriverException
            ):

                self.logger.warning(
                    f"Retry Getting Rows ({attempt}/3)"
                )

                time.sleep(2)

        self.logger.error(
            "Row Extraction Failed"
        )

        return []

    # --------------------------------------------------
    # EXTRACT TICKET DATA
    # --------------------------------------------------

    def extract_ticket_data(
        self,
        rows
    ):

        try:

            for row in rows:

                cols = row.find_elements(
                    By.TAG_NAME,
                    "td"
                )

                if len(cols) < 5:

                    continue

                ticket_id = cols[2].text.strip()

                if ticket_id in self.seen_ticket_ids:

                    continue

                if any(

                    t["ticket_id"] == ticket_id

                    for t in self.ticket_queue

                ):

                    continue

                ticket_title = cols[4].text.strip()

                self.logger.info(
                    f"ticket_id=[{ticket_id}] title=[{ticket_title}]"
                )

                self.ticket_queue.append(

                    {

                        "ticket_id": ticket_id,

                        "title": ticket_title

                    }

                )

                self.ticket_queue.sort(

                    key=lambda x:
                    int(x["ticket_id"])

                )

                self.logger.success(
                    f"Queued Ticket: {ticket_id}"
                )

                self.logger.info(
                    f"Queue Order: {[t['ticket_id'] for t in self.ticket_queue]}"
                )

        except Exception as e:

            self.logger.error(
                f"Ticket Extraction Error: {str(e)}"
            )

    # --------------------------------------------------
    # MONITOR
    # --------------------------------------------------

    def wait_for_new_tickets(self):

        try:

            # ---------- REFRESH DASHBOARD ----------

            if not self.safe_refresh():

                self.logger.error(
                    "Dashboard Refresh Failed"
                )

                time.sleep(
                    MONITOR_REFRESH_INTERVAL
                )

                return []

            time.sleep(3)

            # ---------- OPEN NEW TAB ----------

            if not self.open_new_tab():

                self.logger.error(
                    "Unable To Open NEW Ticket Tab"
                )

                time.sleep(
                    MONITOR_REFRESH_INTERVAL
                )

                return []

            time.sleep(2)

            # ---------- GET ROWS ----------

            valid_rows = self.get_valid_rows()

            if not valid_rows:

                self.logger.info(
                    "No Valid Ticket Rows Found"
                )

            # ---------- EXTRACT ----------

            self.extract_ticket_data(
                valid_rows
            )

            # ---------- PROCESS QUEUE ----------

            ticket_count = len(
                self.ticket_queue
            )

            if ticket_count > 0:

                self.logger.success(
                    f"Queue Size: {ticket_count}"
                )

                ticket = self.ticket_queue.pop(0)

                self.logger.info(
                    f"Processing Ticket: {ticket['ticket_id']}"
                )

                return [
                    ticket
                ]

            # ---------- NO TICKETS ----------

            self.logger.info(
                "No New Tickets Found"
            )

            self.logger.info(
                f"Sleeping For {MONITOR_REFRESH_INTERVAL} sec"
            )

            time.sleep(
                MONITOR_REFRESH_INTERVAL
            )

            return []

        except Exception as e:

            self.logger.error(
                f"Monitoring Error: {str(e)}"
            )

            time.sleep(
                MONITOR_REFRESH_INTERVAL
            )

            return []
