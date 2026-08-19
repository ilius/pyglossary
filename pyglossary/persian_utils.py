"""
Persian (Farsi) text normalization for glossary entries.

``faEditStr`` normalizes legacy Arabic-codepoint variants to standard Persian
letters, fixes heh forms, and adjusts punctuation spacing after the Arabic
comma.
"""

from __future__ import annotations

from .text_utils import replacePostSpaceChar

__all__ = ["faEditStr"]


def faEditStr(st: str) -> str:
	return replacePostSpaceChar(
		st.replace("ي", "ی")
		.replace("ك", "ک")
		.replace("ۂ", "هٔ")
		.replace("\u06c1", "\u0647"),
		"،",
	)
