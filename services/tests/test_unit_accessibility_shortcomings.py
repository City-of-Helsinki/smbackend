import pytest
from django.core.management import call_command
from django.utils.timezone import now
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from urllib.parse import urlencode

from services.models import AccessibilityVariable, Unit, UnitAccessibilityProperty
from services.utils.accessibility_shortcoming_calculator import OperatorException


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def unit():
    unit = Unit.objects.create(id=1, name="test unit", last_modified_time=now(),)
    return unit


@pytest.fixture
def unit_with_props(unit):
    variable = AccessibilityVariable.objects.get_or_create(id=1, name="var")[0]
    UnitAccessibilityProperty.objects.create(unit=unit, variable=variable, value="x")
    return unit


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query_params,include_count,include_description",
    [
        pytest.param({}, True, False, id="count only (default)"),
        pytest.param(
            {"accessibility_description": "true"},
            True,
            True,
            id="count and description",
        ),
        pytest.param(
            {"only": "name", "accessibility_description": "true"},
            False,
            True,
            id="description only",
        ),
        pytest.param({"only": "name"}, False, False, id="no count or description"),
    ],
)
def test_get_unit(api_client, unit, query_params, include_count, include_description):
    unit_url = "{}?{}".format(
        reverse("unit-detail", kwargs={"pk": unit.id}), urlencode(query_params)
    )

    response = api_client.get(unit_url)

    assert ("accessibility_shortcoming_count" in response.data) == include_count
    assert ("accessibility_description" in response.data) == include_description


@pytest.fixture
def patch_rules():
    from services.utils import AccessibilityShortcomingCalculator

    # Verify that AccessibilityShortcomingCalculator is singleton
    assert AccessibilityShortcomingCalculator() == AccessibilityShortcomingCalculator()

    def _set_rules(rules, messages):
        AccessibilityShortcomingCalculator().rules = rules
        AccessibilityShortcomingCalculator().messages = messages

    return _set_rules


def create_rule(ruleset):
    """
    Create an accessibility rule.

    Args:
        ruleset (tuple): (operator, message, [list of subrules] or None)
                         each subrule must be a valid ruleset

    Returns:
        accessibility rule suitable for patching
    """
    rule_id = 1

    def _create_rule(op, msg, rules, parent_id):
        nonlocal rule_id
        my_id = rule_id
        rule_id = rule_id + 1
        rule = {
            "id": my_id,
            "requirement_id": parent_id,
            "path": ["outside"],
            "operator": op,
            "msg": msg,
        }
        if isinstance(rules, list):
            rule["operands"] = [_create_rule(*ruleset, my_id) for ruleset in rules]
        else:
            rule["operands"] = [1, "x"]
        return rule

    return _create_rule(*ruleset, rule_id)


@pytest.mark.django_db
def test_calculate_shortcomings_no_properties(unit, patch_rules):
    patch_rules({"1": create_rule(("EQ", 0, None))}, ["message"])

    call_command("calculate_accessibility_shortcomings")

    shortcomings = Unit.objects.get(id=unit.id).accessibility_shortcomings
    assert shortcomings.accessibility_shortcoming_count == {}
    assert shortcomings.accessibility_description == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rules",
    [
        pytest.param({"1": create_rule(("ERR", 0, None))}, id="leaf"),
        pytest.param(
            {"1": create_rule(("ERR", 0, [("EQ", None, None), ("NEQ", None, None)]))},
            id="compound",
        ),
    ],
)
def test_check_invalid_rule(unit_with_props, patch_rules, rules):
    patch_rules(rules, ["message"])

    with pytest.raises(OperatorException) as e:
        call_command("calculate_accessibility_shortcomings")

    assert str(e.value) == "ERR"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rules",
    [
        pytest.param({"1": create_rule(("NEQ", 1, None))}, id="simple"),
        pytest.param(
            {"1": create_rule(("OR", 0, [("NEQ", 1, None)]))}, id="message from leaf"
        ),
        pytest.param(
            {"1": create_rule(("OR", 1, [("NEQ", 2, None)]))}, id="message not found"
        ),
        pytest.param(
            {
                "1": create_rule(
                    ("OR", 1, [("AND", None, [("NEQ", None, None), ("NEQ", 0, None)])])
                )
            },
            id="short circuit AND",
        ),
        pytest.param(
            {
                "1": create_rule(
                    (
                        "AND",
                        None,
                        [
                            ("OR", None, [("EQ", None, None), ("NEQ", 0, None)]),
                            ("NEQ", 1, None),
                        ],
                    )
                )
            },
            id="short circuit OR",
        ),
        pytest.param(
            {
                "1": create_rule(
                    (
                        "AND",
                        None,
                        [
                            ("AND", None, [("EQ", None, None), ("EQ", None, None)]),
                            ("NEQ", 1, None),
                        ],
                    )
                )
            },
            id="AND",
        ),
        pytest.param(
            {"1A": create_rule(("NEQ", 1, None)), "1B": create_rule(("NEQ", 1, None))},
            id="overlapping profiles",
        ),
        pytest.param(
            {"1": create_rule(("NEQ", 1, None)), "2": create_rule(("NEQ", 1, None))},
            id="multiple profiles",
        ),
    ],
)
def test_calculate_shortcomings(unit_with_props, patch_rules, rules):
    patch_rules(rules, ["failure", "success"])

    call_command("calculate_accessibility_shortcomings")

    shortcomings = Unit.objects.get(id=unit_with_props.id).accessibility_shortcomings

    profile_count = len(set([profile[0] for profile in rules.keys()]))
    assert len(shortcomings.accessibility_shortcoming_count) == profile_count
    for count in shortcomings.accessibility_shortcoming_count.values():
        assert count == 1

    assert shortcomings.accessibility_description
    for profile in shortcomings.accessibility_description[0]["profiles"]:
        for shortcoming in profile["shortcomings"]:
            assert shortcoming == "success"
