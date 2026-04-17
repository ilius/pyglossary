# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

"""Detect light terminal backgrounds and adapt palette foregrounds for contrast."""

from __future__ import annotations

import os
import sys
import time
from typing import Final

from pyglossary.ui.termcolors import colors

__all__ = [
	"adapt_rgb_for_light_background",
	"ansi_fg_open_for_palette_code",
	"hex_fg_for_palette_code",
	"is_light_terminal_background",
	"parse_osc11_background",
	"relative_luminance_srgb",
	"reset_terminal_theme_cache",
]

_LIGHT_BG_LUM_THRESHOLD: Final = 0.52
_osc_query_timeout_s: Final = 0.12

_light_bg_cache: bool | None = None


def reset_terminal_theme_cache() -> None:
	"""Clear cached :func:`is_light_terminal_background` result (for tests)."""
	global _light_bg_cache
	_light_bg_cache = None


def relative_luminance_srgb(r: int, g: int, b: int) -> float:
	"""WCAG 2.x relative luminance for 8-bit sRGB channels."""
	channel = (r / 255.0, g / 255.0, b / 255.0)

	def lin(u: float) -> float:
		return u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4

	R, G, B = lin(channel[0]), lin(channel[1]), lin(channel[2])
	return 0.2126 * R + 0.7152 * G + 0.0722 * B


def parse_osc11_background(data: bytes) -> tuple[int, int, int] | None:
	"""
	Parse RGB from a host reply to an OSC 11 query (default background).

	Supports common ``rgb:``/``rgba:`` (4/8/12 hex digits per channel) and ``#rrggbb``.
	"""
	if b"]11;" not in data:
		return None
	i = data.index(b"]11;") + 4
	end = len(data)
	for j in range(i, len(data)):
		if data[j : j + 1] == b"\x07":
			end = j
			break
		if data[j : j + 2] == b"\033\\":
			end = j
			break
	payload = data[i:end].decode("latin-1", errors="ignore").strip()

	def channel_from_hex(h: str) -> int:
		h = h.strip()
		n = int(h, 16)
		if len(h) <= 2:
			return min(255, n)
		return min(255, int(n * 255 / 65535))

	if payload.startswith(("rgb:", "rgba:")):
		body = payload.split(":", 1)[1]
		parts = body.split("/")
		if len(parts) < 3:
			return None
		return (
			channel_from_hex(parts[0]),
			channel_from_hex(parts[1]),
			channel_from_hex(parts[2]),
		)

	if payload.startswith("#"):
		h = payload[1:7] if len(payload) >= 7 else ""
		if len(h) == 6:
			return (
				int(h[0:2], 16),
				int(h[2:4], 16),
				int(h[4:6], 16),
			)
	return None


def _query_osc11_rgb() -> tuple[int, int, int] | None:
	try:
		import select
		import termios
		import tty
	except ImportError:
		return None

	stdin = sys.stdin
	stdout = sys.stdout
	if not stdin.isatty() or not stdout.isatty():
		return None

	fd = stdin.fileno()
	try:
		old = termios.tcgetattr(fd)
	except (OSError, termios.error, AttributeError):
		return None

	buf = bytearray()
	try:
		tty.setcbreak(fd)
		stdout.write("\033]11;?\033\\")
		stdout.flush()
		deadline = time.monotonic() + _osc_query_timeout_s
		while time.monotonic() < deadline:
			remaining = deadline - time.monotonic()
			if remaining <= 0:
				break
			r, _, _ = select.select([fd], [], [], min(remaining, 0.05))
			if not r:
				continue
			chunk = os.read(fd, 4096)
			if not chunk:
				break
			buf.extend(chunk)
			if b"\x07" in buf or b"\033\\" in buf:
				break
	except (OSError, termios.error, ValueError):
		return None
	finally:
		try:
			termios.tcsetattr(fd, termios.TCSADRAIN, old)
		except OSError:
			pass

	return parse_osc11_background(bytes(buf))


def _colorfgbg_suggests_light_bg() -> bool | None:
	"""Interpret ``COLORFGBG`` when OSC 11 is unavailable (often ``fg;bg`` ANSI codes)."""
	val = os.environ.get("COLORFGBG")
	if not val:
		return None
	parts = val.split(";")
	if len(parts) < 2:
		return None
	try:
		bg = int(parts[1])
	except ValueError:
		return None
	if bg in (7, 15):
		return True
	if bg <= 6 or bg == 8:
		return False
	return None


def is_light_terminal_background() -> bool:
	"""
	Return True if the terminal default background appears light.

	Uses OSC 11 when supported, else ``COLORFGBG``. On failure or non-tty stdin,
	returns False so existing (dark-background) palette choices stay unchanged.
	"""
	global _light_bg_cache
	if _light_bg_cache is not None:
		return _light_bg_cache

	rgb = _query_osc11_rgb()
	if rgb is not None:
		lum = relative_luminance_srgb(*rgb)
		_light_bg_cache = lum >= _LIGHT_BG_LUM_THRESHOLD
		return _light_bg_cache

	cfb = _colorfgbg_suggests_light_bg()
	if cfb is not None:
		_light_bg_cache = cfb
		return _light_bg_cache

	_light_bg_cache = False
	return _light_bg_cache


def adapt_rgb_for_light_background(r: int, g: int, b: int) -> tuple[int, int, int]:
	"""Darken bright foreground RGB so it stays readable on a light background."""
	lum = relative_luminance_srgb(r, g, b)
	if lum <= 0.38:
		return r, g, b
	factor = min(0.88, 0.28 / max(lum, 0.06))
	nr = max(0, min(255, int(r * factor)))
	ng = max(0, min(255, int(g * factor)))
	nb = max(0, min(255, int(b * factor)))
	return nr, ng, nb


def ansi_fg_open_for_palette_code(code: int, light_bg: bool) -> str:
	"""Opening ANSI SGR for foreground (caller supplies reset)."""
	if not light_bg:
		return f"\x1b[38;5;{code}m"
	prop = colors[code]
	r, g, b = int(prop.rgb[0]), int(prop.rgb[1]), int(prop.rgb[2])
	r, g, b = adapt_rgb_for_light_background(r, g, b)
	return f"\x1b[38;2;{r};{g};{b}m"


def hex_fg_for_palette_code(code: int, light_bg: bool) -> str:
	"""``#rrggbb`` for prompt_toolkit ``fg:`` styles."""
	prop = colors[code]
	r, g, b = int(prop.rgb[0]), int(prop.rgb[1]), int(prop.rgb[2])
	if light_bg:
		r, g, b = adapt_rgb_for_light_background(r, g, b)
	return f"#{r:02x}{g:02x}{b:02x}"
