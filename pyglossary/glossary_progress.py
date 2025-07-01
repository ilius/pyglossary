from __future__ import annotations

from typing import TYPE_CHECKING

from .core import log

if TYPE_CHECKING:
	from collections.abc import Iterable, Iterator
	from typing import Protocol

	from .glossary_types import EntryType
	from .ui_type import UIType

	class ReaderType(Protocol):
		def __iter__(self) -> Iterator[EntryType]: ...

		def __len__(self) -> int: ...


__all__ = ["GlossaryProgress"]


class GlossaryProgress:
	def __init__(
		self,
		ui: UIType | None = None,  # noqa: F821
	) -> None:
		self._ui = ui
		self._progressbar = True

	def clear(self) -> None:
		self._progressbar = True

	@property
	def progressbar(self) -> bool:
		return self._ui is not None and self._progressbar

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None:
		self._progressbar = enabled

	def progressInit(
		self,
		*args,  # noqa: ANN002
	) -> None:
		if self._ui and self._progressbar:
			self._ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if total == 0:
			log.warning(f"{pos=}, {total=}")
			return
		if self._ui is None:
			return
		self._ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self) -> None:
		if self._ui and self._progressbar:
			self._ui.progressEnd()

	def _byteProgressIter(
		self,
		iterable: Iterable[EntryType],
	) -> Iterator[EntryType]:
		lastPos = 0
		for entry in iterable:
			if entry is None:
				continue
			yield entry
			if (bp := entry.byteProgress()) and bp[0] > lastPos + 100_000:
				self.progress(bp[0], bp[1], unit="bytes")
				lastPos = bp[0]

	def _wordCountProgressIter(
		self,
		iterable: Iterable[EntryType],
		wordCount: int,
	) -> Iterator[EntryType]:
		wordCountThreshold = max(
			1,
			min(
				500,
				wordCount // 200,
			),
		)
		for index, entry in enumerate(iterable):
			yield entry
			if index % wordCountThreshold == 0:
				self.progress(index, wordCount)

	def _progressIter(self, reader: ReaderType) -> Iterable[EntryType]:
		if not self.progressbar:
			return reader
		if getattr(reader, "useByteProgress", False):
			return self._byteProgressIter(reader)
		if (wordCount := len(reader)) > 0:
			return self._wordCountProgressIter(reader, wordCount)
		return self._byteProgressIter(reader)
