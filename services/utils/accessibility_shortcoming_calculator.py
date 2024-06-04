import logging

from services.accessibility import RULES

logger = logging.getLogger(__name__)

PROFILE_IDS = {
    1: "wheelchair",
    2: "reduced_mobility",
    3: "rollator",
    4: "stroller",
    5: "visually_impaired",
    6: "hearing_aid",
}

PATH_TITLES = {
    "outside": {"fi": "Pysäköinti", "sv": "Parkering", "en": "Parking"},
    "parking_hall": {"fi": "Pysäköinti", "sv": "Parkering", "en": "Parking"},
    "route_to_entrance": {
        "fi": "Reitti pääsisäänkäynnille",
        "sv": "Väg till huvudingången",
        "en": "Route to entrance",
    },
    "entrance": {"fi": "Pääsisäänkäynti", "sv": "Huvudingång", "en": "Entrance"},
    "interior": {"fi": "Sisätilat", "sv": "Inomhuslokaler", "en": "Interior"},
    "outdoor_sport_facility": {
        "fi": "Ulkoliikuntapaikka",
        "sv": "Utomhusstället",
        "en": "Outdoors sports facility",
    },
    "route_to_outdoor_sport_facility": {
        "fi": "Reitti ulkoliikuntapaikkaan",
        "sv": "Väg till utomhusstället",
        "en": "Route to outdoors sports facility",
    },
    "service_point": {
        "fi": "Toimipiste",
        "sv": "Verksamhetsställe",
        "en": "Service point",
    },
}


class OperatorError(Exception):
    def __init__(self, operator):
        self.message = "Invalid operator {}".format(operator)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AccessibilityShortcomingCalculator(object, metaclass=Singleton):
    def __init__(self):
        try:
            self.rules, self.messages = RULES.get_data()
        except FileNotFoundError as e:
            logger.error(e)
            self.rules, self.messages = {}, []

    def calculate(self, unit):
        self.shortcomings = {}
        properties_by_id = {
            p.variable.id: p.value for p in unit.accessibility_properties.all()
        }
        profile_dict = {
            profile_id: [
                rule for rule in self.rules.keys() if rule[0] == str(profile_id)
            ]
            for profile_id in PROFILE_IDS.keys()
        }
        for profile_id, profiles in profile_dict.items():
            for profile in profiles:
                self._calculate_shortcomings(
                    self.rules[profile], properties_by_id, {}, profile_id
                )
        shortcomings = {}
        counts = {}
        for profile, titles in self.shortcomings.items():
            for title, codes in titles.items():
                shortcomings[title] = shortcomings.get(title, {})
                shortcomings[title][profile] = shortcomings[title].get(profile, set())
                shortcomings[title][profile].update(codes)
                counts[profile] = counts.get(profile, 0) + len(codes)

        return (
            [
                {
                    "title": PATH_TITLES[title],
                    "profiles": [
                        {
                            "id": PROFILE_IDS[profile],
                            "shortcomings": [self.messages[code] for code in codes],
                        }
                        for profile, codes in profiles.items()
                    ],
                }
                for title, profiles in shortcomings.items()
            ],
            {PROFILE_IDS[profile]: count for profile, count in counts.items()},
        )

    def _calculate_shortcomings(self, rule, properties, messages, profile_id):
        if not isinstance(rule["operands"][0], dict):
            # This is a leaf rule.
            prop = properties.get(rule["operands"][0])
            # If the information is not supplied, pretend that everything is fine.
            if not prop:
                logger.debug(
                    "{}: No property {}".format(rule["id"], rule["operands"][0])
                )
                return True, False

            if rule["operator"] not in ["EQ", "NEQ"]:
                raise OperatorError(rule["operator"])

            val = rule["operands"][1]
            is_ok = (prop == val) if rule["operator"] == "EQ" else (prop != val)

            message_recorded = (
                self._record_shortcoming(rule, messages, profile_id)
                if not is_ok
                else False
            )
            logger.debug(
                "{}: {} {}".format(
                    rule["id"],
                    rule["operator"],
                    (
                        "{}recorded".format("" if message_recorded else "not ")
                        if not is_ok
                        else "passed"
                    ),
                )
            )
            return is_ok, message_recorded

        # This is a compound rule.
        return_values = []
        for op in rule["operands"]:
            is_ok, message_recorded = self._calculate_shortcomings(
                op, properties, messages, profile_id
            )
            if rule["operator"] == "AND" and not is_ok and not message_recorded:
                # Short circuit AND evaluation when no message was emitted. This edge case is required!
                # NOTE: No messages are emitted from the AND clause itself.
                logger.debug("{}: AND short circuited".format(rule["id"]))
                return False, False
            if rule["operator"] == "OR" and is_ok:
                # Short circuit with OR too when matching satisfying condition found.
                logger.debug("{}: OR short circuited".format(rule["id"]))
                return True, False
            return_values.append(is_ok)

        if rule["operator"] not in ["AND", "OR"]:
            raise OperatorError(rule["operator"])

        if rule["operator"] == "AND" and False not in return_values:
            logger.debug("{}: AND met".format(rule["id"]))
            return True, False
        if rule["operator"] == "OR" and True in return_values:
            # This condition is never met due to OR short circuiting above
            logger.debug("{}: OR met".format(rule["id"]))
            return True, False

        message_recorded = self._record_shortcoming(rule, messages, profile_id)
        logger.debug(
            "{}: {} {}".format(
                rule["id"],
                rule["operator"],
                "{}recorded".format("" if message_recorded else "not "),
            )
        )
        return False, message_recorded

    def _record_shortcoming(self, rule, messages, profile_id):
        if rule["msg"] is None or rule["msg"] >= len(self.messages):
            return False

        def record(segment, message):
            self.shortcomings[profile_id] = self.shortcomings.get(profile_id, {})
            self.shortcomings[profile_id][segment] = self.shortcomings[profile_id].get(
                segment, set()
            )
            self.shortcomings[profile_id][segment].add(message)

        segment = rule["path"][0]
        requirement_id = rule["requirement_id"]
        messages[segment] = messages.get(segment, {})
        messages[segment][requirement_id] = messages[segment].get(requirement_id, [])
        if rule["id"] == requirement_id:
            # This is a top level requirement - only add top level message if there are no specific messages.
            if not messages[segment][requirement_id]:
                messages[segment][requirement_id].append(rule["msg"])
                record(segment, rule["msg"])
        else:
            messages[segment][requirement_id].append(rule["msg"])
            record(segment, rule["msg"])
        return True
