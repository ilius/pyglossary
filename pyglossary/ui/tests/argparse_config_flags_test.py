# -*- coding: utf-8 -*-
"""Tests for CLI config flags registered from ``configDefDict`` (e.g. ``--log-time``)."""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import unittest
from os.path import abspath, dirname, join
from unittest.mock import Mock

_here = abspath(dirname(__file__))
rootDir = abspath(join(_here, "..", "..", ".."))
sys.path.insert(0, rootDir)

from pyglossary.ui.argparse_main import configFromArgs, defineFlags

__all__ = [
	"TestBoolConfigFlags",
	"TestConfigFlagConflicts",
	"TestConfigFromArgs",
	"TestStrConfigFlags",
]

# config key, positive flag, negative flag
BOOL_PAIR_FLAGS: list[tuple[str, str, str]] = [
	("log_time", "--log-time", "--no-log-time"),
	("cleanup", "--cleanup", "--no-cleanup"),
	("enable_alts", "--alts", "--no-alts"),
	("lower", "--lower", "--no-lower"),
	("utf8_check", "--utf8-check", "--no-utf8-check"),
]

# config key, flag (store_true only)
BOOL_STORE_TRUE_FLAGS: list[tuple[str, str]] = [
	("skip_resources", "--skip-resources"),
	("save_info_json", "--info"),
	("rtl", "--rtl"),
	("remove_html_all", "--remove-html-all"),
	("normalize_html", "--normalize-html"),
	("skip_duplicate_headword", "--skip-duplicate-headword"),
	("trim_arabic_diacritics", "--trim-arabic-diacritics"),
	("unescape_word_links", "--unescape-word-links"),
]

# config key, flag, sample value
STR_FLAGS: list[tuple[str, str, str]] = [
	("remove_html", "--remove-html", "b,i"),
	("skip_term_regex", "--skip-term-regex", "foo.*"),
]


def _make_parser(config: dict | None = None) -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(add_help=False)
	defineFlags(parser, config or {})
	return parser


class TestBoolConfigFlags(unittest.TestCase):
	"""Bool config options with ``--flag`` / ``--no-flag`` or ``--flag`` only."""

	@classmethod
	def setUpClass(cls) -> None:
		cls.parser = _make_parser()

	def test_bool_pair_flags_set_namespace_and_config(self) -> None:
		log = Mock()
		for key, flag, no_flag in BOOL_PAIR_FLAGS:
			with self.subTest(key=key, flag=flag, value=True):
				args = self.parser.parse_args([flag])
				self.assertTrue(getattr(args, key))
				self.assertEqual(configFromArgs(args, log), {key: True})
			with self.subTest(key=key, flag=no_flag, value=False):
				args = self.parser.parse_args([no_flag])
				self.assertFalse(getattr(args, key))
				self.assertEqual(configFromArgs(args, log), {key: False})

	def test_bool_store_true_flags(self) -> None:
		log = Mock()
		for key, flag in BOOL_STORE_TRUE_FLAGS:
			with self.subTest(key=key, flag=flag):
				args = self.parser.parse_args([flag])
				self.assertTrue(getattr(args, key))
				self.assertEqual(configFromArgs(args, log), {key: True})
			with self.subTest(key=key, omitted=True):
				args = self.parser.parse_args([])
				self.assertIsNone(getattr(args, key, None))
				self.assertNotIn(key, configFromArgs(args, log))


class TestStrConfigFlags(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.parser = _make_parser()

	def test_str_flags_accept_values(self) -> None:
		log = Mock()
		for key, flag, value in STR_FLAGS:
			with self.subTest(key=key, flag=flag):
				args = self.parser.parse_args([flag, value])
				self.assertEqual(getattr(args, key), value)
				self.assertEqual(configFromArgs(args, log), {key: value})


class TestConfigFlagConflicts(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.parser = _make_parser()

	def test_conflicting_bool_pair_exits(self) -> None:
		with contextlib.redirect_stderr(io.StringIO()):
			with self.assertRaises(SystemExit):
				self.parser.parse_args(["--log-time", "--no-log-time"])

	def test_duplicate_positive_bool_pair_exits(self) -> None:
		with contextlib.redirect_stderr(io.StringIO()):
			with self.assertRaises(SystemExit):
				self.parser.parse_args(["--log-time", "--log-time"])


class TestConfigFromArgs(unittest.TestCase):
	def test_omits_unset_flags(self) -> None:
		parser = _make_parser()
		args = parser.parse_args([])
		self.assertEqual(configFromArgs(args, Mock()), {})


if __name__ == "__main__":
	unittest.main()
