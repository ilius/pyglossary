# -*- coding: utf-8 -*-

import io
import typing
from typing import Generator, List

from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	ListOption,
	NewlineOption,
	Option,
)

enable = True
lname = "sql"
format = "Sql"
description = "SQL (.sql)"
extensions = (".sql",)
extensionCreate = ".sql"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/SQL"
website = None
optionsProp: "dict[str, Option]" = {
	"encoding": EncodingOption(),
	"info_keys": ListOption(comment="List of dbinfo table columns"),
	"add_extra_info": BoolOption(comment="Create dbinfo_extra table"),
	"newline": NewlineOption(),
	"transaction": BoolOption(comment="Use TRANSACTION"),
}


class Writer(object):
	_encoding: str = "utf-8"
	_info_keys: "List | None" = None
	_add_extra_info: bool = True
	_newline: str = "<br>"
	_transaction: bool = False

	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._filename = ""
		self._file: "io.IOBase | None" = None

	def finish(self: "typing.Self") -> None:
		self._filename = ""
		if self._file:
			self._file.close()
			self._file = None

	def open(self: "typing.Self", filename: str) -> None:
		self._filename = filename
		self._file = open(filename, "wt", encoding=self._encoding)
		self._writeInfo()

	def _writeInfo(self: "typing.Self") -> None:
		fileObj = self._file
		if fileObj is None:
			raise ValueError("fileObj is None")
		newline = self._newline
		info_keys = self._getInfoKeys()
		infoDefLine = "CREATE TABLE dbinfo ("
		infoValues = []
		glos = self._glos

		for key in info_keys:
			value = glos.getInfo(key)
			value = value\
				.replace("\'", "\'\'")\
				.replace("\x00", "")\
				.replace("\r", "")\
				.replace("\n", newline)
			infoValues.append(f"\'{value}\'")
			infoDefLine += f"{key} char({len(value)}), "

		infoDefLine = infoDefLine[:-2] + ");"
		fileObj.write(infoDefLine + "\n")

		if self._add_extra_info:
			fileObj.write(
				"CREATE TABLE dbinfo_extra ("
				"\'id\' INTEGER PRIMARY KEY NOT NULL, "
				"\'name\' TEXT UNIQUE, \'value\' TEXT);\n",
			)

		fileObj.write(
			"CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, "
			"\'w\' TEXT, \'m\' TEXT);\n",
		)

		if self._transaction:
			fileObj.write("BEGIN TRANSACTION;\n")
		fileObj.write(f"INSERT INTO dbinfo VALUES({','.join(infoValues)});\n")

		if self._add_extra_info:
			extraInfo = glos.getExtraInfos(info_keys)
			for index, (key, value) in enumerate(extraInfo.items()):
				key = key.replace("\'", "\'\'")
				value = value.replace("\'", "\'\'")
				fileObj.write(
					f"INSERT INTO dbinfo_extra VALUES({index+1}, "
					f"\'{key}\', \'{value}\');\n",
				)

	def _getInfoKeys(self: "typing.Self") -> "list[str]":
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

	def write(self: "typing.Self") -> "Generator[None, EntryType, None]":
		newline = self._newline

		fileObj = self._file
		if fileObj is None:
			raise ValueError("fileObj is None")

		i = 0
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# FIXME
				continue
			word = entry.s_word
			defi = entry.defi
			word = word.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			defi = defi.replace("\'", "\'\'")\
				.replace("\r", "").replace("\n", newline)
			fileObj.write(
				f"INSERT INTO word VALUES({i+1}, \'{word}\', \'{defi}\');\n",
			)
			i += 1
		if self._transaction:
			fileObj.write("END TRANSACTION;\n")
		fileObj.write("CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);\n")
