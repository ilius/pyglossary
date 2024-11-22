from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.icu_types import T_Collator

	from .sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "Random"


def normal(**_options) -> SortKeyType:
	from random import random

	return lambda _words: random()


def locale(
	_collator: "T_Collator",  # noqa: F821
) -> SortKeyType:
	from random import random

	return lambda **_options: lambda _words: random()


def sqlite(**_options) -> SQLiteSortKeyType:
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
) -> Callable[..., SQLiteSortKeyType]:
	from random import random

	return lambda **_opt: [
		(
			"random",
			"REAL",
			lambda _words: random(),
		),
	]
