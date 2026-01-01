from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType

__all__ = ["formatEntry"]


def formatEntry(entry: EntryType) -> str:
	terms = entry.l_term
	headword = ""
	if terms:
		headword = terms[0]
	if os.getenv("SHOW_DEFI_FORMAT") and entry.defiFormat:
		headword = f"{headword} (format: {entry.defiFormat})"
	lines = [
		f">> {headword}",
	]
	if len(terms) > 1:
		lines += [f"Alt: {alt}" for alt in terms[1:]]
	lines.append(f"\n{entry.defi}")
	return "\n".join(lines)
