# [PyICU](https://pyicu.org)

Installation on Linux
---------------------
- Debian/Ubuntu: `sudo apt install pyicu`
- openSUSE: `sudo zypper install python3-PyICU`
- Fedora: `sudo dnf install python3-pyicu`
- Other distros:
	+ Install [ICU](http://site.icu-project.org/) >= 4.8
	+ Run `sudo pip3 install PyICU` or `pip3 install PyICU --user`


Installation on Android with Termux
---------------------
- Run `pkg install libicu`
- Run `pip install PyICU`


Installation on Windows
---------------------
- Open https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyicu
- Download latest file that matches your system:
	+ `cp39` for Python 3.9, `cp38` for Python 3.8, etc.
	+ `win_amd64` for Windows 64-bit, `win32` for Windows 32-bit.

	For example:
	+ `PyICU‑2.6‑cp39‑cp39‑win_amd64.whl` for 64-bit with Python 3.9
	+ `PyICU‑2.6‑cp39‑cp39‑win32.whl` for 32-bit with Python 3.9

- Open Start -> type Command -> right-click on Command Prompt -> Run as administrator
- Type `pip install `

	then drag-and-drop downloaded file into Command Prompt and press Enter.

