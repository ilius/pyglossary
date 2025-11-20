# [PyICU](https://pyicu.org)

## Installation on Linux

- Debian `sudo apt-get install python3-icu`
- Ubuntu: `sudo apt install pyicu`
- openSUSE: `sudo zypper install python3-PyICU`
- Fedora: `sudo dnf install python3-pyicu`
- Other distros:
  - Install [ICU](https://icu.unicode.org/)
  - Run `sudo pip3 install PyICU` or `pip3 install PyICU --user`

## Installation on Android with Termux

- Run `pkg install libicu`
- Run `pip install PyICU`

## Installation on Mac OS

```sh
brew install pkg-config icu4c
export PATH="$(brew --prefix)/opt/icu4c/bin:$(brew --prefix)/opt/icu4c/sbin:$PATH"
export PKG_CONFIG_PATH="$PKG_CONFIG_PATH:/usr/local/opt/icu4c/lib/pkgconfig"
# ensure system clang is used for proper libstdc++
# https://github.com/ovalhub/pyicu/issues/5#issuecomment-291631507
unset CC CXX
python3 -m pip install PyICU
```

## Installation on Windows

- Open https://github.com/cgohlke/pyicu-build/releases

- Download latest file that matches your system:

  - `cp313` for Python 3.13, `cp312` for Python 3.12, etc.
  - `win_amd64` for Windows 64-bit, `win32` for Windows 32-bit.

  For example:

  - `pyicu-2.16-cp313-cp313-win_amd64.whl` for 64-bit with Python 3.13

- Open Start -> type Command -> right-click on Command Prompt -> Run as administrator

- Type `pip install `

  then drag-and-drop downloaded file into Command Prompt and press Enter.
