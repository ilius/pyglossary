import sys
from os.path import dirname, realpath

if hasattr(sys, 'frozen'):
	rootDir = dirname(sys.executable)
else:
	rootDir = dirname(dirname(realpath(__file__)))
