from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "DictionaryForMIDs"


def normal(**_options) -> SortKeyType:
	re_punc = re.compile(
		r"""[!"$§%&/()=?´`\\{}\[\]^°+*~#'\-_.:,;<>@|]*""",  # noqa: RUF001
	)
	re_spaces = re.compile(" +")
	re_tabs = re.compile("\t+")

	def sortKey(words: list[str]) -> str:
		word = words[0]
		word = word.strip()
		word = re_punc.sub("", word)
		word = re_spaces.sub(" ", word)
		word = re_tabs.sub(" ", word)
		word = word.lower()
		return word  # noqa: RET504

	return sortKey


def sqlite(**options) -> SQLiteSortKeyType:
	return [
		(
			"headword_norm",
			"TEXT",
			normal(**options),
		),
	]
