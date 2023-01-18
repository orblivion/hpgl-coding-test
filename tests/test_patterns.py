import pyparsing as pp

from tester import HPGLTest
from hpgl_input.hpgl_input import (
    numeric_parameter,
    first_numeric_parameter_pair,
    next_numeric_parameter_pair,
    unpaired_first_numeric_parameter,
    unpaired_next_numeric_parameter,
    numeric_parameter_pair_list,
    cmd_pen_down,
    cmd_pen_up,
    cmd_polyline_encoded,
    cmd_symbol_mode,
    cmd_define_label_terminator,
    cmd_label,
    cmd_other,
)

class HPGLPatternsTest(HPGLTest):
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
            self.fail("expected ParseException")


class HPGLNumericParameterTests(HPGLPatternsTest):
    """Test the HPGL command parameter list related parsing patterns"""

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


class HPGLCommandTests(HPGLPatternsTest):
    """
    Test the HPGL command parsing patterns

    In some cases the input string includes the beginning of a next command.
    This is to confirm that the given parser doesn't parse too much.

    """

    def test_cmd_pen_up(self):
        self.assert_parse_result(cmd_pen_up, "PU ", ["PU"])
        self.assert_parse_result(cmd_pen_up, "PU12XY", ["PU", "12"])
        self.assert_parse_result(cmd_pen_up, "PU12; XY", ["PU", "12", ";"])
        self.assert_parse_result(cmd_pen_up, "PU12,13XY", ["PU", ["12", ",", "13"]])
        self.assert_parse_result(
            cmd_pen_up, "PU12,13; XY", ["PU", ["12", ",", "13"], ";"]
        )
        self.assert_parse_result(
            cmd_pen_up, "PU12,13 14XY", ["PU", ["12", ",", "13"], "14"]
        )

        self.assert_parse_failure(cmd_pen_up, "PU12,;")

    def test_cmd_pen_down(self):
        self.assert_parse_result(cmd_pen_down, "PD ", ["PD"])
        self.assert_parse_result(cmd_pen_down, "PD12XY", ["PD", "12"])
        self.assert_parse_result(cmd_pen_down, "PD12; XY", ["PD", "12", ";"])
        self.assert_parse_result(cmd_pen_down, "PD12,13XY", ["PD", ["12", ",", "13"]])
        self.assert_parse_result(
            cmd_pen_down, "PD12,13; XY", ["PD", ["12", ",", "13"], ";"]
        )
        self.assert_parse_result(
            cmd_pen_down, "PD12,13 14XY", ["PD", ["12", ",", "13"], "14"]
        )

        self.assert_parse_failure(cmd_pen_down, "PD12,;")

    def test_cmd_other(self):
        # Note that for these, we don't care about parameter pairings, so all
        # resulting lists come out flat.
        self.assert_parse_result(cmd_other, "XY ", ["XY"])
        self.assert_parse_result(cmd_other, "XY12ZW", ["XY", "12"])
        self.assert_parse_result(cmd_other, "XY12; ZW", ["XY", "12", ";"])
        self.assert_parse_result(cmd_other, "XY12,13 ZW", ["XY", "12", ",", "13"])
        self.assert_parse_result(cmd_other, "XY12,13; ZW", ["XY", "12", ",", "13", ";"])
        self.assert_parse_result(
            cmd_other, "XY12,13 14 ZW", ["XY", "12", ",", "13", "14"]
        )

        # We also don't much care about numeric separators being out of order
        self.assert_parse_result(
            cmd_other,
            "XY, ,12 ,,",
            [
                "XY",
                ",",
                ",",
                "12",
                ",",
                ",",
            ],
        )

    def test_cmd_polyline_encoded(self):
        self.assert_parse_result(
            cmd_polyline_encoded,
            "PE 123 #AB; XY",
            ["PE", "1", "2", "3", "#", "A", "B", ";"],
        )
        self.assert_parse_failure(
            cmd_polyline_encoded,
            "PE 123 #AB",
        )

    def test_cmd_symbol_mode(self):
        # character and semicolon
        self.assert_parse_result(cmd_symbol_mode, "SM c ; XY", ["SM", "c", ";"])

        # character only
        self.assert_parse_result(cmd_symbol_mode, "SM c XY", ["SM", "c"])

        # semicolon only
        self.assert_parse_result(cmd_symbol_mode, "SM; XY", ["SM", ";"])

        # No char, no semicolon (invalid input, bad result)
        self.assert_parse_result(cmd_symbol_mode, "SM XY", ["SM", "X"])

    def test_define_label_terminator(self):
        # Abort command
        self.assert_parse_result(cmd_define_label_terminator, "DT;XY", ["DT", ";"])

        # Set label terminator to &
        self.assert_parse_result(
            cmd_define_label_terminator, "DT&;XY", ["DT", "&", ";"]
        )
        self.assert_parse_result(cmd_define_label_terminator, "DT&XY", ["DT", "&"])

        # Set label terminator to & and set mode
        self.assert_parse_result(
            cmd_define_label_terminator, "DT&,0;XY", ["DT", "&", ",", "0", ";"]
        )
        self.assert_parse_result(
            cmd_define_label_terminator, "DT& 0;XY", ["DT", "&", "0", ";"]
        )
        self.assert_parse_result(
            cmd_define_label_terminator, "DT& 0XY", ["DT", "&", "0"]
        )

        # No whitespace allowed before the label terminator. This parses the wrong thing.
        self.assert_parse_result(cmd_define_label_terminator, "DT &;", ["DT", " "])

    def test_label(self):
        self.assert_parse_result(cmd_label("&"), "LB a b c &XY", ["LB", " a b c ", "&"])
        self.assert_parse_result(
            cmd_label("&"), "LB a b c & XY", ["LB", " a b c ", "&"]
        )
        self.assert_parse_result(
            cmd_label("&"), "LB a b c & ; XY", ["LB", " a b c ", "&", ";"]
        )
