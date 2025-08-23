#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys
import os

dist_dir = os.getenv("DIST_DIR")
app_name = os.getenv("APPNAME")


if not dist_dir or not app_name:
    print('missing env vars')
    sys.exit(1)

dist_path = Path(dist_dir)
print(f'DIST_DIR={dist_path}, APPNAME={app_name}')

target_path = dist_path / f"{app_name}.app/Contents/MacOS"
sources = ["about", "AUTHORS", "_license-dialog", "config.json", "plugins-meta", "help", "res", "pyglossary"]

if not target_path.exists():
    print(f'missing target dir {target_path.absolute()}')
    sys.exit(1)

for source in sources:
    src = Path(source)
    try:
        if src.is_dir():
            copied_to = shutil.copytree(src, target_path / src.name, dirs_exist_ok=True, symlinks=True,
                                        ignore_dangling_symlinks=True)
        else:
            copied_to = shutil.copy(src, target_path, follow_symlinks=False)
        print(f"Copied {src} -> {copied_to}")
    except FileNotFoundError:
        print(f"Missing {src}")
    except PermissionError:
        print(f"No access {src}")
    except Exception as e:
        print(f"Failed {src}: {e}")
print("Done")