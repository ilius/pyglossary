from __future__ import annotations

import json
import logging
from os.path import join

from pyglossary.core import rootDir

log = logging.getLogger("pyglossary")


class Lang:
	def __init__(
		self,
		codes: list[str],
		names: list[str],
		titleTag: str = "b",
		rtl: int = 0,
	) -> None:
		self._codes = codes
		self._names = names
		self._titleTag = titleTag
		self._rtl = rtl

	def __repr__(self) -> str:
		return (
			"Lang("
			f"codes={self._codes!r}, "
			f"names={self._names!r}, "
			f"titleTag={self._titleTag!r}"
			")"
		)

	def __str__(self) -> str:
		return f"Lang({self._codes + self._names})"

	@property
	def codes(self) -> list[str]:
		return self._codes

	@property
	def names(self) -> list[str]:
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
	def _addLang(self, lang: Lang) -> None:
		for key in lang.codes:
			if key in self:
				log.error(f"duplicate language code: {key}")
			self[key] = lang
		for name in lang.names:
			if name in self:
				log.error(f"duplicate language name: {name}")
			self[name.lower()] = lang

	def load(self) -> None:
		from time import perf_counter as now

		if len(self) > 0:
			return
		t0 = now()
		filename = join(rootDir, "pyglossary", "langs", "langs.json")
		with open(filename, encoding="utf-8") as _file:
			data = json.load(_file)
			for row in data:
				self._addLang(
					Lang(
						codes=row["codes"],
						names=[row["name"]] + row["alt_names"],
						titleTag=row["title_tag"],
						rtl=row.get("rtl", 0),
					),
				)

		log.debug(
			f"LangDict: loaded, {len(self)} keys, "
			f"took {(now() - t0) * 1000:.1f} ms",
		)

	def __getitem__(self, key: str) -> Lang | None:
		self.load()
		return self.get(key.lower(), None)


langDict = LangDict()
