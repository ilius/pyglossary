"""
ANSI color escape helpers for PyGlossary CLI tools.

Defines foreground/background wrappers used by ``diff_glossary``,
``view_glossary``, and interactive terminal UIs.
"""

__all__ = ["green", "red", "reset", "yellow"]

redCode = 1
greenCode = 2
yellowCode = 3
red = f"\x1b[38;5;{redCode}m"
green = f"\x1b[38;5;{greenCode}m"
yellow = f"\x1b[38;5;{yellowCode}m"
reset = "\x1b[0;0;0m"
