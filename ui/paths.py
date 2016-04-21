from os.path import realpath, dirname, join, isdir
import sys

srcDir = ''

if hasattr(sys, 'frozen'):
   rootDir = dirname(sys.executable)
   srcDir = join(rootDir, 'ui')
else:
   srcDir = dirname(realpath(__file__))
   rootDir = dirname(srcDir)

resDir = join(rootDir, 'res')
