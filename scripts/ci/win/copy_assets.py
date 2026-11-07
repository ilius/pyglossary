#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path

dist_dir = os.getenv("DIST_DIR")
app_name = os.getenv("APPNAME", "main")

if not dist_dir:
	sys.stderr.write("empty DIST_DIR!")
	sys.exit(1)

dist_dir_path = Path(dist_dir)

if not dist_dir_path.exists():
	sys.stderr.write(f"DIST_DIR does not exist: {dist_dir}")
	sys.exit(1)

target_path = dist_dir_path / f"{app_name}.dist"

_ignoreJunk = shutil.ignore_patterns(
	"__pycache__",
	"*.pyc",
	".ruff_cache",
	".DS_Store",
	"*.md",
	"*.sh",
)


def ignoreDevFiles(dirpath: str, names: list[str]) -> set[str]:
	"""Skip dev-only files inside the pyglossary package (notes, caches, screenshots)."""
	ignored = set(_ignoreJunk(dirpath, names))
	if Path(dirpath).name == "ui_slint":
		ignored.update(name for name in names if name.endswith(".png"))
	return ignored


sources = [
	"about",
	"AUTHORS",
	"_license-dialog",
	"config.json",
	"plugins-meta",
	"help",
	"res",
	"pyglossary",
]

if not target_path.exists():
	sys.stderr.write(f"missing target dir: {target_path.absolute()}")
	sys.exit(1)

for source in sources:
	src = Path(source)
	try:
		if src.is_dir():
			copied_to = shutil.copytree(
				src,
				target_path / src.name,
				dirs_exist_ok=True,
				symlinks=True,
				ignore_dangling_symlinks=True,
				ignore=ignoreDevFiles if source == "pyglossary" else None,
			)
		else:
			copied_to = shutil.copy(src, target_path, follow_symlinks=False)
		sys.stdout.write(f"Copied {src} -> {copied_to}")
	except Exception as e:  # noqa: BLE001
		sys.stderr.write(f"Error copying {src}: {e}")
		sys.exit(1)
