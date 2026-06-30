from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
    InvalidSessionIdException
)

from config.settings import (
    HEADLESS_MODE,
    CHROME_PROFILE
)

import time


class SeleniumManager:

    def __init__(self, logger):

        self.logger = logger

        self.driver = None

    # --------------------------------------------------
    # START DRIVER
    # --------------------------------------------------

    def start_driver(self):

        try:

            if self.driver:

                try:
                    self.driver.quit()
                except:
                    pass

                self.driver = None

            self.logger.info(
                "Initializing Chrome Driver"
            )

            options = webdriver.ChromeOptions()

            # ---------------- PROFILE ----------------

            options.add_argument(
                f"--user-data-dir={CHROME_PROFILE}"
            )

            options.add_argument(
                "--profile-directory=Default"
            )

            # ---------------- WINDOW ----------------

            options.add_argument(
                "--start-maximized"
            )

            options.add_argument(
                "--window-size=1920,1080"
            )

            # ---------------- PERFORMANCE ----------------

            options.add_argument(
                "--disable-gpu"
            )

            options.add_argument(
                "--disable-dev-shm-usage"
            )

            options.add_argument(
                "--no-sandbox"
            )

            options.add_argument(
                "--disable-notifications"
            )

            options.add_argument(
                "--disable-popup-blocking"
            )

            options.add_argument(
                "--disable-infobars"
            )

            options.add_argument(
                "--disable-extensions"
            )

            options.add_argument(
                "--disable-blink-features=AutomationControlled"
            )

            options.add_argument(
                "--ignore-certificate-errors"
            )

            options.add_argument(
                "--allow-insecure-localhost"
            )

            options.add_argument(
                "--ignore-ssl-errors=yes"
            )

            options.add_argument(
                "--log-level=3"
            )

            # ---------------- HEADLESS ----------------

            if HEADLESS_MODE:

                options.add_argument(
                    "--headless=new"
                )

            # ---------------- EXPERIMENTAL ----------------

            options.add_experimental_option(
                "excludeSwitches",
                [
                    "enable-automation"
                ]
            )

            options.add_experimental_option(
                "useAutomationExtension",
                False
            )

            # ---------------- CREATE DRIVER ----------------

            self.driver = webdriver.Chrome(
                options=options
            )

            self.driver.set_page_load_timeout(
                60
            )

            self.driver.implicitly_wait(
                10
            )

            self.driver.get(
                "https://www.google.com"
            )

            self.logger.success(
                f"Chrome {self.driver.capabilities['browserVersion']} Started Successfully"
            )

            self.logger.success(
                "Chrome Profile Loaded"
            )

            self.logger.success(
                "Selenium Ready"
            )

            return self.driver

        except Exception as e:

            self.logger.error(
                f"Driver Error: {str(e)}"
            )

            self.driver = None

            return None

    # --------------------------------------------------
    # DRIVER HEALTH
    # --------------------------------------------------

    def is_alive(self):

        try:

            if self.driver is None:

                return False

            self.driver.current_url

            return True

        except (
            InvalidSessionIdException,
            WebDriverException,
            Exception
        ):

            return False

    # --------------------------------------------------
    # RESTART DRIVER
    # --------------------------------------------------

    def restart_driver(self):

        self.logger.warning(
            "Restarting Chrome Driver"
        )

        self.close_driver()

        time.sleep(2)

        return self.start_driver()

    # --------------------------------------------------
    # GET DRIVER
    # --------------------------------------------------

    def get_driver(self):

        return self.driver

    # --------------------------------------------------
    # CLOSE DRIVER
    # --------------------------------------------------

    def close_driver(self):

        try:

            if self.driver:

                self.driver.quit()

                self.logger.warning(
                    "Chrome Driver Closed"
                )

        except Exception as e:

            self.logger.error(
                f"Close Driver Error: {str(e)}"
            )

        finally:

            self.driver = None