#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path

dist_dir = os.getenv("DIST_DIR")

if not dist_dir:
	sys.stderr.write("empty DIST_DIR!")
	sys.exit(1)

dist_dir_path = Path(dist_dir)

if not dist_dir_path.exists():
	sys.stderr.write(f"DIST_DIR does not exist: {dist_dir}")
	sys.exit(1)

target_path = dist_dir_path / "main.dist"

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
			)
		else:
			copied_to = shutil.copy(src, target_path, follow_symlinks=False)
		sys.stdout.write(f"Copied {src} -> {copied_to}")
	except FileNotFoundError:
		sys.stderr.write(f"No such file: {src}")
		sys.exit(1)
	except PermissionError:
		sys.stderr.write(f"Cannot access file: {src}")
		sys.exit(1)
	except Exception as e:
		sys.stderr.write(f"Error copying file {src}: {e}")
		sys.exit(1)
