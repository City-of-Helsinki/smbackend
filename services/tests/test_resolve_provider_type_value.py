import pytest
from rest_framework.exceptions import ParseError

from services.api import resolve_provider_type_value
from services.models.unit import PROVIDER_TYPES


@pytest.mark.parametrize("int_val, str_val", PROVIDER_TYPES)
def test_valid_integer_string_returns_int(int_val, str_val):
    assert resolve_provider_type_value(str(int_val)) == int_val


@pytest.mark.parametrize("int_val, str_val", PROVIDER_TYPES)
def test_valid_string_label_returns_int(int_val, str_val):
    assert resolve_provider_type_value(str_val) == int_val


@pytest.mark.parametrize(
    "value",
    [
        "999",  # integer not in PROVIDER_TYPES
        "0",  # zero is not a valid type
        "-1",  # negative integer
        "UNKNOWN_TYPE",  # unrecognised string label
        "",  # empty string
    ],
)
def test_invalid_value_raises_parse_error(value):
    with pytest.raises(ParseError):
        resolve_provider_type_value(value)


def test_parse_error_message_contains_value():
    bad_value = "BAD_VALUE"
    with pytest.raises(ParseError) as exc_info:
        resolve_provider_type_value(bad_value)
    assert bad_value in str(exc_info.value.detail)
