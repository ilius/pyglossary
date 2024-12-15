# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	ListOption,
	NewlineOption,
	Option,
)

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = [
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "sql"
name = "Sql"
description = "SQL (.sql)"
extensions = (".sql",)
extensionCreate = ".sql"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/SQL"
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"info_keys": ListOption(comment="List of dbinfo table columns"),
	"add_extra_info": BoolOption(comment="Create dbinfo_extra table"),
	"newline": NewlineOption(),
	"transaction": BoolOption(comment="Use TRANSACTION"),
}


class Writer:
	_encoding: str = "utf-8"
	_info_keys: list | None = None
	_add_extra_info: bool = True
	_newline: str = "<br>"
	_transaction: bool = False

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.IOBase | None = None

	def finish(self) -> None:
		self._filename = ""
		if self._file:
			self._file.close()
			self._file = None

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = open(filename, "w", encoding=self._encoding)
		self._writeInfo()

	def _writeInfo(self) -> None:
		fileObj = self._file
		if fileObj is None:
			raise ValueError("fileObj is None")
		newline = self._newline
		info_keys = self._getInfoKeys()
		infoDefLine = "CREATE TABLE dbinfo ("
		infoValues: list[str] = []
		glos = self._glos

		for key in info_keys:
			value = glos.getInfo(key)
			value = (
				value.replace("'", "''")
				.replace("\x00", "")
				.replace("\r", "")
				.replace("\n", newline)
			)
			infoValues.append(f"'{value}'")
			infoDefLine += f"{key} char({len(value)}), "

		infoDefLine = infoDefLine[:-2] + ");"
		fileObj.write(infoDefLine + "\n")

		if self._add_extra_info:
			fileObj.write(
				"CREATE TABLE dbinfo_extra ("
				"'id' INTEGER PRIMARY KEY NOT NULL, "
				"'name' TEXT UNIQUE, 'value' TEXT);\n",
			)

		fileObj.write(
			"CREATE TABLE word ('id' INTEGER PRIMARY KEY NOT NULL, "
			"'w' TEXT, 'm' TEXT);\n",
		)
		fileObj.write(
			"CREATE TABLE alt ('id' INTEGER NOT NULL, 'w' TEXT);\n",
		)

		if self._transaction:
			fileObj.write("BEGIN TRANSACTION;\n")
		fileObj.write(f"INSERT INTO dbinfo VALUES({','.join(infoValues)});\n")

		if self._add_extra_info:
			extraInfo = glos.getExtraInfos(info_keys)
			for index, (key, value) in enumerate(extraInfo.items()):
				key2 = key.replace("'", "''")
				value2 = value.replace("'", "''")
				fileObj.write(
					f"INSERT INTO dbinfo_extra VALUES({index + 1}, "
					f"'{key2}', '{value2}');\n",
				)

	def _getInfoKeys(self) -> list[str]:
		info_keys = self._info_keys
		if info_keys:
			return info_keys
		return [
			"dbname",
			"author",
			"version",
			"direction",
			"origLang",
			"destLang",
			"license",
			"category",
			"description",
		]

	def write(self) -> Generator[None, EntryType, None]:
		newline = self._newline

		fileObj = self._file
		if fileObj is None:
			raise ValueError("fileObj is None")

		def fixStr(word: str) -> str:
			return word.replace("'", "''").replace("\r", "").replace("\n", newline)

		id_ = 1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# FIXME
				continue
			words = entry.l_word
			word = fixStr(words[0])
			defi = fixStr(entry.defi)
			fileObj.write(
				f"INSERT INTO word VALUES({id_}, '{word}', '{defi}');\n",
			)
			for alt in words[1:]:
				fileObj.write(
					f"INSERT INTO alt VALUES({id_}, '{fixStr(alt)}');\n",
				)
			id_ += 1

		if self._transaction:
			fileObj.write("END TRANSACTION;\n")

		fileObj.write("CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);\n")
		fileObj.write("CREATE INDEX ix_alt_id ON alt(id COLLATE NOCASE);\n")
		fileObj.write("CREATE INDEX ix_alt_w ON alt(w COLLATE NOCASE);\n")
