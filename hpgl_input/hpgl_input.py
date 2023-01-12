#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2022 Jonathan Neuhauser (jonathan.neuhauser@outlook.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""Parser for HP/GL Documents"""

import pyparsing as pp

from inkex.base import SvgOutputMixin
import inkex
from inkex.localization import inkex_gettext as _


class HpglInput(inkex.InputExtension):
    """InputExtension to import HP/GL2 documents."""

    def add_arguments(self, pars):
        pass

    def load(self, stream):
        """Load the document, making sure that we operate on a decoded string"""
        res = stream.read()
        if isinstance(res, str):
            return res
        return res.decode()

    def effect(self):
        # interpret HPGL data

        # Create an 8x11 inch document in mm units.
        doc: inkex.SvgDocumentElement = SvgOutputMixin.get_template(
            width=8 * 25.4,
            height=11 * 25.4,
            unit="mm",
        )

        # Add a root layer that takes care of transforming the HPGL coordinate
        # system to SVG coordinates.
        layer = doc.getroot().add(inkex.Layer())

        plu_to_svg = inkex.Transform(
            scale=(
                0.025,
                -0.025,
            ),
            translate=(0, 11 * 25.4),
        )
        layer.transform = plu_to_svg

        self.parse_document(self.document, layer)

        # deliver document to inkscape
        self.document = doc

    def parse_document(self, string, layer):
        """Convert a document stored in string to SVG elements."""

        # TODO: Add your code here
        # parse the document, which is provided as utf8-decoded string in self.document,
        # i.e. create path elements (inkex.PathElement), set their .path, and .style,
        # and append them to "layer"

        inkex.errormsg("I still have work to do.")


if __name__ == "__main__":
    HpglInput().run()
