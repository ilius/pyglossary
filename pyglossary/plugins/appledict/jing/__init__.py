"""checking XML files with Apple Dictionary Schema.

this module can be run from command line with only argument -- file to
be checked.  otherwise, you need to import this module and call
`run` function with the filename as its only argument.
"""

__all__ = ["run", "JingTestError"]

from .main import run, JingTestError
