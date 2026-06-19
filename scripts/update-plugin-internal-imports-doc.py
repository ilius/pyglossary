#!/usr/bin/python3
"""Add plugin-usage docstrings to imported pyglossary modules."""

from __future__ import annotations

import ast
import re
from os.path import abspath, dirname
from pathlib import Path

rootDir = dirname(dirname(abspath(__file__)))
pluginsDir = Path(rootDir) / "pyglossary" / "plugins"
pyglossaryDir = Path(rootDir) / "pyglossary"

PLUGINS_USAGE_LINE = "This module is used in plugins."
_PLUGINS_USAGE_RE = re.compile(
	r"^This module is used in plugins\.?\s*$",
	re.MULTILINE,
)


def module_path_from_import(module: str, pyglossary_dir: Path) -> Path | None:
	if module == "pyglossary":
		return None
	if not module.startswith("pyglossary."):
		return None
	if module.startswith("pyglossary.plugins."):
		return None
	rel = module.removeprefix("pyglossary.").replace(".", "/")
	py_file = pyglossary_dir / f"{rel}.py"
	if py_file.is_file():
		return py_file
	init_file = pyglossary_dir / rel / "__init__.py"
	if init_file.is_file():
		return init_file
	return None


def internal_module_paths_from_tree(  # noqa: C901, PLR0912
	tree: ast.AST,
	pyglossary_dir: Path,
) -> set[Path]:
	paths: set[Path] = set()
	for node in ast.walk(tree):
		if isinstance(node, ast.ImportFrom):
			if node.module == "pyglossary":
				for alias in node.names:
					path = module_path_from_import(
						f"pyglossary.{alias.name}",
						pyglossary_dir,
					)
					if path:
						paths.add(path.resolve())
				continue
			if not node.module or not node.module.startswith("pyglossary."):
				continue
			if node.module.startswith("pyglossary.plugins."):
				continue
			if node.module.startswith("pyglossary.plugin_lib"):
				continue
			if len(node.names) == 1 and node.names[0].name == "*":
				path = module_path_from_import(node.module, pyglossary_dir)
				if path:
					paths.add(path.resolve())
				continue
			for alias in node.names:
				submodule = f"{node.module}.{alias.name}"
				path = module_path_from_import(submodule, pyglossary_dir)
				if path is None:
					path = module_path_from_import(node.module, pyglossary_dir)
				if path:
					paths.add(path.resolve())
		elif isinstance(node, ast.Import):
			for alias in node.names:
				path = module_path_from_import(alias.name, pyglossary_dir)
				if path:
					paths.add(path.resolve())
	return paths


def collect_plugin_imported_module_paths(
	plugins_dir: Path,
	pyglossary_dir: Path,
) -> set[Path]:
	paths: set[Path] = set()
	for py_file in plugins_dir.rglob("*.py"):
		source = py_file.read_text(encoding="utf-8")
		try:
			tree = ast.parse(source)
		except SyntaxError:
			continue
		paths |= internal_module_paths_from_tree(tree, pyglossary_dir)
	return paths


def _module_docstring_node(tree: ast.Module) -> ast.Expr | None:
	if not tree.body:
		return None
	first = tree.body[0]
	if not isinstance(first, ast.Expr):
		return None
	value = first.value
	if isinstance(value, ast.Constant) and isinstance(value.value, str):
		return first
	return None


def _docstring_insert_index(lines: list[str]) -> int:
	index = 0
	if index < len(lines) and lines[index].startswith("#!"):
		index += 1
	while index < len(lines):
		stripped = lines[index].strip()
		if not stripped or stripped.startswith("#"):
			index += 1
			continue
		break
	return index


def _upsert_plugins_usage_in_docstring(docstring: str) -> str:
	if _PLUGINS_USAGE_RE.search(docstring):
		return _PLUGINS_USAGE_RE.sub(PLUGINS_USAGE_LINE, docstring, count=1)
	if docstring.endswith("\n"):
		return docstring + "\n" + PLUGINS_USAGE_LINE + "\n"
	return docstring + "\n\n" + PLUGINS_USAGE_LINE + "\n"


def _replace_module_docstring(source: str, new_docstring: str) -> str:
	tree = ast.parse(source)
	doc_node = _module_docstring_node(tree)
	lines = source.splitlines(keepends=True)
	if doc_node is None:
		insert_at = _docstring_insert_index(lines)
		new_block = f'"""{new_docstring}"""\n\n'
		return "".join(lines[:insert_at] + [new_block] + lines[insert_at:])
	start = doc_node.lineno - 1
	end = doc_node.end_lineno
	new_block = f'"""{new_docstring}"""\n'
	return "".join(lines[:start] + [new_block] + lines[end:])


def update_source_plugins_usage_doc(source: str) -> tuple[str, bool]:
	if _PLUGINS_USAGE_RE.search(source):
		return source, False
	try:
		tree = ast.parse(source)
	except SyntaxError:
		return source, False
	docstring = ast.get_docstring(tree)
	if docstring is None:
		new_docstring = PLUGINS_USAGE_LINE
	else:
		new_docstring = _upsert_plugins_usage_in_docstring(docstring)
	new_source = _replace_module_docstring(source, new_docstring)
	return new_source, new_source != source


def update_file(path: Path) -> bool:
	source = path.read_text(encoding="utf-8")
	new_source, changed = update_source_plugins_usage_doc(source)
	if changed:
		path.write_text(new_source, encoding="utf-8")
	return changed


def main() -> int:
	module_paths = collect_plugin_imported_module_paths(
		pluginsDir,
		pyglossaryDir,
	)
	changed = 0
	for path in sorted(module_paths):
		if update_file(path):
			print(path.relative_to(rootDir))
			changed += 1
	print(f"updated {changed} file(s)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
