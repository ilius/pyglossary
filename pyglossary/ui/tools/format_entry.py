#!/usr/bin/env python

def formatEntry(entry):
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
