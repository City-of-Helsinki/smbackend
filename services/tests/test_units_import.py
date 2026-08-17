import datetime
from zoneinfo import ZoneInfo

from services.management.commands.services_import.units import _parse_created_time

HELSINKI = ZoneInfo("Europe/Helsinki")


def test_parse_created_time_preserves_normal_local_timestamp():
    value = _parse_created_time("2025-01-15T12:30:00")

    assert value == datetime.datetime(2025, 1, 15, 12, 30, tzinfo=HELSINKI)


def test_parse_created_time_advances_nonexistent_dst_gap():
    value = _parse_created_time("2025-03-30T03:30:00")

    assert value == datetime.datetime(2025, 3, 30, 4, 30, tzinfo=HELSINKI)
    assert value.utcoffset() == datetime.timedelta(hours=3)


def test_parse_created_time_uses_later_ambiguous_dst_fold():
    value = _parse_created_time("2025-10-26T03:30:00")

    assert value.fold == 1
    assert value.utcoffset() == datetime.timedelta(hours=2)
