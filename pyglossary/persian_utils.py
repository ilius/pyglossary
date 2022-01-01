# -*- coding: future_fstrings -*-
# -*- coding: future_fstrings -*-

from .text_utils import replacePostSpaceChar


def faEditStr(st: str) -> str:
	return replacePostSpaceChar(
		st.replace("ي", "ی").replace("ك", "ک").replace("ۂ", "هٔ").replace("ہ", "ه"),
		"،",
	)
