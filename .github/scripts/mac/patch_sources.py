#!/usr/bin/env python3

import os
import sys
from pathlib import Path

main_script, app_name = os.getenv("MAIN_SCRIPT"), os.getenv("APPNAME")
python_version = sys.argv[1]

if not (main_script and app_name):
    raise SystemExit("Missing env vars")

Path(f"{app_name}.py").write_bytes(Path(main_script).read_bytes())
Path("__init__.py").unlink(missing_ok=True)

arg_main = Path('pyglossary/ui/argparse_main.py')
arg_main.write_text(arg_main.read_text().replace('default="auto"', 'default="tk"'))

plugin_path = Path(
    ".venv") / "lib" / f"python{python_version}" / "site-packages" / "nuitka" / "plugins" / "standard" / "TkinterPlugin.py"

if plugin_path.exists():
    content = plugin_path.read_text(encoding="utf-8")
    if '("8.5", "8.6")' in content:
        plugin_path.write_text(
            content.replace('("8.5", "8.6")', '("8.5", "8.6", "9.0")'),
            encoding="utf-8"
        )
        print("TkinterPlugin.py updated for Tk 9.0 compatibility")
    else:
        print("TkinterPlugin.py already compatible or pattern not found")
else:
    print(f"{plugin_path} not found")
