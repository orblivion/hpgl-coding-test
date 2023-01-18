import pyparsing as pp

from tester import HPGLTest
from hpgl_input.hpgl_input import parse_hp_gl, HPGLParseException


class HPGLParserTest(HPGLTest):
    def assert_parse_failure(self, parse_result_iterator, expected_message):
        try:
            list(parse_result_iterator)
        except HPGLParseException as e:
            self.assertEqual(e.args[0], expected_message)
        else:
            self.fail("expected HPGLParseException")

    def test_parse_hp_gl_success(self):
        commands = parse_hp_gl(
            """
        DT&
        PU12
        PD12,13
        LBa-label&
        DT_
        XY12,13,432,2 234
        LBa-label_
        PE a b # c;
        SM c
        PD14
        PU15,16 17 18;
        """
        )
        self.assertEqual(
            list(commands),
            [
                ("PU", []),
                ("PD", [(12, 13)]),
                ("PD", []),
                ("PU", [(15, 16), (17, 18)]),
            ],
        )

    def test_parse_hp_gl_bad_file(self):
        commands = parse_hp_gl("...")
        self.assert_parse_failure(
            commands, "Failed to parse from this part of the document"
        )

    def test_parse_hp_gl_bad_start(self):
        commands = parse_hp_gl("...PD0,0,10,10;")
        self.assert_parse_failure(
            commands, "Parsing did not begin at the expected place in the document"
        )

    def test_parse_hp_gl_empty_file(self):
        commands = parse_hp_gl("  \n\t")
        self.assert_parse_failure(commands, "Empty file")

    def test_parse_hp_gl_missing_semicolon(self):
        commands = parse_hp_gl(
            """
        PU15,16 17 18
        """
        )
        self.assert_parse_failure(commands, "File did not end with a semicolon")
