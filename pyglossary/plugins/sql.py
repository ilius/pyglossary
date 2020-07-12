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


def iterSqlLines(
	glos: GlossaryType,
	filename: str = "",
	infoKeys: Optional[List] = None,
	addExtraInfo: bool = True,
	newline: str = "\\n",
	transaction: bool = False,
) -> Iterator[str]:
	newline = "<br>"
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
	yield infoDefLine

	if addExtraInfo:
		yield (
			"CREATE TABLE dbinfo_extra (" +
			"\'id\' INTEGER PRIMARY KEY NOT NULL, " +
			"\'name\' TEXT UNIQUE, \'value\' TEXT);"
		)

	yield (
		"CREATE TABLE word (\'id\' INTEGER PRIMARY KEY NOT NULL, " +
		"\'w\' TEXT, \'m\' TEXT);"
	)

	if transaction:
		yield "BEGIN TRANSACTION;"
	yield f"INSERT INTO dbinfo VALUES({','.join(infoValues)});"

	if addExtraInfo:
		extraInfo = glos.getExtraInfos(infoKeys)
		for index, (key, value) in enumerate(extraInfo.items()):
			key = key.replace("\'", "\'\'")
			value = value.replace("\'", "\'\'")
			yield (
				f"INSERT INTO dbinfo_extra VALUES({index+1}, "
				f"\'{key}\', \'{value}\');"
			)

	for i, entry in enumerate(glos):
		if entry.isData():
			# FIXME
			continue
		word = entry.word
		defi = entry.defi
		word = word.replace("\'", "\'\'")\
			.replace("\r", "").replace("\n", newline)
		defi = defi.replace("\'", "\'\'")\
			.replace("\r", "").replace("\n", newline)
		yield f"INSERT INTO word VALUES({i+1}, \'{word}\', \'{defi}\');"
	if transaction:
		yield "END TRANSACTION;"
	yield "CREATE INDEX ix_word_w ON word(w COLLATE NOCASE);"


def write(
	glos: GlossaryType,
	filename: str,
	encoding: str = "utf-8",
):
	with open(filename, "w", encoding=encoding) as fp:
		for line in iterSqlLines(
			glos,
			transaction=False,
		):
			fp.write(line + "\n")
