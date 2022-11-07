from django.conf import settings

AUTORI_EVENTS_URL = settings.AUTORI_EVENTS_URL
AUTORI_ROUTES_URL = settings.AUTORI_ROUTES_URL
AUTORI_VEHICLES_URL = settings.AUTORI_VEHICLES_URL
AUTORI_CONTRACTS_URL = settings.AUTORI_CONTRACTS_URL
AUTORI_TOKEN_URL = settings.AUTORI_TOKEN_URL

INFRAROAD_UNITS_URL = (
    "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/query?since=72hours"
)
INFRAROAD_WORKS_URL = "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/{id}?history={history_size}"

KUNTEC_KEY = settings.KUNTEC_KEY
KUNTEC_UNITS_URL = (
    f"https://mapon.com/api/v1/unit/list.json?key={KUNTEC_KEY}&include=io_din"
)
KUNTEC_WORKS_URL = (
    "https://mapon.com/api/v1/route/list.json?key={key}&from={start}"
    "&till={end}&include=polyline&unit_id={unit_id}"
)
# Events are categorized into flowwoing main groups:
AURAUS = "auraus"
LIUKKAUDENTORJUNTA = "liukkaudentorjunta"
PUHTAANAPITO = "puhtaanapito"
HIEKANPOISTO = "hiekanpoisto"
# MUUT is currenlty only for testing purposes, TODO, remove from production
MUUT = "muut"
# As data providers have different names for their events, they are mapped
# with this dict, so that every event that does the same has the same name.
EVENT_MAPPINGS = {
    "auraus": AURAUS,
    "auraus ja sohjonpoisto": AURAUS,
    "lumen poisajo": AURAUS,
    "lumensiirto": AURAUS,
    "suolas": LIUKKAUDENTORJUNTA,
    "suolaus (sirotinlaite)": LIUKKAUDENTORJUNTA,
    "liuossuolaus": LIUKKAUDENTORJUNTA,
    "hiekoitus": LIUKKAUDENTORJUNTA,
    "hiekotus": LIUKKAUDENTORJUNTA,
    "hiekoitus (sirotinlaite)": LIUKKAUDENTORJUNTA,
    "linjahiekoitus": LIUKKAUDENTORJUNTA,
    "pistehiekoitus": LIUKKAUDENTORJUNTA,
    "paannejään poisto": LIUKKAUDENTORJUNTA,
    "puhtaanapito": PUHTAANAPITO,
    "harjaus": PUHTAANAPITO,
    "pesu": PUHTAANAPITO,
    "harjaus ja sohjonpoisto": PUHTAANAPITO,
    "pölynsidonta": PUHTAANAPITO,
    "hiekanpoisto": HIEKANPOISTO,
    "muut työt": MUUT,
    "lisätyö": MUUT,
    "viherhoito": MUUT,
    "kaivot": MUUT,
    "metsätyöt": MUUT,
    "rikkakasvien torjunta": MUUT,
    "paikkaus": MUUT,
}
# The number of works(point data with timestamp and event) to be fetched for every unit.
INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE = 10000
# Length of Autori history size in days, max value is 31.
AUTORI_DEFAULT_WORKS_HISTORY_SIZE = 5
AUTORI_MAX_WORKS_HISTORY_SIZE = 31
AUTORI_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"
KUNTEC_DEFAULT_WORKS_HISTORY_SIZE = 10
KUNTEC_MAX_WORKS_HISTORY_SIZE = 31
KUNTEC_DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
