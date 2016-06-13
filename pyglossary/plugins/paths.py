from os.path import realpath, dirname, join, isdir
import sys

if hasattr(sys, 'frozen'):
    rootDir = dirname(sys.executable)
else:
    rootDir = dirname(dirname(realpath(__file__)))
