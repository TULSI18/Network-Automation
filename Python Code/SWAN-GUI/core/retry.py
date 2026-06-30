import time


class RetryEngine:

    def __init__(
        self,
        logger,
        retries=3,
        delay=2
    ):

        self.logger = logger
        self.retries = retries
        self.delay = delay

    def execute(
        self,
        func,
        action_name,
        *args,
        **kwargs
    ):

        last_exception = None

        for attempt in range(
            1,
            self.retries + 1
        ):

            try:

                result = func(
                    *args,
                    **kwargs
                )

                if attempt > 1:

                    self.logger.success(
                        f"{action_name} succeeded on attempt {attempt}"
                    )

                return result

            except Exception as e:

                last_exception = e

                self.logger.warning(
                    f"{action_name} failed "
                    f"(Attempt {attempt}/{self.retries})"
                )

                if attempt < self.retries:

                    time.sleep(
                        self.delay
                    )

        self.logger.error(
            f"{action_name} failed after "
            f"{self.retries} attempts"
        )

        raise last_exception