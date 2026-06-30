from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


class LoginManager:

    def __init__(self, driver, logger):

        self.driver = driver
        self.logger = logger

        self.wait = WebDriverWait(
            self.driver,
            20
        )

    # ---------------- LOGIN ----------------

    def login(
        self,
        portal_url,
        username,
        password
    ):

        try:

            # ---------- OPEN PORTAL ----------

            self.logger.info(
                "Opening Portal"
            )

            self.driver.get(portal_url)

            self.logger.success(
                "Portal Loaded Successfully"
            )

            # ---------- USERNAME ----------

            self.logger.info(
                "Waiting For Username Field"
            )

            username_box = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@type='text']"
                    )
                )
            )

            username_box.clear()

            username_box.send_keys(username)

            self.logger.success(
                "Username Entered"
            )

            # ---------- PASSWORD ----------

            self.logger.info(
                "Entering Password"
            )

            password_box = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@type='password']"
                    )
                )
            )

            password_box.clear()

            password_box.send_keys(password)

            self.logger.success(
                "Password Entered"
            )

            # ---------- LOGIN BUTTON ----------

            self.logger.info(
                "Clicking Login Button"
            )

            login_button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(),'Login')]"
                    )
                )
            )

            login_button.click()

            # ---------- WAIT AFTER LOGIN ----------

            self.logger.info(
                "Waiting For Dashboard"
            )

            time.sleep(5)

            # ---------- LOGIN SUCCESS ----------

            self.logger.success(
                "Login Successful"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Login Failed: {str(e)}"
            )

            return False

        # ---------------- CHECK SESSION ----------------

    def is_logged_in(self):

        try:

            self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="ulBannerID"]/li[3]/ul/li[2]/a'
                    )
                )
            )

            return True

        except:

            return False