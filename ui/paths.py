from os.path import realpath, dirname, join

srcDir = ''
if __file__:
    srcDir = dirname(realpath(__file__))
if not srcDir:
    srcDir = '/usr/share/pyglossary'
rootDir = dirname(srcDir)



