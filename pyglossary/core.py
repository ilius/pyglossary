import logging
from pprint import pformat
import sys
import os
from os.path import (
    join,
    isfile,
    isdir,
    exists,
    realpath,
    dirname,
)
import platform

class MyLogger(logging.Logger):
    levelsByVerbosity = (
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        logging.NOTSET,
    )
    levelNamesCap = [
        'Critical',
        'Error',
        'Warning',
        'Info',
        'Debug',
        'All',#'Not-Set',
    ]
    def setVerbosity(self, verbosity):
        self.setLevel(self.levelsByVerbosity[verbosity])
        self._verbosity = verbosity

    def getVerbosity(self):
        return getattr(self, '_verbosity', 3)  # FIXME

    def pretty(self, data, header=''):
        self.debug(header + pformat(data))

    def isDebug(self):
        return self.getVerbosity() >= 4



sysName = platform.system()



if hasattr(sys, 'frozen'):
   rootDir = dirname(sys.executable)
   uiDir = join(rootDir, 'ui')
else:
   uiDir = dirname(realpath(__file__))
   rootDir = dirname(uiDir)

resDir = join(rootDir, 'res')

if os.sep=='/': ## Operating system is Unix-Like
    homeDir = os.getenv('HOME')
    user = os.getenv('USER')
    tmpDir = '/tmp'
    ## os.name == 'posix' ## ????
    if sysName=='Darwin':## MacOS X
        confDir = homeDir + '/Library/Preferences/PyGlossary' ## OR '/Library/PyGlossary'
        ## os.environ['OSTYPE'] == 'darwin10.0'
        ## os.environ['MACHTYPE'] == 'x86_64-apple-darwin10.0'
        ## platform.dist() == ('', '', '')
        ## platform.release() == '10.3.0'
    else:## GNU/Linux, ...
        confDir = homeDir + '/.pyglossary'
elif os.sep=='\\': ## Operating system is Windows
    homeDir = os.getenv('HOMEDRIVE') + os.getenv('HOMEPATH')
    user = os.getenv('USERNAME')
    tmpDir = os.getenv('TEMP')
    confDir = os.getenv('APPDATA') + '\\' + 'PyGlossary'
else:
    raise RuntimeError('Unknown path seperator(os.sep=="%s"), unknown operating system!'%os.sep)

confJsonFile = join(confDir, 'config.json')
rootConfJsonFile = join(rootDir, 'config.json')
userPluginsDir = join(confDir, 'plugins')


def checkCreateConfDir():
    if not isdir(confDir):
        if exists(confDir):## file, or anything other than directory
            os.rename(confDir, confDir + '.bak')## sorry, we don't import old config
        os.mkdir(confDir)
    if not exists(userPluginsDir):
        os.mkdir(userPluginsDir)
    if not isfile(confJsonFile):
        with open(rootConfJsonFile) as srcFp, open(confJsonFile, 'w') as userFp:
            userFp.write(srcFp.read())



logging.setLoggerClass(MyLogger)



