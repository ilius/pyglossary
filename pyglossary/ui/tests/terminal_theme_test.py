# -*- coding: utf-8 -*-
"""Tests for :mod:`pyglossary.ui.terminal_theme`."""

from __future__ import annotations

import sys
import unittest
from os.path import abspath, dirname, join
from unittest.mock import patch

_here = abspath(dirname(__file__))
rootDir = abspath(join(_here, "..", "..", ".."))
sys.path.insert(0, rootDir)

from pyglossary.ui import terminal_theme as tt


class TestParseOsc11Background(unittest.TestCase):
	def test_rgb_four_hex_digits(self) -> None:
		raw = b"\x1b]11;rgb:ffff/ffff/ffff\x1b\\"
		self.assertEqual(tt.parse_osc11_background(raw), (255, 255, 255))

	def test_rgb_dark(self) -> None:
		raw = b"\x1b]11;rgb:1e1e/1e1e/1e1e\x07"
		self.assertEqual(tt.parse_osc11_background(raw), (30, 30, 30))

	def test_hash_form(self) -> None:
		raw = b"\x1b]11;#aabbcc\x1b\\"
		self.assertEqual(tt.parse_osc11_background(raw), (0xAA, 0xBB, 0xCC))

	def test_rgba_prefix(self) -> None:
		raw = b"\x1b]11;rgba:ffff/ffff/ffff/ffff\x1b\\"
		self.assertEqual(tt.parse_osc11_background(raw), (255, 255, 255))

	def test_no_sequence(self) -> None:
		self.assertIsNone(tt.parse_osc11_background(b"noise"))


class TestLightBackgroundHeuristics(unittest.TestCase):
	def tearDown(self) -> None:
		tt.reset_terminal_theme_cache()

	def test_colorfgbg_white_bg(self) -> None:
		with patch.object(tt, "_query_osc11_rgb", return_value=None):
			with patch.dict("os.environ", {"COLORFGBG": "0;15"}, clear=False):
				tt.reset_terminal_theme_cache()
				self.assertTrue(tt.is_light_terminal_background())

	def test_colorfgbg_black_bg(self) -> None:
		with patch.object(tt, "_query_osc11_rgb", return_value=None):
			with patch.dict("os.environ", {"COLORFGBG": "15;0"}, clear=False):
				tt.reset_terminal_theme_cache()
				self.assertFalse(tt.is_light_terminal_background())

	def test_osc_white_is_light(self) -> None:
		with patch.object(tt, "_query_osc11_rgb", return_value=(255, 255, 255)):
			tt.reset_terminal_theme_cache()
			self.assertTrue(tt.is_light_terminal_background())

	def test_osc_dark_is_not_light(self) -> None:
		with patch.object(tt, "_query_osc11_rgb", return_value=(20, 24, 28)):
			tt.reset_terminal_theme_cache()
			self.assertFalse(tt.is_light_terminal_background())


class TestAdaptForeground(unittest.TestCase):
	def test_bright_color_darkened_on_light(self) -> None:
		r, g, b = tt.adapt_rgb_for_light_background(85, 255, 85)
		self.assertLess(tt.relative_luminance_srgb(r, g, b), 0.4)

	def test_already_dark_unchanged(self) -> None:
		self.assertEqual(tt.adapt_rgb_for_light_background(0, 85, 0), (0, 85, 0))

	def test_hex_fg_uses_truecolor_palette_when_not_light(self) -> None:
		self.assertEqual(tt.hex_fg_for_palette_code(2, False), "#00aa00")

	def test_hex_fg_darkens_when_light(self) -> None:
		h = tt.hex_fg_for_palette_code(10, True)
		self.assertTrue(h.startswith("#"))
		self.assertNotEqual(h, tt.hex_fg_for_palette_code(10, False))
