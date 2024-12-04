from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.icu_types import T_Collator
	from pyglossary.sort_keys_types import (
		SortKeyMakerType,
		SortKeyType,
		SQLiteSortKeyType,
	)


desc = "Random"


def normal(**_options) -> SortKeyType:
	from random import random

	return lambda _words: random()


def locale(
	collator: T_Collator,  # noqa: ARG001  # noqa: F821
) -> SortKeyMakerType:
	from random import random

	def sortKey(words: list[str]) -> Any:  # noqa: ARG001
		return random()

	def warpper(sortEncoding: str = "utf-8", **_options) -> SortKeyType:  # noqa: ARG001
		return sortKey

	return warpper


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
	_collator: T_Collator,  # noqa: F821
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
