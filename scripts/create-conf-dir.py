#!/usr/bin/env python3

import sys
import os
from os.path import dirname, abspath

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import confDir


os.makedirs(confDir, mode=0o755, exist_ok=True)
