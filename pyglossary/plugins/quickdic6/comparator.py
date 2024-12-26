# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Literal

__all__ = ["Comparator"]


class Comparator:
	def __init__(self, locale_str: str, normalizer_rules: str, version: int) -> None:
		import icu

		self.version = version
		self.locale = icu.Locale(locale_str)
		self._comparator = (
			icu.RuleBasedCollator("&z<ȝ")
			if self.locale.getLanguage() == "en"
			else icu.Collator.createInstance(self.locale)
		)
		self._comparator.setStrength(icu.Collator.IDENTICAL)
		self.normalizer_rules = normalizer_rules
		self.normalize = icu.Transliterator.createFromRules(
			"",
			self.normalizer_rules,
			icu.UTransDirection.FORWARD,
		).transliterate

	def compare(
		self,
		tup1: tuple[str, str],
		tup2: tuple[str, str],
	) -> Literal[0, 1, -1]:
		# assert isinstance(tup1, tuple)
		# assert isinstance(tup2, tuple)
		s1, n1 = tup1
		s2, n2 = tup2
		cn = self._compare_without_dash(n1, n2)
		if cn != 0:
			return cn
		cn = self._comparator.compare(n1, n2)
		if cn != 0 or self.version < 7:
			return cn
		return self._comparator.compare(s1, s2)

	def _compare_without_dash(
		self,
		a: str,
		b: str,
	) -> Literal[0, 1, -1]:
		if self.version < 7:
			return 0
		s1 = self._without_dash(a)
		s2 = self._without_dash(b)
		return self._comparator.compare(s1, s2)

	@staticmethod
	def _without_dash(a: str) -> str:
		return a.replace("-", "").replace("þ", "th").replace("Þ", "Th")
