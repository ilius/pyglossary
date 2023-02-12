#!/usr/bin/env python3

import os
import sys
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import confDir

os.makedirs(confDir, mode=0o755, exist_ok=True)
