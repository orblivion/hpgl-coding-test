import context
import io

import inkex
from inkex.tester import TestCase, ComparisonMixin

from hpgl_input.hpgl_input import HpglInput
from typing import List


class HPGLTest(TestCase):
    """Base class for HPGL tests"""

    effect_class = HpglInput

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def import_string(self, string, *args) -> inkex.SvgDocumentElement:
        """Runs a string through an import extension, with optional arguments
        provided as "--arg=value" arguments"""
        stream = io.BytesIO(string.encode())
        reader = self.effect_class()
        out = io.BytesIO()
        reader.parse_arguments([*args])
        reader.options.input_file = stream
        reader.options.output = out
        reader.load_raw()
        reader.save_raw(reader.effect())
        out.seek(0)
        decoded = out.read().decode("utf-8")
        document = inkex.load_svg(decoded)
        return document

    def run_to_layer(self, string) -> inkex.Layer:
        """Runs the HPGL string, returns the first layer"""
        doc = self.import_string(string)
        layers = doc.getroot().xpath("//svg:g[@inkscape:groupmode='layer']")
        return (layers or [None])[0]

    @staticmethod
    def break_apart(path) -> List[inkex.Path]:
        """Breaks apart a path into its subpaths"""
        result = [inkex.Path()]
        current = result[0]

        for cmnd in path.proxy_iterator():
            if cmnd.letter.lower() == "m":
                current = inkex.Path()
                result.append(current)
                current.append(inkex.paths.Move(*cmnd.end_point))
            else:
                current.append(cmnd.command)
        # Remove all subpaths that are empty or only contain move commands
        return [
            i
            for i in result
            if len(i) != 0 and not all(j.letter.lower() == "m" for j in i)
        ]

    def get_equivalent_path(self, layer: inkex.Layer) -> inkex.Path:
        """Join all paths of the layer (only outline is relevant),
        then remove noop movetos"""
        # Combine all paths in the layer.
        joined = inkex.Path()
        for path in layer:
            joined.append(path.path)
        joined = joined.to_relative()
        # Then remove zero-length subpaths
        joined2 = inkex.Path()
        for path in self.break_apart(joined):
            joined2.append(path)

        result = inkex.Path()
        index = -1
        for command in joined2.to_relative():
            index += 1
            if (
                index != 0
                and command.letter == "m"
                and command.args[0] == 0
                and command.args[1] == 0
            ):
                continue
            result.append(command)
        return result.to_absolute()

    def assert_resulting_path(self, string, comparison) -> inkex.Path:
        """Runs a document and cleans the output for comparison"""
        result = self.run_to_layer(string)
        self.assertEqual(
            self.get_equivalent_path(result).to_superpath(),
            inkex.Path(comparison).to_absolute().to_superpath(),
            "The effective path data is different",
        )

        self.assertEqual(
            result[0].specified_style()("stroke"),
            inkex.Color("black"),
            "The stroke color must be black",
        )

        self.assertEqual(
            result[0].specified_style()("fill"),
            None,
            "The fill must be 'none'",
        )
        self.assertGreater(
            result.to_dimensionless(result[0].specified_style()("stroke-width")),
            0,
            "The stroke width has to be greater than 0",
        )
