import logging
from pprint import pformat

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
    getVerbosity = lambda self: self._verbosity
    def pretty(self, data, header=''):
        self.debug(header + pformat(data))


logging.setLoggerClass(MyLogger)



