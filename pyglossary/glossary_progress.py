from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .core import log

if TYPE_CHECKING:
	from collections.abc import Iterable, Iterator
	from typing import Protocol

	from .glossary_types import EntryType
	from .ui_type import UIType

	class ReaderType(Protocol):
		def __iter__(self) -> Iterator[EntryType]: ...

		def __len__(self) -> int: ...

		def countResourceFiles(self) -> int: ...


__all__ = ["GlossaryProgress"]


class GlossaryProgress:
	"""Progress-bar helpers mixed into :class:`~pyglossary.glossary_v2.GlossaryCommon`."""

	def __init__(
		self,
		ui: UIType | None = None,  # noqa: F821
	) -> None:
		"""Store *ui* for progress updates; bar is active only when UI is set."""
		self._ui = ui
		self._progressbar = True

	def clear(self) -> None:
		"""Reset state and re-enable the progress-bar flag."""
		self._progressbar = True

	@property
	def progressbar(self) -> bool:
		"""Whether progress updates are forwarded to the UI."""
		return self._ui is not None and self._progressbar

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None:
		self._progressbar = enabled

	def progressInit(self, *args: Any) -> None:
		"""Start or restart a progress phase (forwards *args* to the UI)."""
		if self._ui and self._progressbar:
			self._ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		"""Report current position: ``pos`` of ``total`` with the given *unit*."""
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
		"""Mark the current progress phase complete."""
		if self._ui and self._progressbar:
			self._ui.progressEnd()

	def _byteProgressIter(
		self,
		reader: ReaderType,
	) -> Iterator[EntryType]:
		"""
		Wrap a byte-progress reader and update the progress bar while iterating.

		Text entries report progress via ``entry.byteProgress()`` (file position).
		Resource entries (``entry.isData()``) that are read from individual files
		have no byte position, so after main entries are read the bar switches to
		entry-count progress using ``reader.countResourceFiles()`` as the total.

		``countResourceFiles()`` is called once at the start. Readers cache
		the result (e.g. from a ``_res`` directory listing at open time), so
		other formats are not slowed down by repeated counting.

		DSL is the exception: loose resource files are referenced inside entry
		definitions, so the full count is only known after parsing. If the
		initial call returns zero, it is called again on the first data entry.
		"""
		lastPos = 0
		resIndex = 0
		resCount = 0
		countResourceFiles = getattr(reader, "countResourceFiles", None)
		if countResourceFiles:
			resCount = countResourceFiles()
		for entry in reader:
			if entry is None:
				continue
			yield entry
			bp = entry.byteProgress()
			if bp:
				if bp[0] > lastPos + 100_000:
					self.progress(bp[0], bp[1], unit="bytes")
					lastPos = bp[0]
			elif entry.isData():
				if not resCount and countResourceFiles:
					resCount = countResourceFiles()
				if resCount:
					if resIndex == 0:
						self.progressEnd()
						self.progressInit("Reading resources")
					elif resIndex % 10 == 0:
						self.progress(resIndex, resCount)
					resIndex += 1

	def _entryCountProgressIter(
		self,
		iterable: Iterable[EntryType],
		entryCount: int,
	) -> Iterator[EntryType]:
		"""
		Wrap an iterable and update progress by entry index.

		Updates are throttled to at most once every ``entryCount // 200``
		entries, clamped between 1 and 500.
		"""
		entryCountThreshold = max(
			1,
			min(
				500,
				entryCount // 200,
			),
		)
		for index, entry in enumerate(iterable):
			yield entry
			if index % entryCountThreshold == 0:
				self.progress(index, entryCount)

	def _progressIter(self, reader: ReaderType) -> Iterable[EntryType]:
		"""
		Return a progress-tracking wrapper for *reader*, or *reader* itself.

		Uses byte progress when ``reader.useByteProgress`` is set, otherwise
		entry-count progress when ``len(reader)`` is known. Falls back to byte
		progress when the entry count is zero. No wrapper when the bar is off.
		"""
		if not self.progressbar:
			return reader
		if getattr(reader, "useByteProgress", False):
			return self._byteProgressIter(reader)
		if (entryCount := len(reader)) > 0:
			return self._entryCountProgressIter(reader, entryCount)
		return self._byteProgressIter(reader)
