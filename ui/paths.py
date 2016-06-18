from os.path import realpath, dirname, join, isdir
import sys

uiDir = ''

if hasattr(sys, 'frozen'):
    rootDir = dirname(sys.executable)
    uiDir = join(rootDir, 'ui')
else:
    uiDir = dirname(realpath(__file__))
    rootDir = dirname(uiDir)

resDir = join(rootDir, 'res')
