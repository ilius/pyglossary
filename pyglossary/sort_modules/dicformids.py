from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "DictionaryForMIDs"


def normal(**_options: Any) -> SortKeyType:
	re_punc = re.compile(
		r"""[!"$§%&/()=?´`\\{}\[\]^°+*~#'\-_.:,;<>@|]*""",  # noqa: RUF001
	)
	re_spaces = re.compile(" +")
	re_tabs = re.compile("\t+")

	def sortKey(words: list[str]) -> str:
		term = words[0]
		term = term.strip()
		term = re_punc.sub("", term)
		term = re_spaces.sub(" ", term)
		term = re_tabs.sub(" ", term)
		term = term.lower()
		return term  # noqa: RET504

	return sortKey


def sqlite(**options: Any) -> SQLiteSortKeyType:
	return [
		(
			"headword_norm",
			"TEXT",
			normal(**options),
		),
	]
