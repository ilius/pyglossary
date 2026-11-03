import io
import struct
import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugins.quickdic6.commons import LINKED_HASH_SET_INIT
from pyglossary.plugins.quickdic6.read_funcs import read_entry_index
from pyglossary.plugins.quickdic6.write_funcs import write_entry_index


class ReadEntryIndexTest(unittest.TestCase):
	def test_stop_list_size_mismatch(self):
		# Older DictionaryPC versions undercounted the size of stop-list
		# entries containing multi-byte characters.
		stop_list = ["für", "die"]
		entry = (
			"en",
			"en",
			"en",
			"",
			False,
			0,
			[],
			stop_list,
			[],
		)
		fp = io.BytesIO()
		write_entry_index(fp, entry)
		data = bytearray(fp.getvalue())

		stop_list_offset = data.index(LINKED_HASH_SET_INIT)
		size_offset = stop_list_offset - 4
		size = struct.unpack(">i", data[size_offset:stop_list_offset])[0]
		extra_bytes = sum(1 for c in "".join(stop_list) if ord(c) >= 0x80)
		struct.pack_into(">i", data, size_offset, size - extra_bytes)

		actual = read_entry_index(io.BytesIO(data))
		self.assertEqual(actual[7], stop_list)


if __name__ == "__main__":
	unittest.main()
