import logging

class MyLogger(logging.Logger):
    levelsByVerbosity = (
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        logging.NOTSET,
    )
    def setVerbosity(self, verbosity):
        self.setLevel(self.levelsByVerbosity[verbosity])
        self._verbosity = verbosity
    getVerbosity = lambda self: self._verbosity


logging.setLoggerClass(MyLogger)



