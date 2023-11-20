from eco_counter.constants import ECO_COUNTER, LAM_COUNTER, TRAFFIC_COUNTER

TEST_EC_STATION_NAME = "Auransilta"
TEST_TC_STATION_NAME = "Myllysilta"
TEST_LC_STATION_NAME = "Tie 8 Raisio"

ECO_COUNTER_TEST_COLUMN_NAMES = [
    "Auransilta AK",
    "Auransilta AP",
    "Auransilta JK",
    "Auransilta JP",
    "Auransilta PK",
    "Auransilta PP",
    "Auransilta BK",
    "Auransilta BP",
]

TRAFFIC_COUNTER_TEST_COLUMN_NAMES = [
    "Myllysilta AK",
    "Myllysilta AP",
    "Myllysilta PK",
    "Myllysilta PP",
    "Myllysilta JK",
    "Myllysilta JP",
    "Myllysilta BK",
    "Myllysilta BP",
    "Kalevantie 65 BK",
    "Kalevantie 65 BP",
    "Hämeentie 18 PK",
]

LAM_COUNTER_TEST_COLUMN_NAMES = [
    "Tie 8 Raisio AP",
    "Tie 8 Raisio AK",
    "Tie 8 Raisio PP",
    "Tie 8 Raisio PK",
    "Tie 8 Raisio JP",
    "Tie 8 Raisio JK",
    "Tie 8 Raisio BP",
    "Tie 8 Raisio BK",
]

TEST_COLUMN_NAMES = {
    ECO_COUNTER: ECO_COUNTER_TEST_COLUMN_NAMES,
    TRAFFIC_COUNTER: TRAFFIC_COUNTER_TEST_COLUMN_NAMES,
    LAM_COUNTER: LAM_COUNTER_TEST_COLUMN_NAMES,
}
