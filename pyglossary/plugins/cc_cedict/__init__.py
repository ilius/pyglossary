import re
from pyglossary.plugins import formats_common
from . import conv

enable = True
format = 'CC-CEDICT'
# this typo is part of the API used by PyGlossary; don't change it!
extentions = ('.u8', '.txt')

entry_count_reg = re.compile(r'#! entries=(\d+)')
class Reader:
    def __init__(self, glos):
        self.glos = glos
        self.file = None
        self.entries_left = 0

    def open(self, filename, encoding='utf-8'):
        if self.file:
            self.file.close()
        self.file = open(filename, 'r', encoding=encoding)
        for line in self.file:
            match = entry_count_reg.match(line)
            if match is not None:
                count = match.groups()[0]
                self.entries_left = int(count)
                break

    def close(self):
        if self.file:
            self.file.close()
        self.file = None
        self.entries_left = 0

    def __len__(self):
        return self.entries_left

    def __iter__(self):
        if not self.file:
            formats_common.log.error("no file open")
        for line in self.file:
            if not line.startswith('#'):
                if self.entries_left > 0:
                    self.entries_left -= 1
                names, article = conv.make_entry(*conv.parse_line(line))
                entry = self.glos.newEntry(names, article, defiFormat='h')
                yield entry
