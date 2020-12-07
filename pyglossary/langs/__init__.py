
from pyglossary.core import rootDir
from os.path import join
import json

import logging
log = logging.getLogger("pyglossary")


class Lang(object):
	def __init__(
		self,
		codes: "List[str]",
		names: "List[str]",
		titleTag: str = "b",
		rtl: int = 0,
	):
		self._codes = codes
		self._names = names
		self._titleTag = titleTag
		self._rtl = rtl

	def __repr__(self) -> str:
		return (
			f'Lang('
			f'codes={self._codes!r}, '
			f'names={self._names!r}, '
			f'titleTag={self._titleTag!r}'
			f')'
		)

	def __str__(self) -> str:
		return f"Lang({self._codes + self._names})"

	@property
	def codes(self) -> "List[str]":
		return self._codes

	@property
	def names(self) -> "List[str]":
		return self._names

	@property
	def name(self) -> str:
		return self._names[0]

	@property
	def code(self) -> str:
		return self._codes[0]

	@property
	def titleTag(self) -> str:
		return self._titleTag

	@property
	def rtl(self) -> int:
		return self._rtl


class LangDict(dict):
	def load(self):
		from time import time as now
		if len(self) > 0:
			return
		t0 = now()
		filename = join(rootDir, "pyglossary", "langs", "langs.json")
		with open(filename, "r", encoding="utf-8") as _file:
			data = json.load(_file)
			for row in data:
				lang = Lang(
					codes=row["codes"],
					names=[row["name"]] + row["alt_names"],
					titleTag=row["title_tag"],
					rtl=row.get("rtl", 0),
				)
				for key in lang.codes:
					if key in self:
						log.error(f"duplicate language code: {key}")
					self[key] = lang
				for name in lang.names:
					if name in self:
						log.error(f"duplicate language name: {name}")
					self[name.lower()] = lang
		log.debug(f"LangDict: loaded, {len(self)} keys, took {(now() - t0)*1000:.1f} ms")

	def __getitem__(self, key: str) -> "Optional[Lang]":
		self.load()
		return self.get(key.lower(), None)

langDict = LangDict()
