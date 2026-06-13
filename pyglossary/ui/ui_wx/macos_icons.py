# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import logging
import sys
from pathlib import Path

log = logging.getLogger("pyglossary")

__all__ = ["configure_macos_dock_icon"]


def configure_macos_dock_icon(logo_path: str) -> None:
	"""Replace the Dock icon when PyGlossary is run as ``python …`` (no .app bundle)."""
	if sys.platform != "darwin":
		return
	lp = Path(logo_path).expanduser().resolve()
	if not lp.is_file():
		return

	try:
		from AppKit import NSApplication, NSImage  # noqa: PLC0415
	except ImportError:
		log.debug(
			"macOS Dock icon: pip install pyobjc-framework-Cocoa (included in "
			"optional extra pip install pyglossary[wx] on Darwin).",
		)
		return

	img = NSImage.alloc().initWithContentsOfFile_(str(lp))
	if img is None:
		log.debug("Dock icon: failed to load %s via NSImage", lp)
		return

	app = NSApplication.sharedApplication()
	if app is None:
		return
	app.setApplicationIconImage_(img)
