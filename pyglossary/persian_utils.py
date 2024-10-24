# -*- coding: utf-8 -*-

from __future__ import annotations

from .text_utils import replacePostSpaceChar

__all__ = ["faEditStr"]


def faEditStr(st: str) -> str:
	return replacePostSpaceChar(
		st.replace("ي", "ی").replace("ك", "ک").replace("ۂ", "هٔ").replace("ہ", "ه"),
		"،",
	)
