
from pyglossary.core import dataDir
from os.path import join
import csv
from typing import (
	List,
	Optional,
)


class Lang(object):
	def __init__(self, codes: List[str], names: List[str]):
		self._codes = codes
		self._names = names

	def __repr__(self) -> str:
		return f"Lang(codes={self._codes!r}, names={self._names!r})"

	def __str__(self) -> str:
		return f"Lang({self._codes + self._names})"

	@property
	def codes(self):
		return self._codes

	@property
	def names(self):
		return self._names

	@property
	def name(self):
		return self._names[0]


class LandDict(dict):
	def __init__(self):
		self._loaded = False

	def load(self):
		print("LandDict: loading")
		if self._loaded:
			return
		filename = join(dataDir, "pyglossary", "langs", "list.csv")
		with open(filename, "r", encoding="utf-8") as _file:
			csvReader = csv.reader(
				_file,
				dialect="excel",
			)
			for row in csvReader:
				lang = Lang(
					codes=row[:2],
					names=row[2:],
				)
				for key in lang.codes:
					self[key] = lang
				for key in lang.names:
					self[key] = lang
		print(f"LandDict: loaded, {len(self)} keys")

	def __getitem__(self, key: str) -> Optional[Lang]:
		self.load()
		return self.get(key, None)
