AUTORI_EVENTS_URL = (
    "https://test-api.autori.io/api/dailymaintenance-a3/route/types/operation"
)
AUTORI_ROUTES_URL = "https://test-api.autori.io/api/dailymaintenance-a3/route/"
AUTORI_CONTRACTS_URL = "https://test-api.autori.io/api/dailymaintenance-a3/contracts/"
AUTORI_TOKEN_URL = (
    "https://login.microsoftonline.com/86792d09-0d81-4899-8d66-95dfc96c8014/oauth2/v2.0/token?"
    + "Scope=api://7f45c30e-cc67-4a93-85f1-0149b44c1cdf/.default"
)
INFRAROAD_UNITS_URL = (
    "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/query?since=72hours"
)
INFRAROAD_WORKS_URL = "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/{id}?history={history_size}"

AURAUS = "Auraus"
LIUKKAUDENTORJUNTA = "Liukkaudentorjunta"
PUHTAANAPITO = "Puhtaanapito"
HIEKANPOISTO = "Hiekanpoisto"
# MUUT is currenlty only for testing purposes, TODO, remove from production
MUUT = "Muut"
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
    "Muu työ": MUUT,
    "Kaivot": MUUT,
    "Metsätyöt": MUUT,
}
