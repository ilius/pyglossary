import os
import subprocess
import sys

icuTag = "v2.16.0"
icuFileVersion = "2.16"
lzoVer = "1.16"

icuDownload = "https://github.com/cgohlke/pyicu-build/releases/download"
lzoDownload = "https://github.com/ilius/python-lzo/releases/download"

# pyVer: for example "313" for 3.13
pyVer = f"{sys.version_info.major}{sys.version_info.minor}"

# pyVerSuffix: for example "cp313-cp313"
pyVerSuffix = f"cp{pyVer}-cp{pyVer}"


def install(*args: str) -> None:
	cmd = [sys.executable, "-m", "pip", "install"]
	if not os.getenv("VIRTUAL_ENV"):
		cmd.append("--user")
	subprocess.check_call([*cmd, *args])


install(
	f"{icuDownload}/{icuTag}/PyICU-{icuFileVersion}-{pyVerSuffix}-win_amd64.whl",
)

install(
	f"{lzoDownload}/v{lzoVer}/python_lzo-{lzoVer}-{pyVerSuffix}-win_amd64.whl",
)

install("-r", "requirements.txt")

default_ui = os.getenv("DEFAULT_UI", "tk")
if default_ui == "wx":
	install("wxPython")
elif default_ui == "slint":
	slintVer = os.getenv("SLINT_VERSION", "1.17.0b2")
	install("--pre", f"slint=={slintVer}")
else:
	# Tk wizard: drag-and-drop from Explorer (see pyglossary/ui/ui_tk_wizard.py)
	install("tkinterdnd2")
