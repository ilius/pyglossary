from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator

	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "Random"


def normal(**options) -> "sortKeyType":
	from random import random
	return lambda words: random()


def locale(
	collator: "T_Collator",  # noqa: F821
) -> "sortKeyType":
	from random import random
	return lambda **options: lambda words: random()


def sqlite(**options) -> "sqliteSortKeyType":
	from random import random
	return [
		(
			"random",
			"REAL",
			lambda words: random(),
		),
	]


def sqlite_locale(
	collator: "T_Collator",  # noqa: F821
	**options,
) -> "Callable[..., sqliteSortKeyType]":
	from random import random
	return lambda **options: [
		(
			"random",
			"REAL",
			lambda words: random(),
		),
	]
