from django.conf import settings

INFRAROAD = "INFRAROAD"
AUTORI = "AUTORI"
KUNTEC = "KUNTEC"
PROVIDER_CHOICES = (
    (INFRAROAD, "Infraroad"),
    (AUTORI, "Autori"),
    (KUNTEC, "Kuntec"),
)
PROVIDERS = [INFRAROAD, AUTORI, KUNTEC]

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
# Events are categorized into main groups:
AURAUS = "auraus"
LIUKKAUDENTORJUNTA = "liukkaudentorjunta"
PUHTAANAPITO = "puhtaanapito"
HIEKANPOISTO = "hiekanpoisto"
# MUUT is set to None as the events are not currently displayed.
MUUT = None

# As data providers have different names for their events, they are mapped
# with this dict, so that every event that does the same has the same name.
# The value is a list, as there can be events that belong to multiple main groups.
# e.g., event "Auraus ja hiekanpoisto".
EVENT_MAPPINGS = {
    "laiturin ja asema-alueen auraus": [AURAUS],
    "au": [AURAUS],
    "auraus": [AURAUS],
    "auraus ja sohjonpoisto": [AURAUS],
    "lumen poisajo": [AURAUS],
    "lumensiirto": [AURAUS],
    "etuaura": [AURAUS],
    "alusterä": [AURAUS],
    "sivuaura": [AURAUS],
    "höyläys": [AURAUS],
    "suolas": [LIUKKAUDENTORJUNTA],
    "suolaus (sirotinlaite)": [LIUKKAUDENTORJUNTA],
    "liuossuolaus": [LIUKKAUDENTORJUNTA],
    # Hiekoitus
    "hi": [LIUKKAUDENTORJUNTA],
    "su": [LIUKKAUDENTORJUNTA],
    "hiekoitus": [LIUKKAUDENTORJUNTA],
    "hiekotus": [LIUKKAUDENTORJUNTA],
    "hiekoitus (sirotinlaite)": [LIUKKAUDENTORJUNTA],
    "linjahiekoitus": [LIUKKAUDENTORJUNTA],
    "pistehiekoitus": [LIUKKAUDENTORJUNTA],
    "paannejään poisto": [LIUKKAUDENTORJUNTA],
    "sirotin": [LIUKKAUDENTORJUNTA],
    "laiturin ja asema-alueen liukkaudentorjunta": [LIUKKAUDENTORJUNTA],
    # Kadunpesu
    "pe": [PUHTAANAPITO],
    # Harjaus
    "hj": [PUHTAANAPITO],
    # Hiekanpoisto
    "hn": [PUHTAANAPITO],
    "puhtaanapito": [PUHTAANAPITO],
    "harjaus": [PUHTAANAPITO],
    "pesu": [PUHTAANAPITO],
    "harjaus ja sohjonpoisto": [PUHTAANAPITO],
    "pölynsidonta": [PUHTAANAPITO],
    "hiekanpoisto": [HIEKANPOISTO],
    "muu": [MUUT],
    "muut työt": [MUUT],
    "muu työ": [MUUT],
    "lisätyö": [MUUT],
    "viherhoito": [MUUT],
    "kaivot": [MUUT],
    "metsätyöt": [MUUT],
    "rikkakasvien torjunta": [MUUT],
    "paikkaus": [MUUT],
    "lisälaite 1": [MUUT],
    "lisälaite 2": [MUUT],
    "lisälaite 3": [MUUT],
    "pensaiden hoitoleikkaus": [MUUT],
    "puiden hoitoleikkaukset": [MUUT],
    "mittaus- ja tarkastustyöt": [MUUT],
    "siimaleikkurointi tai niittotyö": [MUUT],
    "liikennemerkkien pesu": [MUUT],
    "tiestötarkastus": [MUUT],
    "roskankeräys": [MUUT],
    "tuntityö": [MUUT],
    "pinnan tasaus": [MUUT],
    "lumivallien madaltaminen": [MUUT],
    "aurausviitoitus ja kinostimet": [MUUT],
}

# The number of works(point data with timestamp and event) to be fetched for every unit.
INFRAROAD_DEFAULT_WORKS_FETCH_SIZE = 10000
# In days, Note if value is increased the fetch size should also be increased.
INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE = 4
INFRAROAD_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# Length of Autori history size in days, max value is 31.
AUTORI_DEFAULT_WORKS_HISTORY_SIZE = 4
AUTORI_MAX_WORKS_HISTORY_SIZE = 31
AUTORI_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"
KUNTEC_DEFAULT_WORKS_HISTORY_SIZE = 4
KUNTEC_MAX_WORKS_HISTORY_SIZE = 31
KUNTEC_DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
