from datetime import timedelta
import logging

DOMAIN = "ennatuurlijk_disruptions"
CONF_TOWN = "town"
CONF_POSTAL_CODE = "postal_code"

CONF_ENABLED_SENSORS = "sensors"
CONF_DATE_FORMAT = "dateformat"
CONF_LOCALE = "locale"
CONF_ID = "id"
CONF_NO_DISRUPTIONS_TEXT = "nodisruptionstext"
CONF_CREATE_ALERT_SENSORS = "create_alert_sensors"
DEFAULT_CREATE_ALERT_SENSORS = True
DEFAULT_DAYS_TO_KEEP_SOLVED = 7
CONF_DAYS_TO_KEEP_SOLVED = "days_to_keep_solved"

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 120

SENSOR_PREFIX = "Ennatuurlijk Disruptions "
ATTR_ERROR = "error"
ATTR_LAST_UPDATE = "last_update"
ATTR_IS_PLANNED_DATE_TODAY = "is_planned_date_today"
ATTR_IS_CURRENT_DATE_TODAY = "is_current_date_today"
ATTR_IS_SOLVED_DATE_TODAY = "is_solved_date_today"
ATTR_DAYS_UNTIL_PLANNED_DATE = "days_until_planned_date"
ATTR_DAYS_SINCE_SOLVED_DATE = "days_since_solved_date"
ATTR_DAYS_SINCE_CURRENT_DATE = "days_since_current_date"
ATTR_YEAR_MONTH_DAY_DATE = "year_month_day_date"
ATTR_FRIENDLY_NAME = "friendly_name"
ATTR_LAST_DISRUPTION_DATE = "last_disruption_date"

SCAN_INTERVAL = timedelta(hours=2, minutes=30)

MONTH_TO_NUMBER = {
    "jan": "01",
    "feb": "02",
    "mrt": "03",
    "apr": "04",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "okt": "10",
    "nov": "11",
    "dec": "12",
    "januari": "01",
    "februari": "02",
    "maart": "03",
    "april": "04",
    "mei": "05",
    "juni": "06",
    "juli": "07",
    "augustus": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "december": "12",
}

NUMBER_TO_MONTH = {
    1: "januari",
    2: "februari",
    3: "maart",
    4: "april",
    5: "mei",
    6: "juni",
    7: "juli",
    8: "augustus",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}

_LOGGER = logging.getLogger(__name__)

ENNATUURLIJK_DISRUPTIONS_URL = "https://ennatuurlijk.nl/storingen"
ENNATUURLIJK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}