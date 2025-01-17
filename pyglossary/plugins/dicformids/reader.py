# -*- coding: utf-8 -*-
# mypy: ignore-errors
from __future__ import annotations

import operator
import os
import re
from os.path import join
from typing import TYPE_CHECKING

from pyglossary.plugins.tabfile import Reader as TabfileReader

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = False
	re_number = re.compile(r"\d+")

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._tabFileNames: list[str] = []
		self._tabFileReader = None

	def open(self, dirname: str) -> None:
		self._dirname = dirname
		orderFileNames: list[tuple[int, str]] = []
		for fname in os.listdir(dirname):
			if not fname.startswith("directory"):
				continue
			try:
				num = self.re_number.findall(fname)[-1]
			except IndexError:
				pass
			else:
				orderFileNames.append((num, fname))
		orderFileNames.sort(
			key=operator.itemgetter(0),
			reverse=True,
		)
		self._tabFileNames = [x[1] for x in orderFileNames]
		self.nextTabFile()

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		return self

	def __next__(self) -> EntryType:
		for _ in range(10):
			try:
				return next(self._tabFileReader)
			except StopIteration:  # noqa: PERF203
				self._tabFileReader.close()
				self.nextTabFile()
		return None

	def nextTabFile(self) -> None:
		try:
			tabFileName = self._tabFileNames.pop()
		except IndexError:
			raise StopIteration from None
		self._tabFileReader = TabfileReader(self._glos, hasInfo=False)
		self._tabFileReader.open(join(self._dirname, tabFileName), newline="\n")

	def close(self) -> None:
		if self._tabFileReader:
			try:
				self._tabFileReader.close()
			except Exception:
				pass  # noqa: S110
		self._tabFileReader = None
		self._tabFileNames = []
