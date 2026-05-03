# ICU collation helpers for slob (pyglossary)
from __future__ import annotations

from collections.abc import Callable
from functools import cache
from typing import TYPE_CHECKING

from icu import Collator, Locale, UCollAttribute, UCollAttributeValue

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator

PRIMARY: int = Collator.PRIMARY
SECONDARY: int = Collator.SECONDARY
TERTIARY: int = Collator.TERTIARY
QUATERNARY: int = Collator.QUATERNARY
IDENTICAL: int = Collator.IDENTICAL


@cache
def sortkey(
	strength: int,
	maxlength: int | None = None,
) -> Callable[[str], bytes]:
	c: T_Collator = Collator.createInstance(Locale(""))
	c.setStrength(strength)
	c.setAttribute(
		UCollAttribute.ALTERNATE_HANDLING,
		UCollAttributeValue.SHIFTED,
	)
	if maxlength is None:
		return c.getSortKey

	def func(x: str) -> bytes:
		return c.getSortKey(x)[:maxlength]

	return func
