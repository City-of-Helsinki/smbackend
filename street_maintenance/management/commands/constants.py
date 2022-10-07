from django.conf import settings

AUTORI_EVENTS_URL = settings.AUTORI_EVENTS_URL
AUTORI_ROUTES_URL = settings.AUTORI_ROUTES_URL
AUTORI_CONTRACTS_URL = settings.AUTORI_CONTRACTS_URL
AUTORI_TOKEN_URL = settings.AUTORI_TOKEN_URL
INFRAROAD_UNITS_URL = (
    "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/query?since=72hours"
)
INFRAROAD_WORKS_URL = "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/{id}?history={history_size}"


# Events are categorized into main groups
AURAUS = "Auraus"
LIUKKAUDENTORJUNTA = "Liukkaudentorjunta"
PUHTAANAPITO = "Puhtaanapito"
HIEKANPOISTO = "Hiekanpoisto"
# MUUT is currenlty only for testing purposes, TODO, remove from production
MUUT = "Muut"
# As data providers have different names for their events, the are mapped
# with this dict, so that every event that does the same has the same name.
EVENT_MAPPINGS = {
    "Auraus": AURAUS,
    "Auraus ja sohjonpoisto": AURAUS,
    "Lumen poisajo": AURAUS,
    "Lumensiirto": AURAUS,
    "Suolas": LIUKKAUDENTORJUNTA,
    "Suolaus (sirotinlaite)": LIUKKAUDENTORJUNTA,
    "Liuossuolaus": LIUKKAUDENTORJUNTA,
    "Hiekoitus": LIUKKAUDENTORJUNTA,
    "Hiekoitus (sirotinlaite)": LIUKKAUDENTORJUNTA,
    "Linjahiekoitus": LIUKKAUDENTORJUNTA,
    "Pistehiekoitus": LIUKKAUDENTORJUNTA,
    "Paannejään poisto": LIUKKAUDENTORJUNTA,
    "Puhtaanapito": PUHTAANAPITO,
    "Harjaus": PUHTAANAPITO,
    "Pesu": PUHTAANAPITO,
    "Harjaus ja sohjonpoisto": PUHTAANAPITO,
    "Pölynsidonta": PUHTAANAPITO,
    "Hiekanpoisto": HIEKANPOISTO,
    "Muut työt": MUUT,
    "Kaivot": MUUT,
    "Metsätyöt": MUUT,
    "Rikkakasvien torjunta": MUUT,
}
