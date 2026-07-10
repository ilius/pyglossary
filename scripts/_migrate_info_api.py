#!/usr/bin/env python3
"""Migrate .info.getInfo / .info.setInfo / .info.getExtraInfos and glos.getInfo etc."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = frozenset({".venv", ".git", "__pycache__", "build", "dist"})


def find_call_close(s: str, open_paren_idx: int) -> int:
	depth = 0
	for k in range(open_paren_idx, len(s)):
		c = s[k]
		if c == "(":
			depth += 1
		elif c == ")":
			depth -= 1
			if depth == 0:
				return k
	raise RuntimeError("unbalanced")


def split_top_comma(expr: str) -> tuple[str, str]:
	depth = 0
	for i, c in enumerate(expr):
		if c in "([{":
			depth += 1
		elif c in ")]}":
			depth -= 1
		elif c == "," and depth == 0:
			return expr[:i].strip(), expr[i + 1 :].strip()
	raise ValueError(f"no comma: {expr!r}")


def replace_glos_methods(content: str) -> str:
	# glos.infoKeys() -> glos.info.infoKeys()  (and gloss)
	content = re.sub(
		r"\b(glos|gloss)\.infoKeys\(\)",
		r"\1.info.infoKeys()",
		content,
	)

	# glos.getExtraInfos([...]) -> glos.info - [...]
	content = re.sub(
		r"\b(glos|gloss)\.getExtraInfos\((\[[^\]]*\])\)",
		r"\1.info - \2",
		content,
	)

	# glos.getInfo(arg) -> glos.info[arg]  (arg has no parens)
	content = re.sub(
		r"\b(glos|gloss)\.getInfo\(([^()]*)\)",
		r"\1.info[\2]",
		content,
	)

	# glos.setInfo(key, val) with balanced parens — merge all occurrences
	pos = 0
	chunks: list[str] = []
	while pos < len(content):
		best_j = len(content)
		which: str | None = None
		for name in ("glos", "gloss"):
			needle = f"{name}.setInfo("
			j = content.find(needle, pos)
			if 0 <= j < best_j:
				best_j = j
				which = name
		if which is None:
			chunks.append(content[pos:])
			break
		chunks.append(content[pos:best_j])
		needle = f"{which}.setInfo("
		open_paren = best_j + len(needle) - 1
		close_paren = find_call_close(content, open_paren)
		args = content[open_paren + 1 : close_paren]
		key_expr, val_expr = split_top_comma(args)
		chunks.append(f"{which}.info[{key_expr}] = {val_expr}")
		pos = close_paren + 1
	return "".join(chunks)


def replace_info_dot_methods(content: str) -> str:
	# .info.getExtraInfos([...]) single-line
	content = re.sub(
		r"([\w.]+\.info)\.getExtraInfos\((\[[^\]]*\])\)",
		r"\1 - \2",
		content,
	)

	# .info.getInfo(arg) — group must end with .info
	content = re.sub(
		r"([\w.]+\.info)\.getInfo\(([^()]*)\)",
		r"\1[\2]",
		content,
	)

	# .info.setInfo(key, val)
	out: list[str] = []
	pos = 0
	needle = ".info.setInfo("
	while True:
		j = content.find(needle, pos)
		if j < 0:
			out.append(content[pos:])
			break
		out.append(content[pos:j])
		open_paren = j + len(needle) - 1
		close_paren = find_call_close(content, open_paren)
		args = content[open_paren + 1 : close_paren]
		key_expr, val_expr = split_top_comma(args)
		receiver = content[: j + 5]
		out.append(f"{receiver}[{key_expr}] = {val_expr}")
		pos = close_paren + 1
	return "".join(out)


def transform(content: str) -> str:
	content = replace_glos_methods(content)
	return replace_info_dot_methods(content)


def main() -> None:
	for path in sorted(ROOT.rglob("*.py")):
		if any(p in path.parts for p in SKIP_PARTS):
			continue
		if path.name == "_migrate_info_api.py":
			continue
		text = path.read_text(encoding="utf-8")
		new_text = transform(text)
		if new_text != text:
			path.write_text(new_text, encoding="utf-8")
			print(path.relative_to(ROOT))


if __name__ == "__main__":
	main()
