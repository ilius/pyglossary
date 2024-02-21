from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator

	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "Random"


def normal(**_options) -> "sortKeyType":
	from random import random

	return lambda _words: random()


def locale(
	_collator: "T_Collator",  # noqa: F821
) -> "sortKeyType":
	from random import random

	return lambda **_options: lambda _words: random()


def sqlite(**_options) -> "sqliteSortKeyType":
	from random import random

	return [
		(
			"random",
			"REAL",
			lambda _words: random(),
		),
	]


def sqlite_locale(
	_collator: "T_Collator",  # noqa: F821
	**_options,
) -> "Callable[..., sqliteSortKeyType]":
	from random import random

	return lambda **_opt: [
		(
			"random",
			"REAL",
			lambda _words: random(),
		),
	]
