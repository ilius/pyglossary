import subprocess
import sys

icuVer = "2.15"
lzoVer = "1.16"

icuDownload = "https://github.com/cgohlke/pyicu-build/releases/download"
lzoDownload = "https://github.com/ilius/python-lzo/releases/download"

# pyVer: for example "313" for 3.13
pyVer = f"{sys.version_info.major}{sys.version_info.minor}"

# pyVerSuffix: for example "cp313-cp313"
pyVerSuffix = f"cp{pyVer}-cp{pyVer}"


def install(*args: str) -> None:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", *args])


install(
	f"{icuDownload}/v{icuVer}/PyICU-{icuVer}-{pyVerSuffix}-win_amd64.whl",
)

install(
	f"{lzoDownload}/v{lzoVer}/python_lzo-{lzoVer}-{pyVerSuffix}-win_amd64.whl",
)

install("-r", "requirements.txt")
