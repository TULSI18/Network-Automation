
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


class TicketProcessor:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.wait = WebDriverWait(self.driver, 25)

        # ---------- Retry Configuration ----------

        self.max_retry = 3

        self.retry_delay = 2

        self.driver_alive = True

    # ---------------- UPDATE DRIVER ----------------

    def update_driver(
        self,
        driver
    ):

        self.driver = driver

        self.wait = WebDriverWait(
            self.driver,
            20
        )

        self.driver_alive = True

        self.logger.success(
            "TicketProcessor Driver Updated"
        )


    # ---------------- RETRY ----------------

    def retry(
        self,
        func,
        *args,
        **kwargs
    ):

        last_error = None

        for attempt in range(
            1,
            self.max_retry + 1
        ):

            try:

                return func(
                    *args,
                    **kwargs
                )

            except Exception as e:

                last_error = e

                self.logger.warning(
                    f"Retry {attempt}/{self.max_retry} : {str(e)}"
                )

                time.sleep(
                    self.retry_delay
                )

        raise last_error


    # ---------------- DRIVER CHECK ----------------

    def is_driver_alive(self):

        try:

            self.driver.current_url

            return True

        except Exception:

            self.driver_alive = False

            return False
    # ---------------- JS CLICK ----------------

    def js_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            element
        )
        time.sleep(0.5)
        self.driver.execute_script(
            "arguments[0].click();",
            element
        )

    # ---------------- SAFE SELECT ----------------

    def safe_select(self, by, locator, text, field_name):

        dropdown = self.wait.until(
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

        self.logger.success(f"{field_name}: {text}")

    # ---------------- OPEN TICKET ----------------

    def open_ticket(
        self,
        ticket
    ):

        if not self.is_driver_alive():

            self.logger.error(
                "Driver Not Available"
            )

            return False

        try:

            ticket_id = ticket["ticket_id"]

            rows = self.retry(
                self.driver.find_elements,
                By.XPATH,
                "//table//tbody/tr"
            )

            for row in rows:

                cols = row.find_elements(
                    By.TAG_NAME,
                    "td"
                )

                if len(cols) < 5:

                    continue

                current_ticket = cols[2].text.strip()

                if current_ticket == ticket_id:

                    ticket_link = row.find_element(
                        By.XPATH,
                        "./td[3]//a"
                    )

                    self.retry(
                        self.js_click,
                        ticket_link
                    )

                    time.sleep(3)

                    self.logger.success(
                        f"Opened Ticket: {ticket_id}"
                    )

                    return True

            self.logger.error(
                f"Ticket No Longer In NEW Queue: {ticket_id}"
            )

            return False

        except Exception as e:

            self.logger.error(
                f"Open Ticket Error: {str(e)}"
            )

            return False

    # ---------------- OPEN UPDATE PAGE ----------------

    def open_update_page(self):

        if not self.is_driver_alive():

            self.logger.error(
                "Driver Not Available"
            )

            return False

        try:

            self.retry(
                self.wait.until,
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "ticketUpdateForm"
                    )
                )
            )

            self.logger.success(
                "Ticket Update Page Opened"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Update Page Error: {str(e)}"
            )

            return False

    # ---------------- GET DOMAIN ----------------

    def get_domain(self):

        try:

            domain = self.driver.find_element(
                By.XPATH,
                "//label[contains(normalize-space(),'Domain')]/following::p[1]"
            ).text.strip()

            domain = domain.replace(":", "").strip()

            self.logger.success(f"Domain Found: {domain}")

            return domain

        except Exception as e:

            self.logger.error(f"Domain Error: {e}")

            return ""

    # ---------------- DOMAIN RULES ----------------

    def apply_domain_rules(self, domain):

        self.logger.info(
            f"Applying Rules For Domain: {domain}"
        )

        ticket_assignee = "-"

        try:

            if domain == "Jio_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "swanjio - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "swanjio - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Airtel_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Airtel",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Airtel - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Airtel - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain in [
                "Bsnl_Managed_Services",
                "Bsnl_Maneged_Services"
            ]:

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Bsnl_Managed - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Bsnl_Managed - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Bsnl":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl",
                    "Category"
                )

            elif domain == "Jio":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio",
                    "Category"
                )

            else:

                self.logger.info(
                    f"No domain rule matched for {domain}"
                )

            self.safe_select(
                By.ID,
                "status",
                "In Progress",
                "Status"
            )

            self.logger.success(
                "Domain Rules Applied"
            )

            self.current_assignee = ticket_assignee

            return True

        except Exception as e:

            self.logger.error(
                f"Rule Engine Error: {e}"
            )

            return False

    # ---------------- SAVE ----------------

    def save_ticket(self):

        if not self.is_driver_alive():

            self.logger.error(
                "Driver Not Available"
            )

            return False

        try:

            update_btn = self.retry(

                self.wait.until,

                EC.presence_of_element_located(

                    (
                        By.ID,
                        "btnUpdateClickSave"
                    )
                )
            )

            self.retry(

                self.js_click,

                update_btn
            )

            time.sleep(5)

            self.logger.success(
                "Ticket Saved Successfully"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Save Ticket Error: {str(e)}"
            )

            return False


    # ---------------- PROCESS ----------------

    def process_ticket(
        self,
        ticket
    ):

        if not self.is_driver_alive():

            self.logger.error(
                "Driver Not Available"
            )

            return False

        try:

            self.logger.info(
                f"Processing Ticket: {ticket.get('ticket_id', '')}"
            )

            # ---------- OPEN TICKET ----------

            if not self.retry(
                self.open_ticket,
                ticket
            ):

                return False

            # ---------- OPEN UPDATE PAGE ----------

            if not self.retry(
                self.open_update_page
            ):

                return False

            # ---------- DOMAIN ----------

            domain = self.retry(
                self.get_domain
            )

            ticket["domain"] = domain

            # ---------- APPLY RULES ----------

            if not self.retry(
                self.apply_domain_rules,
                domain
            ):

                return False

            # ---------- SAVE ----------

            if not self.retry(
                self.save_ticket
            ):

                return False

            self.logger.success(
                f"Ticket Processed: {ticket.get('ticket_id', '')}"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Process Ticket Error: {str(e)}"
            )

            return False

            # ---------- FINAL STATUS FOR GUI ----------

            ticket["status"] = "Completed"

            ticket["assignee"] = getattr(
                self,
                "current_assignee",
                "-"
            )

            if hasattr(self, "ticket_monitor"):

                self.ticket_monitor.seen_ticket_ids.add(
                    ticket["ticket_id"]
                )

                self.logger.success(
                    f"Marked Processed: {ticket['ticket_id']}"
                )

            self.logger.success(
                f"Ticket Processed: {ticket.get('ticket_id', '')}"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Processing Error: {e}"
            )

            return False

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


class TicketProcessor:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.wait = WebDriverWait(self.driver, 25)

    # ---------------- JS CLICK ----------------

    def js_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            element
        )
        time.sleep(0.5)
        self.driver.execute_script(
            "arguments[0].click();",
            element
        )

    # ---------------- SAFE SELECT ----------------

    def safe_select(self, by, locator, text, field_name):

        dropdown = self.wait.until(
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

        self.logger.success(f"{field_name}: {text}")

    # ---------------- OPEN TICKET ----------------

    def open_ticket(self, ticket):

        try:

            ticket_id = ticket["ticket_id"]

            rows = self.driver.find_elements(
                By.XPATH,
                "//table//tbody/tr"
            )

            for row in rows:

                cols = row.find_elements(
                    By.TAG_NAME,
                    "td"
                )

                if len(cols) < 5:

                    continue

                current_ticket = cols[2].text.strip()

                if current_ticket == ticket_id:

                    ticket_link = row.find_element(
                        By.XPATH,
                        "./td[3]//a"
                    )

                    self.js_click(
                        ticket_link
                    )

                    time.sleep(3)

                    self.logger.success(
                        f"Opened Ticket: {ticket_id}"
                    )

                    return True

            self.logger.error(
                f"Ticket No Longer In NEW Queue: {ticket_id}"
            )

            return False

        except Exception as e:

            self.logger.error(
                f"Open Ticket Error: {e}"
            )

            return False

    # ---------------- OPEN UPDATE PAGE ----------------

    def open_update_page(self):

        try:

            edit_btn = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//button[normalize-space()='Update']"
                    )
                )
            )

            self.js_click(edit_btn)

            time.sleep(3)

            self.logger.success("Ticket Update Page Opened")

            return True

        except Exception as e:

            self.logger.error(
                f"Update Page Error: {e}"
            )

            return False

    # ---------------- GET DOMAIN ----------------

    def get_domain(self):

        try:

            domain = self.driver.find_element(
                By.XPATH,
                "//label[contains(normalize-space(),'Domain')]/following::p[1]"
            ).text.strip()

            domain = domain.replace(":", "").strip()

            self.logger.success(f"Domain Found: {domain}")

            return domain

        except Exception as e:

            self.logger.error(f"Domain Error: {e}")

            return ""

    # ---------------- DOMAIN RULES ----------------

    def apply_domain_rules(self, domain):

        self.logger.info(
            f"Applying Rules For Domain: {domain}"
        )

        ticket_assignee = "-"

        try:

            if domain == "Jio_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "swanjio - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "swanjio - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Airtel_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Airtel",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Airtel - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Airtel - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain in [
                "Bsnl_Managed_Services",
                "Bsnl_Maneged_Services"
            ]:

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Bsnl_Managed - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Bsnl_Managed - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Bsnl":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl",
                    "Category"
                )

            elif domain == "Jio":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio",
                    "Category"
                )

            else:

                self.logger.info(
                    f"No domain rule matched for {domain}"
                )

            self.safe_select(
                By.ID,
                "status",
                "In Progress",
                "Status"
            )

            self.logger.success(
                "Domain Rules Applied"
            )

            self.current_assignee = ticket_assignee

            return True

        except Exception as e:

            self.logger.error(
                f"Rule Engine Error: {e}"
            )

            return False

    # ---------------- SAVE ----------------

    def save_ticket(self):

        try:

            update_btn = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "btnUpdateClickSave"
                    )
                )
            )

            self.js_click(update_btn)

            time.sleep(5)

            self.logger.success(
                "Ticket Saved Successfully"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Save Ticket Error: {e}"
            )

            return False


    # ---------------- PROCESS ----------------

    def process_ticket(self, ticket):

        try:

            self.logger.info(
                f"Processing Ticket: {ticket.get('ticket_id', '')}"
            )

            if not self.open_ticket(ticket):
                return False

            if not self.open_update_page():
                return False

            domain = self.get_domain()

            ticket["domain"] = domain

            if not self.apply_domain_rules(domain):
                return False

            if not self.save_ticket():
                return False

            # ---------- FINAL STATUS FOR GUI ----------

            ticket["status"] = "Completed"

            ticket["assignee"] = getattr(
                self,
                "current_assignee",
                "-"
            )

            if hasattr(self, "ticket_monitor"):

                self.ticket_monitor.seen_ticket_ids.add(
                    ticket["ticket_id"]
                )

                self.logger.success(
                    f"Marked Processed: {ticket['ticket_id']}"
                )

            self.logger.success(
                f"Ticket Processed: {ticket.get('ticket_id', '')}"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Processing Error: {e}"
            )

            return False

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


class TicketProcessor:

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.wait = WebDriverWait(self.driver, 25)

    # ---------------- JS CLICK ----------------

    def js_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            element
        )
        time.sleep(0.5)
        self.driver.execute_script(
            "arguments[0].click();",
            element
        )

    # ---------------- SAFE SELECT ----------------

    def safe_select(self, by, locator, text, field_name):

        dropdown = self.wait.until(
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

        self.logger.success(f"{field_name}: {text}")

    # ---------------- OPEN TICKET ----------------

    def open_ticket(self, ticket):

        try:

            ticket_id = ticket["ticket_id"]

            rows = self.driver.find_elements(
                By.XPATH,
                "//table//tbody/tr"
            )

            for row in rows:

                cols = row.find_elements(
                    By.TAG_NAME,
                    "td"
                )

                if len(cols) < 5:

                    continue

                current_ticket = cols[2].text.strip()

                if current_ticket == ticket_id:

                    ticket_link = row.find_element(
                        By.XPATH,
                        "./td[3]//a"
                    )

                    self.js_click(
                        ticket_link
                    )

                    time.sleep(3)

                    self.logger.success(
                        f"Opened Ticket: {ticket_id}"
                    )

                    return True

            self.logger.error(
                f"Ticket No Longer In NEW Queue: {ticket_id}"
            )

            return False

        except Exception as e:

            self.logger.error(
                f"Open Ticket Error: {e}"
            )

            return False

    # ---------------- OPEN UPDATE PAGE ----------------

    def open_update_page(self):

        try:

            edit_btn = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//button[normalize-space()='Update']"
                    )
                )
            )

            self.js_click(edit_btn)

            time.sleep(3)

            self.logger.success("Ticket Update Page Opened")

            return True

        except Exception as e:

            self.logger.error(
                f"Update Page Error: {e}"
            )

            return False

    # ---------------- GET DOMAIN ----------------

    def get_domain(self):

        try:

            domain = self.driver.find_element(
                By.XPATH,
                "//label[contains(normalize-space(),'Domain')]/following::p[1]"
            ).text.strip()

            domain = domain.replace(":", "").strip()

            self.logger.success(f"Domain Found: {domain}")

            return domain

        except Exception as e:

            self.logger.error(f"Domain Error: {e}")

            return ""

    # ---------------- DOMAIN RULES ----------------

    def apply_domain_rules(self, domain):

        self.logger.info(
            f"Applying Rules For Domain: {domain}"
        )

        ticket_assignee = "-"

        try:

            if domain == "Jio_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "swanjio - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "swanjio - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Airtel_Managed_Services":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Airtel",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Airtel - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Airtel - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain in [
                "Bsnl_Managed_Services",
                "Bsnl_Maneged_Services"
            ]:

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl Managed Links",
                    "Category"
                )

                self.safe_select(
                    By.ID,
                    "ticket_type_select_comp",
                    "Horizontal",
                    "Ticket Type"
                )

                self.safe_select(
                    By.ID,
                    "assignee",
                    "Bsnl_Managed - Live",
                    "Ticket Assignee"
                )

                ticket_assignee = "Bsnl_Managed - Live"

                self.safe_select(
                    By.NAME,
                    "priority",
                    "Low",
                    "Priority"
                )

                self.safe_select(
                    By.NAME,
                    "2_cusID",
                    "Link Down",
                    "RCA Initial"
                )

            elif domain == "Bsnl":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Bsnl",
                    "Category"
                )

            elif domain == "Jio":

                self.safe_select(
                    By.NAME,
                    "cat",
                    "Jio",
                    "Category"
                )

            else:

                self.logger.info(
                    f"No domain rule matched for {domain}"
                )

            self.safe_select(
                By.ID,
                "status",
                "In Progress",
                "Status"
            )

            self.logger.success(
                "Domain Rules Applied"
            )

            self.current_assignee = ticket_assignee

            return True

        except Exception as e:

            self.logger.error(
                f"Rule Engine Error: {e}"
            )

            return False

    # ---------------- SAVE ----------------

    def save_ticket(self):

        try:

            update_btn = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "btnUpdateClickSave"
                    )
                )
            )

            self.js_click(update_btn)

            time.sleep(5)

            self.logger.success(
                "Ticket Saved Successfully"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Save Ticket Error: {e}"
            )

            return False


    # ---------------- PROCESS ----------------

    def process_ticket(self, ticket):

        try:

            self.logger.info(
                f"Processing Ticket: {ticket.get('ticket_id', '')}"
            )

            if not self.open_ticket(ticket):
                return False

            if not self.open_update_page():
                return False

            domain = self.get_domain()

            ticket["domain"] = domain

            if not self.apply_domain_rules(domain):
                return False

            if not self.save_ticket():
                return False

            # ---------- FINAL STATUS FOR GUI ----------

            ticket["status"] = "Completed"

            ticket["assignee"] = getattr(
                self,
                "current_assignee",
                "-"
            )

            if hasattr(self, "ticket_monitor"):

                self.ticket_monitor.seen_ticket_ids.add(
                    ticket["ticket_id"]
                )

                self.logger.success(
                    f"Marked Processed: {ticket['ticket_id']}"
                )

            self.logger.success(
                f"Ticket Processed: {ticket.get('ticket_id', '')}"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Processing Error: {e}"
            )

            return False