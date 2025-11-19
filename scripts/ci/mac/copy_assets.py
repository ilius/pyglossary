#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path

dist_dir = os.getenv("DIST_DIR")
app_name = os.getenv("APPNAME")


if not dist_dir or not app_name:
	sys.stderr.write("missing env vars!\n")
	sys.exit(1)

dist_path = Path(dist_dir)

target_path: Path = dist_path / f"{app_name}.app/Contents/MacOS"
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
	sys.stderr.write(f"target_path not found {target_path.absolute()}\n")
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
	except FileNotFoundError as e:
		sys.stderr.write(f"source not found {src.absolute()}: {e!s}\n")
	except PermissionError as e:
		sys.stderr.write(f"permission error copying {src.absolute()}: {e!s}\n")
	except Exception as e:
		sys.stderr.write(f"error copying: {src.absolute()}: {e!s}\n")
