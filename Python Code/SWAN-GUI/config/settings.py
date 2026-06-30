# ---------------- PORTAL ----------------

PORTAL_URL = "https://10.124.4.55:8080/controller/Home"


# ---------------- BOT ----------------

MONITOR_INTERVAL = 10


# ---------------- SELENIUM ----------------

HEADLESS_MODE = False

# ---------------- MONITOR ----------------

MONITOR_REFRESH_INTERVAL = 15

# ---------------- PAGES ----------------

DASHBOARD_URL = (
    "https://10.124.4.55:8080/controller/Home"
)
#---------------------------------------------------------

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROME_PROFILE = PROJECT_ROOT / "chrome_profile"

HEADLESS_MODE = False