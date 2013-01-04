from os.path import realpath, dirname, join, isdir
import sys

srcDir = ''
if __file__:
    srcDir = dirname(realpath(__file__))
if not srcDir:
    srcDir = '/usr/share/pyglossary'
if not isdir(srcDir):
    srcDir = rootDir = dirname(sys.executable)
else:
    rootDir = dirname(srcDir)




