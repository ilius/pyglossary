# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Sql"
description = "SQL"
extensions = (".sql",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
}
depends = {}


class Writer(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
		encoding: str = "utf-8",
		infoKeys: Optional[List] = None,
		addExtraInfo: bool = True,
		newline: str = "<br>",
		transaction: bool = False,
	) -> Generator[None, "BaseEntry", None]:
		glos = self._glos
		fileObj = open(filename, "w", encoding=encoding)

		infoDefLine = "CREATE TABLE dbinfo ("
		infoValues = []

		if not infoKeys:
			infoKeys = [
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

		for key in infoKeys:
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

		if addExtraInfo:
			fileObj.write(
				"CREATE TABLE dbinfo_extra ("
				"\'id\' INTEGER PRIMARY KEY NOT NULL, "
				"\'name\' TEXT UNIQUE, \'value\' TEXT);\n"
			)

		fileObj.write(
			"CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, " +
			"\'w\' TEXT, \'m\' TEXT);\n"
		)

		if transaction:
			fileObj.write("BEGIN TRANSACTION;\n")
		fileObj.write(f"INSERT INTO dbinfo VALUES({','.join(infoValues)});\n")

		if addExtraInfo:
			extraInfo = glos.getExtraInfos(infoKeys)
			for index, (key, value) in enumerate(extraInfo.items()):
				key = key.replace("\'", "\'\'")
				value = value.replace("\'", "\'\'")
				fileObj.write(
					f"INSERT INTO dbinfo_extra VALUES({index+1}, "
					f"\'{key}\', \'{value}\');\n"
				)

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
				f"INSERT INTO word VALUES({i+1}, \'{word}\', \'{defi}\');\n"
			)
			i += 1
		if transaction:
			fileObj.write("END TRANSACTION;\n")
		fileObj.write("CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);\n")
