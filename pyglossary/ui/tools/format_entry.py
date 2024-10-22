from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType

__all__ = ["formatEntry"]


def formatEntry(entry: EntryType) -> str:
	words = entry.l_word
	headword = ""
	if words:
		headword = words[0]
	lines = [
		f">> {headword}",
	]
	if len(words) > 1:
		lines += [f"Alt: {alt}" for alt in words[1:]]
	lines.append(f"\n{entry.defi}")
	return "\n".join(lines)
