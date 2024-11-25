#!/usr/bin/env -S python3 -O

import sys
from os.path import dirname

sys.path.insert(0, dirname(__file__))

from pyglossary.ui.main import main

main()
