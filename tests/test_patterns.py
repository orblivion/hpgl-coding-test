import pyparsing as pp

from hpgl_input.hpgl_input import (
    numeric_parameter,
    first_numeric_parameter_pair,
    next_numeric_parameter_pair,
    unpaired_first_numeric_parameter,
    unpaired_next_numeric_parameter,
    numeric_parameter_pair_list,
)
from tester import HPGLTest


class HPGLNumericParameterTests(HPGLTest):
    """Test the HPGL command parameter list related parsing patterns"""

    def assert_parse_result(self, parser, input_string, expected_match_list):
        # Turn ParseResults into a list for simpler comparison
        result = list(parser.parse_string(input_string))
        # If we have nested ParseResults, turn them into nested lists (only one level deep)
        result = [
            list(item) if isinstance(item, pp.ParseResults) else item for item in result
        ]
        self.assertEqual(result, expected_match_list)

    def assert_parse_failure(self, parser, input_string):
        try:
            parser.parse_string(input_string)
        except pp.ParseException:
            pass
        else:
            self.fail("expected parse failure")

    def test_numeric_parameter(self):
        self.assert_parse_result(numeric_parameter, "12", ["12"])
        self.assert_parse_result(numeric_parameter, "12.5", ["12.5"])
        self.assert_parse_result(
            numeric_parameter, "12.5.7", ["12.5"]
        )  # though this wouldn't be valid

        self.assert_parse_failure(numeric_parameter, ".1")

    def test_first_numeric_parameter_pair(self):
        self.assert_parse_result(first_numeric_parameter_pair, "12 13", ["12", "13"])
        self.assert_parse_result(
            first_numeric_parameter_pair, "12, 13,", ["12", ",", "13"]
        )

        self.assert_parse_failure(first_numeric_parameter_pair, ", 12, 13,")

    def test_next_numeric_parameter_pair(self):
        self.assert_parse_result(next_numeric_parameter_pair, "12 13", ["12", "13"])
        self.assert_parse_result(
            next_numeric_parameter_pair, ", 12, 13,", [",", "12", ",", "13"]
        )

    def test_unpaired_first_numeric_parameter(self):
        self.assert_parse_result(unpaired_first_numeric_parameter, "12", ["12"])
        self.assert_parse_failure(unpaired_first_numeric_parameter, ", 12")

    def test_unpaired_next_numeric_parameter(self):
        self.assert_parse_result(unpaired_next_numeric_parameter, ", 12", [",", "12"])

    def test_numeric_parameter_pair_list(self):
        # The expected format is [[paired parameters], unpaired parameters].
        # One or the other or neither may be present:
        # [[paired parameters]]
        # [unpaired parameter]
        # []
        self.assert_parse_result(numeric_parameter_pair_list, "", [])
        self.assert_parse_result(
            numeric_parameter_pair_list, "12", ["12"]  # single list means unpaired
        )
        self.assert_parse_result(
            numeric_parameter_pair_list,
            "12 13",
            [["12", "13"]],  # nested list means paired
        )
        self.assert_parse_result(
            numeric_parameter_pair_list,
            "12 13 14",
            [["12", "13"], "14"],  # both paired and unpaired
        )
        self.assert_parse_result(
            numeric_parameter_pair_list, "12 13 14 15", [["12", "13", "14", "15"]]
        )
        self.assert_parse_result(
            numeric_parameter_pair_list,
            "12 13 14 15 16",
            [["12", "13", "14", "15"], "16"],
        )

        self.assert_parse_result(
            numeric_parameter_pair_list, "12, 13", [["12", ",", "13"]]
        )
        self.assert_parse_result(
            numeric_parameter_pair_list, "12, 13, 14", [["12", ",", "13"], ",", "14"]
        )
        self.assert_parse_result(
            numeric_parameter_pair_list,
            "12, 13, 14, 15",
            [["12", ",", "13", ",", "14", ",", "15"]],
        )
        self.assert_parse_result(
            numeric_parameter_pair_list,
            "12, 13, 14, 15, 16",
            [["12", ",", "13", ",", "14", ",", "15"], ",", "16"],
        )

        self.assert_parse_failure(numeric_parameter_pair_list, ", 12")
        self.assert_parse_failure(numeric_parameter_pair_list, ", 12, ;")
        self.assert_parse_failure(numeric_parameter_pair_list, "12, , 13")
