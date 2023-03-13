#!/usr/bin/env python

from pyglossary.glossary_types import EntryType


def formatEntry(entry: "EntryType") -> str:
    words = entry.l_word
    headword = ""
    if words:
        headword = words[0]
    lines = [
        f">>> {headword}",
    ]
    if len(words) > 1:
        alts = " | ".join(words[1:])
        lines.append(f"Alt: {alts}")
    lines.append(f"\n{entry.defi}")
    return "\n".join(lines)
