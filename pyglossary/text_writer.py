from __future__ import annotations

import logging
import os
from os.path import isdir
from typing import TYPE_CHECKING, cast

from .compression import compressionOpen as c_open
from .io_utils import nullTextIO

if TYPE_CHECKING:
	import io
	from collections.abc import Callable, Generator

	from .glossary_types import EntryType, WriterGlossaryType


__all__ = ["TextGlossaryWriter", "writeTxt"]

log = logging.getLogger("pyglossary")

file_size_check_every = 100


class TextGlossaryWriter:
	_encoding: str = "utf-8"
	_newline: str = "\n"
	_termListEncodeFunc: Callable[[list[str]], str] | None = None
	_termEscapeFunc: Callable[[str], str] | None = None
	_defiEscapeFunc: Callable[[str], str] | None = None
	_ext: str = ".txt"
	_head: str = ""
	_tail: str = ""
	_resources: bool = True
	_file_size_approx: int = 0
	_word_title: bool = False

	def __init__(
		self,
		glos: WriterGlossaryType,
		entryFmt: str = "",  # contain {word} and {defi}
		writeInfo: bool = True,
		outInfoKeysAliasDict: dict[str, str] | None = None,
	) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._resDir = ""

		if not entryFmt:
			raise ValueError("entryFmt argument is missing")

		self._entryFmt = entryFmt
		self._writeInfo = writeInfo
		self._outInfoKeysAliasDict = outInfoKeysAliasDict or {}
		# TODO: replace outInfoKeysAliasDict arg with a func?

	# TODO: use @property setters
	def setAttrs(  # noqa: PLR0913
		self,
		encoding: str | None = None,
		newline: str | None = None,
		termListEncodeFunc: Callable | None = None,
		termEscapeFunc: Callable | None = None,
		defiEscapeFunc: Callable | None = None,
		ext: str | None = None,
		head: str | None = None,
		tail: str | None = None,
		resources: bool | None = None,
		word_title: bool | None = None,
		file_size_approx: int | None = None,
	) -> None:
		if encoding is not None:
			self._encoding = encoding
		if newline is not None:
			self._newline = newline
		if termListEncodeFunc is not None:
			self._termListEncodeFunc = termListEncodeFunc
		if termEscapeFunc is not None:
			self._termEscapeFunc = termEscapeFunc
		if defiEscapeFunc is not None:
			self._defiEscapeFunc = defiEscapeFunc
		if ext is not None:
			self._ext = ext
		if head is not None:
			self._head = head
		if tail is not None:
			self._tail = tail
		if resources is not None:
			self._resources = resources
		if word_title is not None:
			self._word_title = word_title
		if file_size_approx is not None:
			self._file_size_approx = file_size_approx

	def open(self, filename: str) -> None:
		if self._file_size_approx > 0:
			self._glos.setInfo("file_count", "-1")
		self._open(filename)
		self._filename = filename
		if not self._glos.getConfig("skip_resources", False):
			self._resDir = f"{filename}_res"
			if not isdir(self._resDir):
				os.mkdir(self._resDir)

	def _doWriteInfo(self, file: io.TextIOBase) -> None:
		entryFmt = self._entryFmt
		outInfoKeysAliasDict = self._outInfoKeysAliasDict
		termEscapeFunc = self._termEscapeFunc
		defiEscapeFunc = self._defiEscapeFunc
		for key, value in self._glos.iterInfo():
			# both key and value are supposed to be non-empty string
			if not (key and value):
				log.warning(f"skipping info {key=}, {value=}")
				continue
			key = outInfoKeysAliasDict.get(key, key)  # noqa: PLW2901
			if not key:
				continue
			term = f"##{key}"
			if termEscapeFunc is not None:
				term = termEscapeFunc(term)
				if not term:
					continue
			if defiEscapeFunc is not None:
				value = defiEscapeFunc(value)  # noqa: PLW2901
				if not value:
					continue
			file.write(
				entryFmt.format(
					word=term,
					defi=value,
				),
			)

	def _open(self, filename: str) -> io.TextIOBase:
		if not filename:
			filename = self._glos.filename + self._ext

		file = self._file = cast(
			"io.TextIOBase",
			c_open(
				filename,
				mode="wt",
				encoding=self._encoding,
				newline=self._newline,
			),
		)
		file.write(self._head)

		if self._writeInfo:
			self._doWriteInfo(file)

		file.flush()
		return file

	def write(self) -> Generator[None, EntryType, None]:
		glos = self._glos
		file = self._file
		entryFmt = self._entryFmt
		termListEncodeFunc = self._termListEncodeFunc
		termEscapeFunc = self._termEscapeFunc
		defiEscapeFunc = self._defiEscapeFunc
		resources = self._resources
		word_title = self._word_title

		file_size_approx = self._file_size_approx
		entryCount = 0
		fileIndex = 0
		glosName = self._glos.getInfo("name") or self._filename

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(self._resDir)
				continue

			term = entry.s_term
			defi = entry.defi

			# if glos.alts:  # FIXME

			if word_title:
				defi = glos.wordTitleStr(entry.l_term[0]) + defi

			if termListEncodeFunc is not None:
				term = termListEncodeFunc(entry.l_term)
			elif termEscapeFunc is not None:
				term = termEscapeFunc(term)

			if defiEscapeFunc is not None:
				defi = defiEscapeFunc(defi)
			file.write(entryFmt.format(word=term, defi=defi))

			if file_size_approx > 0:
				entryCount += 1
				if (
					entryCount % file_size_check_every == 0
					and file.tell() >= file_size_approx
				):
					fileIndex += 1
					log.info(f"Creating {self._filename}.{fileIndex}")
					self._glos.setInfo("name", f"{glosName} part {fileIndex + 1}")
					file = self._open(f"{self._filename}.{fileIndex}")

	def finish(self) -> None:
		if self._tail:
			self._file.write(self._tail)
		self._file.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)


def writeTxt(  # noqa: PLR0913
	glos: WriterGlossaryType,
	entryFmt: str = "",  # contain {word} and {defi}
	filename: str = "",
	writeInfo: bool = True,
	termEscapeFunc: Callable | None = None,
	defiEscapeFunc: Callable | None = None,
	ext: str = ".txt",
	head: str = "",
	tail: str = "",
	outInfoKeysAliasDict: dict[str, str] | None = None,
	encoding: str = "utf-8",
	newline: str = "\n",
	resources: bool = True,
	word_title: bool = False,
) -> Generator[None, EntryType, None]:
	writer = TextGlossaryWriter(
		glos,
		entryFmt=entryFmt,
		writeInfo=writeInfo,
		outInfoKeysAliasDict=outInfoKeysAliasDict,
	)
	writer.setAttrs(
		encoding=encoding,
		newline=newline,
		termEscapeFunc=termEscapeFunc,
		defiEscapeFunc=defiEscapeFunc,
		ext=ext,
		head=head,
		tail=tail,
		resources=resources,
		word_title=word_title,
	)
	writer.open(filename)
	yield from writer.write()
	writer.finish()
