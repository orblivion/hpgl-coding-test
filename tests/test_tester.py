from test_paths import HPGLVectorTests
from hpgl_input.hpgl_input import HpglInput
import inkex

HPGLVectorTests.__test__ = False


class DummyHPGLConverter(HpglInput):
    """A dummy HPGL converter with provides test data for tests."""

    def parse_document(self, string, layer):
        """Convert a document stored in string to SVG elements."""
        pel = inkex.PathElement()
        layer.append(pel)
        pel.style.update({"stroke": "black", "stroke-width": "1"})

        if string == "IN;SP1;PU0,0;PD2500,0,0,1500,0,0;":
            pel.path = "M 0 0 2500 0 0 1500 0 0"
        if string == "IN; SP1; PU 10,10; PD 10, 30; PU 20, 30 PD 20, 10, 10, 10;":
            pel.path = "M 10 10 L 10 30 M 20 30 L 20 10 L 10 10"


class DummyHPGLConverterWithExtraMoveTos(DummyHPGLConverter):
    """A dummy HPGL converter which adds spurious subpaths."""

    def parse_document(self, string, layer):
        """Convert a document stored in string to SVG elements."""
        pel = inkex.PathElement()
        layer.append(pel)

        pel.style.update({"stroke": "#000000", "stroke-width": "6pt"})

        if string == "IN;SP1;PU0,0;PD2500,0,0,1500,0,0;":
            pel.path = "M 0 0 2500 0 m 10 0 m -10 0 L 0 1500 0 0 m 0 0"
        else:
            # tested this to exhaustion, return the unmodified data
            layer.remove(layer[0])
            super().parse_document(string, layer)


class DummyHGPLConverterSplit(DummyHPGLConverter):
    """A dummy HPGL converter which adds one element per subpath"""

    def parse_document(self, string, layer):
        super().parse_document(string, layer)

        for subpath in HPGLVectorTests.break_apart(layer[0].path):
            pel = inkex.PathElement()
            layer.append(pel)
            pel.style.update({"stroke": "black", "stroke-width": "1"})
            pel.path = subpath

        layer.remove(layer[0])


class DummyHPGLVectorTest(HPGLVectorTests):
    __test__ = True
    effect_class = DummyHPGLConverter


class DummyHPGLVectorTestWithExtraMoveTos(HPGLVectorTests):
    __test__ = True
    effect_class = DummyHPGLConverterWithExtraMoveTos


class DummyHPGLVectorTestSplit(HPGLVectorTests):
    __test__ = True
    effect_class = DummyHGPLConverterSplit
