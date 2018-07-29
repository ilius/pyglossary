# Overview

Convert CC-CEDICT into a pleasantly-formatted dictionary!

# Dependencies

- Python 3
- Jinja2 (installed as a Python 3 library)
- [PyGlossary](https://github.com/ilius/pyglossary)
- Optionally, `dictzip` (might be part of `dictd` on your OS)

# Usage

This is a PyGlossary plugin. To use it, simply clone this repository as a
subdirectory of the PyGlossary plugins directory and use PyGlossary normally
with this plugin and an (unzipped) copy of CC-CEDICT as the input. You can find
the plugins directory at `~/.pyglossary/plugins/` on Unices,
`~/Library/Preferences/PyGlossary/plugins/` on macOS, and
`%APPDATA%\PyGlossary\plugins\` on Windows.

For StarDict/GoldenDict, at least, compressing the output dictionary seems to
take a long time, so be patient—PyGlossary hasn't crashed. It may take up to 10
minutes—I don't know whether my case is representative. This is probably an
issue with something in the output logic, not with this plugin.

# License

`jinja2htmlcompress.py` is subject to the license in `LICENSE2` (BSD 3-clause).
Everything else is subject to the license in `LICENSE` (GPLv3).

