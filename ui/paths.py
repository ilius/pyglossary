from os.path import realpath, dirname, join, isdir
import sys

srcDir = ''
if __file__:
    srcDir = dirname(realpath(__file__))
    rootDir = dirname(srcDir)
else:
    #rootDir = '/usr/share/pyglossary'
    rootDir = dirname(sys.executable)
    srcDir = join(rootDir, 'ui')



