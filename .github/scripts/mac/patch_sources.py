#!/usr/bin/env python3

import os
from pathlib import Path

main_script, app_name = os.getenv("MAIN_SCRIPT"), os.getenv("APPNAME")

if not (main_script and app_name):
	raise SystemExit("Missing env vars")

Path(f"{app_name}.py").write_bytes(Path(main_script).read_bytes())
Path("__init__.py").unlink(missing_ok=True)

arg_main = Path("pyglossary/ui/argparse_main.py")
arg_main.write_text(
	arg_main.read_text(encoding="utf-8").replace('default="auto"', 'default="tk"'),
	encoding="utf-8",
)
