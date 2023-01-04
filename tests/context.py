"""Handles imports for unit tests"""

import os
import sys

# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hpgl_input.hpgl_input import HpglInput

HpglInput.__module__ = "hpgl_input"
