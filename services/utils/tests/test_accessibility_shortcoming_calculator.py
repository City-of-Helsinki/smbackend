"""
Tests for the AccessibilityShortcomingCalculator module.

This module tests:
- Singleton pattern behavior
- OperatorError exception
- Rule evaluation logic (EQ, NEQ, AND, OR)
- Shortcoming calculation and recording
- Message aggregation
- Profile ID and path title handling
"""

from unittest.mock import Mock, patch

import pytest

from services.utils.accessibility_shortcoming_calculator import (
    PATH_TITLES,
    PROFILE_IDS,
    AccessibilityShortcomingCalculator,
    OperatorError,
    Singleton,
)


class TestOperatorError:
    """Test the OperatorError exception class."""

    def test_operator_error_message(self):
        """Test that OperatorError creates the correct error message."""
        error = OperatorError("INVALID_OP")
        assert error.message == "Invalid operator INVALID_OP"

    def test_operator_error_with_various_operators(self):
        """Test OperatorError with different operator strings."""
        operators = ["XOR", "NOT", "IMPLIES", "123", ""]
        for op in operators:
            error = OperatorError(op)
            assert error.message == f"Invalid operator {op}"


class TestSingleton:
    """Test the Singleton metaclass."""

    def test_singleton_creates_single_instance(self):
        """Test that Singleton metaclass ensures only one instance exists."""
        # Clear any existing instance
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        instance1 = AccessibilityShortcomingCalculator()
        instance2 = AccessibilityShortcomingCalculator()

        assert instance1 is instance2

    def test_singleton_with_multiple_classes(self):
        """Test that Singleton works correctly with multiple classes."""

        class TestClass1(metaclass=Singleton):
            pass

        class TestClass2(metaclass=Singleton):
            pass

        t1_a = TestClass1()
        t1_b = TestClass1()
        t2_a = TestClass2()
        t2_b = TestClass2()

        assert t1_a is t1_b
        assert t2_a is t2_b
        assert t1_a is not t2_a


class TestAccessibilityShortcomingCalculatorInit:
    """Test initialization of AccessibilityShortcomingCalculator."""

    @patch("services.utils.accessibility_shortcoming_calculator.RULES")
    def test_init_success(self, mock_rules):
        """Test successful initialization with valid rules."""
        mock_rules.get_data.return_value = (
            {"1": {"id": 1, "operator": "EQ"}},
            ["message1", "message2"],
        )

        # Clear singleton instance
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        calculator = AccessibilityShortcomingCalculator()

        assert calculator.rules == {"1": {"id": 1, "operator": "EQ"}}
        assert calculator.messages == ["message1", "message2"]

    @patch("services.utils.accessibility_shortcoming_calculator.RULES")
    @patch("services.utils.accessibility_shortcoming_calculator.logger")
    def test_init_file_not_found(self, mock_logger, mock_rules):
        """Test initialization when rules file is not found."""
        mock_rules.get_data.side_effect = FileNotFoundError("Rules file not found")

        # Clear singleton instance
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        calculator = AccessibilityShortcomingCalculator()

        assert calculator.rules == {}
        assert calculator.messages == []
        mock_logger.error.assert_called_once()


class TestAccessibilityShortcomingCalculatorCalculate:
    """Test the calculate method."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance with mocked rules."""
        # Clear singleton instance
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        with patch(
            "services.utils.accessibility_shortcoming_calculator.RULES"
        ) as mock_rules:
            mock_rules.get_data.return_value = ({}, [])
            calc = AccessibilityShortcomingCalculator()
        return calc

    @pytest.fixture
    def mock_unit(self):
        """Create a mock unit with accessibility properties."""
        unit = Mock()
        prop1 = Mock()
        prop1.variable.id = 1
        prop1.value = "yes"

        prop2 = Mock()
        prop2.variable.id = 2
        prop2.value = "no"

        unit.accessibility_properties.all.return_value = [prop1, prop2]
        return unit

    def test_calculate_no_rules(self, calculator, mock_unit):
        """Test calculate with no rules configured."""
        calculator.rules = {}
        calculator.messages = []

        result, counts = calculator.calculate(mock_unit)

        assert result == []
        assert counts == {}

    def test_calculate_no_properties(self, calculator):
        """Test calculate with a unit that has no properties."""
        unit = Mock()
        unit.accessibility_properties.all.return_value = []

        calculator.rules = {
            "1": {
                "id": 1,
                "requirement_id": 1,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "yes"],
                "msg": 0,
            }
        }
        calculator.messages = ["Test message"]

        result, counts = calculator.calculate(unit)

        # No properties means everything passes
        assert result == []
        assert counts == {}

    def test_calculate_with_matching_rule(self, calculator, mock_unit):
        """Test calculate with a rule that matches (passes)."""
        calculator.rules = {
            "1": {
                "id": 1,
                "requirement_id": 1,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "yes"],
                "msg": 0,
            }
        }
        calculator.messages = ["Test message"]

        result, counts = calculator.calculate(mock_unit)

        assert result == []
        assert counts == {}

    def test_calculate_with_failing_rule(self, calculator, mock_unit):
        """Test calculate with a rule that fails and generates a shortcoming."""
        calculator.rules = {
            "1": {
                "id": 1,
                "requirement_id": 1,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "no"],
                "msg": 0,
            }
        }
        calculator.messages = ["Access problem"]

        result, counts = calculator.calculate(mock_unit)

        assert len(result) == 1
        assert result[0]["title"] == PATH_TITLES["entrance"]
        assert len(result[0]["profiles"]) == 1
        assert result[0]["profiles"][0]["id"] == "wheelchair"
        assert "Access problem" in result[0]["profiles"][0]["shortcomings"]
        assert counts == {"wheelchair": 1}

    def test_calculate_multiple_profiles(self, calculator, mock_unit):
        """Test calculate with multiple accessibility profiles."""
        calculator.rules = {
            "1": {
                "id": 1,
                "requirement_id": 1,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "no"],
                "msg": 0,
            },
            "2": {
                "id": 2,
                "requirement_id": 2,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [2, "yes"],
                "msg": 1,
            },
        }
        calculator.messages = ["Wheelchair problem", "Mobility problem"]

        result, counts = calculator.calculate(mock_unit)

        assert len(result) == 1
        assert len(result[0]["profiles"]) == 2
        assert counts["wheelchair"] == 1
        assert counts["reduced_mobility"] == 1

    def test_calculate_multiple_paths(self, calculator, mock_unit):
        """Test calculate with shortcomings in multiple paths."""
        calculator.rules = {
            "1": {
                "id": 1,
                "requirement_id": 1,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "no"],
                "msg": 0,
            },
            "1A": {
                "id": 2,
                "requirement_id": 2,
                "path": ["interior"],
                "operator": "EQ",
                "operands": [1, "no"],
                "msg": 1,
            },
        }
        calculator.messages = ["Entrance problem", "Interior problem"]

        result, counts = calculator.calculate(mock_unit)

        assert len(result) == 2
        path_titles = [r["title"] for r in result]
        assert PATH_TITLES["entrance"] in path_titles
        assert PATH_TITLES["interior"] in path_titles


class TestCalculateShortcomingsLeafRules:
    """Test _calculate_shortcomings method with leaf (simple) rules."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        with patch(
            "services.utils.accessibility_shortcoming_calculator.RULES"
        ) as mock_rules:
            mock_rules.get_data.return_value = ({}, ["Test message"])
            calc = AccessibilityShortcomingCalculator()
        return calc

    def test_leaf_rule_eq_pass(self, calculator):
        """Test leaf rule with EQ operator that passes."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [1, "yes"],
            "msg": 0,
        }
        properties = {1: "yes"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True
        assert message_recorded is False

    def test_leaf_rule_eq_fail(self, calculator):
        """Test leaf rule with EQ operator that fails."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [1, "yes"],
            "msg": 0,
        }
        properties = {1: "no"}
        messages = {}

        # Initialize shortcomings as calculate() would do
        calculator.shortcomings = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is False
        assert message_recorded is True

    def test_leaf_rule_neq_pass(self, calculator):
        """Test leaf rule with NEQ operator that passes."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "NEQ",
            "operands": [1, "no"],
            "msg": 0,
        }
        properties = {1: "yes"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True
        assert message_recorded is False

    def test_leaf_rule_neq_fail(self, calculator):
        """Test leaf rule with NEQ operator that fails."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "NEQ",
            "operands": [1, "no"],
            "msg": 0,
        }
        properties = {1: "no"}
        messages = {}

        # Initialize shortcomings as calculate() would do
        calculator.shortcomings = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is False
        assert message_recorded is True

    def test_leaf_rule_missing_property(self, calculator):
        """Test leaf rule when property is not supplied."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [999, "yes"],
            "msg": 0,
        }
        properties = {1: "yes"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        # Missing properties should pass (pretend everything is fine)
        assert is_ok is True
        assert message_recorded is False

    def test_leaf_rule_invalid_operator(self, calculator):
        """Test leaf rule with invalid operator raises OperatorError."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "INVALID",
            "operands": [1, "yes"],
            "msg": 0,
        }
        properties = {1: "yes"}
        messages = {}

        with pytest.raises(OperatorError) as exc_info:
            calculator._calculate_shortcomings(rule, properties, messages, 1)

        assert "INVALID" in str(exc_info.value.message)


class TestCalculateShortcomingsCompoundRules:
    """Test _calculate_shortcomings method with compound (AND/OR) rules."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        with patch(
            "services.utils.accessibility_shortcoming_calculator.RULES"
        ) as mock_rules:
            mock_rules.get_data.return_value = ({}, ["Test message"])
            calc = AccessibilityShortcomingCalculator()
        return calc

    def test_and_rule_all_pass(self, calculator):
        """Test AND rule where all sub-rules pass."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "AND",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "yes", 2: "ok"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True
        assert message_recorded is False

    def test_and_rule_one_fails(self, calculator):
        """Test AND rule where one sub-rule fails."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "AND",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "no", 2: "ok"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is False
        # No message recorded because of short circuit
        assert message_recorded is False

    def test_and_rule_all_fail(self, calculator):
        """Test AND rule where all sub-rules fail."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "AND",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": 0,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": 0,
                },
            ],
            "msg": None,
        }
        properties = {1: "no", 2: "fail"}
        messages = {}

        # Initialize shortcomings as calculate() would do
        calculator.shortcomings = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is False
        # AND short circuits after first failing subrule that records a message,
        # so the compound rule itself doesn't record a message
        assert message_recorded is False

    def test_or_rule_all_pass(self, calculator):
        """Test OR rule where all sub-rules pass."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "OR",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "yes", 2: "ok"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        # OR short circuits on first pass
        assert is_ok is True
        assert message_recorded is False

    def test_or_rule_one_passes(self, calculator):
        """Test OR rule where one sub-rule passes."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "OR",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "no", 2: "ok"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True
        assert message_recorded is False

    def test_or_rule_all_fail(self, calculator):
        """Test OR rule where all sub-rules fail."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "OR",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                },
                {
                    "id": 3,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [2, "ok"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "no", 2: "fail"}
        messages = {}

        # Initialize shortcomings as calculate() would do
        calculator.shortcomings = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is False
        assert message_recorded is True

    def test_compound_rule_invalid_operator(self, calculator):
        """Test compound rule with invalid operator raises OperatorError."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "XOR",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [1, "yes"],
                    "msg": None,
                }
            ],
            "msg": 0,
        }
        properties = {1: "yes"}
        messages = {}

        with pytest.raises(OperatorError) as exc_info:
            calculator._calculate_shortcomings(rule, properties, messages, 1)

        assert "XOR" in str(exc_info.value.message)

    def test_nested_compound_rules(self, calculator):
        """Test nested compound rules (AND within OR)."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "OR",
            "operands": [
                {
                    "id": 2,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "AND",
                    "operands": [
                        {
                            "id": 3,
                            "requirement_id": 1,
                            "path": ["entrance"],
                            "operator": "EQ",
                            "operands": [1, "yes"],
                            "msg": None,
                        },
                        {
                            "id": 4,
                            "requirement_id": 1,
                            "path": ["entrance"],
                            "operator": "EQ",
                            "operands": [2, "ok"],
                            "msg": None,
                        },
                    ],
                    "msg": None,
                },
                {
                    "id": 5,
                    "requirement_id": 1,
                    "path": ["entrance"],
                    "operator": "EQ",
                    "operands": [3, "good"],
                    "msg": None,
                },
            ],
            "msg": 0,
        }
        properties = {1: "yes", 2: "ok", 3: "bad"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        # Inner AND passes, so OR passes (short circuits)
        assert is_ok is True
        assert message_recorded is False


class TestRecordShortcoming:
    """Test the _record_shortcoming method."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        with patch(
            "services.utils.accessibility_shortcoming_calculator.RULES"
        ) as mock_rules:
            mock_rules.get_data.return_value = (
                {},
                ["Message 1", "Message 2", "Message 3"],
            )
            calc = AccessibilityShortcomingCalculator()
        calc.shortcomings = {}
        return calc

    def test_record_shortcoming_valid_message(self, calculator):
        """Test recording a shortcoming with a valid message index."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        messages = {}

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is True
        assert 1 in calculator.shortcomings
        assert "entrance" in calculator.shortcomings[1]
        assert 0 in calculator.shortcomings[1]["entrance"]

    def test_record_shortcoming_none_message(self, calculator):
        """Test recording a shortcoming with None message index."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": None}
        messages = {}

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is False
        assert calculator.shortcomings == {}

    def test_record_shortcoming_out_of_range_message(self, calculator):
        """Test recording a shortcoming with message index out of range."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 999}
        messages = {}

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is False
        assert calculator.shortcomings == {}

    def test_record_shortcoming_top_level_requirement_empty_messages(self, calculator):
        """Test recording a top-level requirement when no specific messages exist."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        messages = {}

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is True
        assert messages["entrance"][1] == [0]

    def test_record_shortcoming_top_level_requirement_existing_messages(
        self, calculator
    ):
        """Test recording a top-level requirement when specific messages already exist."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        messages = {
            "entrance": {
                1: [1]  # Already has specific message
            }
        }

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is True
        # Top level message should not be added since specific messages exist
        assert 0 not in messages["entrance"][1]
        assert messages["entrance"][1] == [1]

    def test_record_shortcoming_specific_requirement(self, calculator):
        """Test recording a specific (non-top-level) requirement."""
        rule = {"id": 2, "requirement_id": 1, "path": ["entrance"], "msg": 1}
        messages = {}

        result = calculator._record_shortcoming(rule, messages, 1)

        assert result is True
        assert messages["entrance"][1] == [1]

    def test_record_shortcoming_multiple_profiles(self, calculator):
        """Test recording shortcomings for multiple profiles."""
        # Use different rules for different profiles to test multiple profile recording
        rule1 = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        rule2 = {"id": 2, "requirement_id": 2, "path": ["entrance"], "msg": 0}
        messages = {}

        calculator._record_shortcoming(rule1, messages, 1)
        # Verify first profile is recorded
        assert 1 in calculator.shortcomings
        assert "entrance" in calculator.shortcomings[1]

        calculator._record_shortcoming(rule2, messages, 2)
        # Both profiles should now be present
        assert 1 in calculator.shortcomings
        assert 2 in calculator.shortcomings
        assert "entrance" in calculator.shortcomings[1]
        assert "entrance" in calculator.shortcomings[2]

    def test_record_shortcoming_multiple_segments(self, calculator):
        """Test recording shortcomings for multiple path segments."""
        rule1 = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        rule2 = {"id": 2, "requirement_id": 2, "path": ["interior"], "msg": 1}
        messages = {}

        calculator._record_shortcoming(rule1, messages, 1)
        calculator._record_shortcoming(rule2, messages, 1)

        assert "entrance" in calculator.shortcomings[1]
        assert "interior" in calculator.shortcomings[1]

    def test_record_shortcoming_duplicate_messages(self, calculator):
        """Test that duplicate messages are handled correctly (using sets)."""
        rule = {"id": 1, "requirement_id": 1, "path": ["entrance"], "msg": 0}
        messages = {}

        calculator._record_shortcoming(rule, messages, 1)
        calculator._record_shortcoming(rule, messages, 1)

        # Should only record once due to set usage
        assert len(calculator.shortcomings[1]["entrance"]) == 1
        assert 0 in calculator.shortcomings[1]["entrance"]


class TestProfileIDsAndPathTitles:
    """Test the PROFILE_IDS and PATH_TITLES constants."""

    def test_profile_ids_structure(self):
        """Test that PROFILE_IDS has expected structure."""
        assert isinstance(PROFILE_IDS, dict)
        assert len(PROFILE_IDS) == 6
        assert PROFILE_IDS[1] == "wheelchair"
        assert PROFILE_IDS[2] == "reduced_mobility"
        assert PROFILE_IDS[3] == "rollator"
        assert PROFILE_IDS[4] == "stroller"
        assert PROFILE_IDS[5] == "visually_impaired"
        assert PROFILE_IDS[6] == "hearing_aid"

    def test_path_titles_structure(self):
        """Test that PATH_TITLES has expected structure."""
        assert isinstance(PATH_TITLES, dict)

        expected_paths = [
            "outside",
            "parking_hall",
            "route_to_entrance",
            "entrance",
            "interior",
            "outdoor_sport_facility",
            "route_to_outdoor_sport_facility",
            "service_point",
            "playground",
            "restaurant",
            "nature_site",
        ]

        for path in expected_paths:
            assert path in PATH_TITLES
            assert "fi" in PATH_TITLES[path]
            assert "sv" in PATH_TITLES[path]
            assert "en" in PATH_TITLES[path]

    def test_path_titles_translations(self):
        """Test that PATH_TITLES have all three language translations."""
        for _path, translations in PATH_TITLES.items():
            assert isinstance(translations, dict)
            assert len(translations) == 3
            assert all(lang in translations for lang in ["fi", "sv", "en"])
            assert all(
                isinstance(translations[lang], str) for lang in ["fi", "sv", "en"]
            )
            assert all(len(translations[lang]) > 0 for lang in ["fi", "sv", "en"])


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        if AccessibilityShortcomingCalculator in Singleton._instances:
            del Singleton._instances[AccessibilityShortcomingCalculator]

        with patch(
            "services.utils.accessibility_shortcoming_calculator.RULES"
        ) as mock_rules:
            mock_rules.get_data.return_value = ({}, ["Message"])
            calc = AccessibilityShortcomingCalculator()
        return calc

    def test_empty_properties(self, calculator):
        """Test with empty properties dictionary."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [1, "yes"],
            "msg": 0,
        }
        properties = {}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        # Missing property should pass
        assert is_ok is True

    def test_property_value_none(self, calculator):
        """Test with property value that is None."""
        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [1, None],
            "msg": 0,
        }
        properties = {1: None}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True

    def test_large_rule_tree(self, calculator):
        """Test with deeply nested rule structure."""
        # Create a deep nested structure
        innermost = {
            "id": 4,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "EQ",
            "operands": [1, "yes"],
            "msg": None,
        }

        level3 = {
            "id": 3,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "AND",
            "operands": [innermost],
            "msg": None,
        }

        level2 = {
            "id": 2,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "OR",
            "operands": [level3],
            "msg": None,
        }

        rule = {
            "id": 1,
            "requirement_id": 1,
            "path": ["entrance"],
            "operator": "AND",
            "operands": [level2],
            "msg": 0,
        }

        properties = {1: "yes"}
        messages = {}

        is_ok, message_recorded = calculator._calculate_shortcomings(
            rule, properties, messages, 1
        )

        assert is_ok is True

    def test_calculate_with_all_profiles(self, calculator):
        """Test calculate with rules for all six profiles."""
        unit = Mock()
        prop = Mock()
        prop.variable.id = 1
        prop.value = "no"
        unit.accessibility_properties.all.return_value = [prop]

        calculator.rules = {}
        calculator.messages = ["Problem"]

        for profile_id in PROFILE_IDS.keys():
            calculator.rules[str(profile_id)] = {
                "id": profile_id,
                "requirement_id": profile_id,
                "path": ["entrance"],
                "operator": "EQ",
                "operands": [1, "yes"],
                "msg": 0,
            }

        result, counts = calculator.calculate(unit)

        # All profiles should have shortcomings
        assert len(counts) == 6
        for profile_name in PROFILE_IDS.values():
            assert profile_name in counts
            assert counts[profile_name] == 1

    def test_calculate_with_all_path_types(self, calculator):
        """Test calculate with shortcomings in all path types."""
        unit = Mock()
        prop = Mock()
        prop.variable.id = 1
        prop.value = "no"
        unit.accessibility_properties.all.return_value = [prop]

        calculator.rules = {}
        calculator.messages = ["Problem"]

        for idx, path_name in enumerate(PATH_TITLES.keys()):
            calculator.rules[f"1{chr(65 + idx)}"] = {
                "id": idx + 1,
                "requirement_id": idx + 1,
                "path": [path_name],
                "operator": "EQ",
                "operands": [1, "yes"],
                "msg": 0,
            }

        result, counts = calculator.calculate(unit)

        # Should have shortcomings for all paths
        assert len(result) == len(PATH_TITLES)
        path_titles = [r["title"] for r in result]
        for path_name in PATH_TITLES.keys():
            assert PATH_TITLES[path_name] in path_titles
