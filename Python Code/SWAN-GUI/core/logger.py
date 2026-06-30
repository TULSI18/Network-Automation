from datetime import datetime


class EnterpriseLogger:

    def __init__(self, gui_queue=None):

        self.gui_queue = gui_queue


    # ---------------- MAIN LOGGER ----------------

    def log(self, message, level="INFO"):

        current_time = datetime.now().strftime("%H:%M:%S")

        formatted_message = (
            f"[{current_time}] "
            f"{level:<8} "
            f"{message}"
        )

        # ---------- CLI OUTPUT ----------

        print(formatted_message)


        # ---------- GUI OUTPUT ----------

        if self.gui_queue:

            self.gui_queue.put(
                (
                    "log",
                    message,
                    level
                )
            )


        # ---------- FILE LOGGING ----------

        with open(
            "logs/runtime.log",
            "a",
            encoding="utf-8"
        ) as log_file:

            log_file.write(
                formatted_message + "\n"
            )


    # ---------------- SHORTCUT METHODS ----------------

    def info(self, message):

        self.log(message, "INFO")


    def success(self, message):

        self.log(message, "SUCCESS")


    def warning(self, message):

        self.log(message, "WARNING")


    def error(self, message):

        self.log(message, "ERROR")