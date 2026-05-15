# -*- coding: utf-8 -*-
# Read Apple Dictionary XML sources written by Dictionary Development Kit format.
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

from __future__ import annotations

import os
import plistlib
from os.path import basename, dirname, isdir, isfile, join, relpath, splitext
from typing import TYPE_CHECKING

from lxml import etree
from lxml.etree import QName

from pyglossary.core import log
from pyglossary.info import c_author, c_copyright, c_name

if TYPE_CHECKING:
	from collections.abc import Iterator

	from lxml.etree import _Element

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]

NS_D = "http://www.apple.com/DTDs/DictionaryService-1.0.rng"


class Reader:
	useByteProgress = False
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._dirname = ""
		self._xmlPath = ""
		self._entryElems: list[_Element] = []
		self._resourceFiles: list[tuple[str, str]] = []
		self._entryCount = 0

	def open(self, filename: str) -> None:
		if not isdir(filename):
			raise TypeError(f"not a directory: {filename!r}")

		self._dirname = filename
		self._xmlPath = self._resolve_dictionary_xml(filename)
		self._load_plist_info()

		tree = etree.parse(self._xmlPath)
		root = tree.getroot()
		self._entryElems = []
		for elem in root:
			q = QName(elem)
			if q.namespace != NS_D or q.localname != "entry":
				continue
			if elem.get("id") == "front_back_matter":
				continue

			title = self._attrib_d(elem, "title")
			if not title:
				log.warning("skipping d:entry without d:title in %s", self._xmlPath)
				continue
			self._entryElems.append(elem)

		self._resourceFiles = self._collect_other_resources()
		self._entryCount = len(self._entryElems) + len(self._resourceFiles)

	def close(self) -> None:
		self._dirname = ""
		self._xmlPath = ""
		self._entryElems.clear()
		self._resourceFiles.clear()
		self._entryCount = 0

	def __len__(self) -> int:
		return self._entryCount

	def __iter__(self) -> Iterator[EntryType]:
		for rel, absPath in self._resourceFiles:
			with open(absPath, "rb") as fromFile:
				yield self._glos.newDataEntry(rel.replace("\\", "/"), fromFile.read())

		for elem in self._entryElems:
			terms_list = self._entry_terms(elem)

			defi_parts = []
			for child in elem:
				cq = QName(child)
				if cq.namespace == NS_D and cq.localname == "index":
					continue
				part = etree.tostring(
					child,
					encoding="unicode",
				)
				part = part.replace(
					'<a href="x-dictionary:d:',
					'<a href="bword://',
				).replace("<br/>", "<br>")
				defi_parts.append(part)

			defi = "".join(defi_parts)
			pos = defi.find('<div xmlns="')
			pos = defi.find(">", pos)
			defi = "<div>" + defi[pos + 1 :]

			yield self._glos.newEntry(
				terms_list if len(terms_list) > 1 else terms_list[0],
				defi,
				defiFormat="h",
			)

	@staticmethod
	def _attrib_d(elem: _Element, local: str) -> str | None:
		nsVal = elem.get(f"{{{NS_D}}}{local}")
		if nsVal is not None:
			return nsVal
		return elem.get(local)

	def _entry_terms(self, entry: _Element) -> list[str]:
		title = self._attrib_d(entry, "title")
		assert title
		alts = [title]
		seen: set[str] = {title}

		for child in entry:
			cq = QName(child)
			if cq.namespace != NS_D or cq.localname != "index":
				continue
			idx = self._attrib_d(child, "value")
			if idx and idx not in seen:
				seen.add(idx)
				alts.append(idx)
		return alts

	def _collect_other_resources(self) -> list[tuple[str, str]]:
		root = join(self._dirname, "OtherResources")
		if not isdir(root):
			return []

		results: list[tuple[str, str]] = []
		for dir_, _subdirs, files in os.walk(root):
			for name in files:
				if name.startswith("."):
					continue
				absPath = join(dir_, name)
				rel = relpath(absPath, root)
				results.append((rel, absPath))

		results.sort(key=lambda pair: pair[0])
		return results

	def _load_plist_info(self) -> None:
		plist_path = join(
			dirname(self._xmlPath),
			f"{splitext(basename(self._xmlPath))[0]}.plist",
		)
		if not isfile(plist_path):
			return

		try:
			with open(plist_path, "rb") as plistFile:
				info = plistlib.load(plistFile)
		except (OSError, plistlib.InvalidFileException):
			log.exception("failed to parse plist %s", plist_path)
			return

		if not isinstance(info, dict):
			return

		mapping = {
			"CFBundleDisplayName": c_name,
			"DCSDictionaryCopyright": c_copyright,
			"DCSDictionaryManufacturerName": c_author,
		}
		for plistKey, glossaryKey in mapping.items():
			val = info.get(plistKey)
			if isinstance(val, str) and val.strip():
				self._glos.setInfo(glossaryKey, val.strip())

	def _resolve_dictionary_xml(self, dirname: str) -> str:
		dirname_base = basename(dirname).replace(".", "_")
		preferred = join(dirname, f"{dirname_base}.xml")
		if isfile(preferred):
			return preferred

		candidates = sorted(
			join(dirname, n)
			for n in os.listdir(dirname)
			if n.endswith(".xml") and isfile(join(dirname, n))
		)
		if len(candidates) == 1:
			return candidates[0]
		if not candidates:
			raise LookupError(f"no dictionary XML found in directory {dirname!r}")
		raise LookupError(
			f"multiple XML files in {dirname!r}, expected {basename(preferred)!r} "
			f"or a single *.xml file (found: {[basename(c) for c in candidates]})",
		)
