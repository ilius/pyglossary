from itertools import (
    takewhile,
    repeat,
)

def fileCountLines(filename):
    f = open(filename, 'rb')## or 'r'
    bufgen = takewhile(
        lambda x: x, (f.read(1024*1024) for _ in repeat(None))
    )
    return sum(
        buf.count(b'\n') for buf in bufgen if buf
    )

class FileLineWrapper(object):
    def __init__(self, f):
        self.f = f
        self.line = 0
    def close(self):
        return self.f.close()
    def readline(self):
        self.line += 1
        return self.f.readline()
    __iter__ = lambda self: iter(self.f)

