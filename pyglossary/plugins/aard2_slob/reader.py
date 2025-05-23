# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyglossary.core import exc_note, log, pip
from pyglossary.plugins.aard2_slob.tags import (
	supported_tags,
	t_copyright,
	t_created_at,
	t_created_by,
	t_edition,
	t_label,
	t_license_name,
	t_license_url,
	t_uri,
)

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary import slob
	from pyglossary.glossary_types import EntryType, ReaderGlossaryType


__all__ = ["Reader"]


class Reader:
	useByteProgress = False
	depends = {
		"icu": "PyICU",  # >=1.5
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._clear()
		self._re_bword = re.compile(
			"(<a href=[^<>]+?>)",
			re.IGNORECASE,
		)

	def close(self) -> None:
		if self._slobObj is not None:
			self._slobObj.close()
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._slobObj: slob.Slob | None = None

	# TODO: PLR0912 Too many branches (13 > 12)
	def open(self, filename: str) -> None:  # noqa: PLR0912
		try:
			import icu  # type: ignore # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install PyICU` to install")
			raise
		from pyglossary import slob

		self._filename = filename
		self._slobObj = slob.open(filename)
		tags = dict(self._slobObj.tags.items())

		if t_label in tags:
			self._glos.setInfo("name", tags[t_label])

		if t_created_at in tags:
			self._glos.setInfo("creationTime", tags[t_created_at])

		if t_created_by in tags:
			self._glos.setInfo("author", tags[t_created_by])

		copyrightLines: list[str] = []
		for key in (t_copyright, t_license_name, t_license_url):
			try:
				value = tags.pop(key)
			except KeyError:
				continue
			copyrightLines.append(value)
		if copyrightLines:
			self._glos.setInfo("copyright", "\n".join(copyrightLines))

		if t_uri in tags:
			self._glos.setInfo("website", tags[t_uri])

		if t_edition in tags:
			self._glos.setInfo("edition", tags[t_edition])

		for key, value in tags.items():
			if key in supported_tags:
				continue
			self._glos.setInfo(f"slob.{key}", value)

	def __len__(self) -> int:
		if self._slobObj is None:
			log.error("called len() on a reader which is not open")
			return 0
		return len(self._slobObj)

	@staticmethod
	def _href_sub(m: re.Match) -> str:
		st = m.group(0)
		if "//" in st:
			return st
		return st.replace('href="', 'href="bword://').replace(
			"href='",
			"href='bword://",
		)

	def __iter__(self) -> Iterator[EntryType | None]:
		from pyglossary.slob import MIME_HTML, MIME_TEXT

		if self._slobObj is None:
			raise RuntimeError("iterating over a reader while it's not open")

		slobObj = self._slobObj
		blobSet = set()

		# slob library gives duplicate blobs when iterating over slobObj
		# even keeping the last id is not enough, since duplicate blobs
		# are not all consecutive. so we have to keep a set of blob IDs

		for blob in slobObj:
			id_ = blob.identity
			if id_ in blobSet:
				yield None  # update progressbar
				continue
			blobSet.add(id_)

			# blob.key is str, blob.content is bytes
			word = blob.key

			ctype = blob.content_type.split(";")[0]
			if ctype not in {MIME_HTML, MIME_TEXT}:
				log.debug(f"unknown {blob.content_type=} in {word=}")
				word = word.removeprefix("~/")
				yield self._glos.newDataEntry(word, blob.content)
				continue
			defiFormat = ""
			if ctype == MIME_HTML:
				defiFormat = "h"
			elif ctype == MIME_TEXT:
				defiFormat = "m"

			defi = blob.content.decode("utf-8")
			defi = self._re_bword.sub(self._href_sub, defi)
			yield self._glos.newEntry(word, defi, defiFormat=defiFormat)
