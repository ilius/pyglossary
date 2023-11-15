import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "DictionaryForMIDs"


def normal(**options) -> "sortKeyType":
	re_punc = re.compile(
		r"""[!"$§%&/()=?´`\\{}\[\]^°+*~#'\-_.:,;<>@|]*""",
	)
	re_spaces = re.compile(" +")
	re_tabs = re.compile("\t+")

	def sortKey(words: "list[str]") -> str:
		word = words[0]
		word = word.strip()
		word = re_punc.sub("", word)
		word = re_spaces.sub(" ", word)
		word = re_tabs.sub(" ", word)
		word = word.lower()
		return word  # noqa: RET504

	return sortKey


def sqlite(**options) -> "sqliteSortKeyType":
	return [
		(
			"headword_norm",
			"TEXT",
			normal(**options),
		),
	]
