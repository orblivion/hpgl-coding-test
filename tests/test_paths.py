from tester import HPGLTest

import inkex


class HPGLVectorTests(HPGLTest):
    """Test the vector group of HPGL"""

    def test_simple_lines(self):
        self.assert_resulting_path(
            "IN;SP1;PU0,0;PD2500,0,0,1500,0,0;", "M 0 0 2500 0 0 1500 0 0"
        )
        self.assert_resulting_path(
            "IN; SP1; PU 10,10; PD 10, 30; PU 20, 30 PD 20, 10, 10, 10;",
            "M 10 10 L 10 30 M 20 30 L 20 10 L 10 10",
        )
