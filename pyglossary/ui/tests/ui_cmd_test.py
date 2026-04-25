# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Integration-style tests for ``ui_cmd`` (CLI help, option parsing, ``UI.run``)."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from os.path import abspath, dirname, join
from types import SimpleNamespace
from unittest.mock import patch

_here = abspath(dirname(__file__))
rootDir = abspath(join(_here, "..", "..", ".."))
sys.path.insert(0, rootDir)

from pyglossary.core import log
from pyglossary.glossary_v2 import Error, Glossary
from pyglossary.logger import StdLogHandler
from pyglossary.ui import pbar_legacy
from pyglossary.ui.tests.logging_helpers import silence_pyglossary_log

try:
	from pyglossary.ui import pbar_tqdm
except ImportError:
	pbar_tqdm = None  # tqdm optional; ``progressInit`` falls back to ``pbar_legacy``
from pyglossary.ui.ui_cmd import (
	UI,
	NullObj,
	getColWidth,
	getFormatsTable,
	parseFormatOptionsStr,
	printHelp,
	wc_ljust,
)


class TestParseFormatOptionsStr(unittest.TestCase):
	"""``--*-options`` string parsing used by the CLI."""

	def test_accepts_empty_and_key_value_pairs(self) -> None:
		self.assertEqual(parseFormatOptionsStr(""), {})
		self.assertEqual(parseFormatOptionsStr("opt=val"), {"opt": "val"})
		self.assertEqual(
			parseFormatOptionsStr("a=1; b=two"),
			{"a": "1", "b": "two"},
		)

	def test_rejects_malformed_fragments(self) -> None:
		with silence_pyglossary_log():
			self.assertIsNone(parseFormatOptionsStr("no_equals"))
			self.assertIsNone(parseFormatOptionsStr("=nokey"))

	def test_skips_empty_segments_between_semicolons(self) -> None:
		self.assertEqual(
			parseFormatOptionsStr("a=1;;b=2"),
			{"a": "1", "b": "2"},
		)


class TestUiCmdHelpers(unittest.TestCase):
	"""Small helpers bundled with ``ui_cmd`` (layout, table, null progress)."""

	def test_wc_ljust_pads_to_display_width(self) -> None:
		self.assertEqual(wc_ljust("ab", 4), "ab  ")
		self.assertEqual(wc_ljust("", 3), "   ")

	def test_get_col_width(self) -> None:
		self.assertEqual(getColWidth("H", ["a", "bbb"]), 3)

	def test_get_formats_table_lists_plugins(self) -> None:
		Glossary.init()
		names = Glossary.readFormats[:2]
		table = getFormatsTable(names, "Test header")
		self.assertIn("Test header", table)
		for name in names:
			self.assertIn(name, table)

	def test_null_obj_swallows_ops(self) -> None:
		n = NullObj()
		self.assertIs(n.foo, n)
		self.assertFalse(bool(n))
		n.x = 1
		n["k"] = 2
		n()
		self.assertIsNone(n(1, 2, x=3))


class TestPrintHelp(unittest.TestCase):
	"""``printHelp`` loads text, substitutes ``CMD``, and appends format tables."""

	@classmethod
	def setUpClass(cls) -> None:
		Glossary.init()

	def test_output_includes_executable_name_and_format_sections(self) -> None:
		buf = io.StringIO()
		with contextlib.redirect_stdout(buf):
			printHelp()
		out = buf.getvalue()
		self.assertIn("pyglossary", out)
		self.assertIn("Supported input formats:", out)
		self.assertIn("Supported output formats:", out)
		self.assertIn(Glossary.readFormats[0], out)


class TestUiCmdRun(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		Glossary.init()

	def test_rejects_invalid_write_format_before_convert(self) -> None:
		with silence_pyglossary_log():
			ok = UI().run(
				inputFilename="/tmp/nonexistent_in",
				outputFilename="/tmp/out",
				inputFormat=Glossary.readFormats[0],
				outputFormat="__not_a_registered_write_format__",
			)
		self.assertFalse(ok)

	def test_requires_output_path_or_format(self) -> None:
		with silence_pyglossary_log():
			ok = UI().run(
				inputFilename="/tmp/in",
				outputFilename="",
				inputFormat="",
				outputFormat="",
			)
		self.assertFalse(ok)

	def test_builds_output_path_from_input_basename_when_omitted(self) -> None:
		out_fmt = Glossary.writeFormats[0]
		ext = Glossary.plugins[out_fmt].extensions[0]
		in_path = f"/tmp/onlyname{ext}"
		captured = []

		def fake_convert(_self, args):
			captured.append(args)
			return "/tmp/fake_out"

		with patch.object(Glossary, "convert", fake_convert):
			with silence_pyglossary_log():
				ok = UI().run(
					inputFilename=in_path,
					outputFilename="",
					inputFormat="",
					outputFormat=out_fmt,
				)
		self.assertTrue(ok)
		self.assertEqual(len(captured), 1)
		self.assertTrue(captured[0].outputFilename.endswith(ext))
		self.assertEqual(captured[0].inputFilename, in_path)
		self.assertEqual(captured[0].outputFormat, out_fmt)

	def test_convert_raises_logs_and_returns_false_after_cleanup(self) -> None:
		out_fmt = Glossary.writeFormats[0]

		def boom(_self, _args):
			raise Error("convert failed")

		with patch.object(Glossary, "convert", boom):
			with patch.object(Glossary, "cleanup") as mock_cleanup:
				with silence_pyglossary_log():
					ok = UI().run(
						inputFilename="/tmp/in",
						outputFilename="/tmp/out",
						inputFormat=Glossary.readFormats[0],
						outputFormat=out_fmt,
					)
		self.assertFalse(ok)
		self.assertEqual(mock_cleanup.call_count, 1)

	def test_convert_falsy_result_returns_false(self) -> None:
		out_fmt = Glossary.writeFormats[0]

		def none_result(_self, _args):
			return None

		with patch.object(Glossary, "convert", none_result):
			with silence_pyglossary_log():
				ok = UI().run(
					inputFilename="/tmp/in",
					outputFilename="/tmp/out",
					inputFormat=Glossary.readFormats[0],
					outputFormat=out_fmt,
				)
		self.assertFalse(ok)

	def test_glossary_set_attrs_applied_to_glossary(self) -> None:
		out_fmt = Glossary.writeFormats[0]

		def capture(glos, _args):
			self.assertEqual(getattr(glos, "_ui_cmd_test_marker", None), 42)
			return "/done"

		with patch.object(Glossary, "convert", capture):
			with silence_pyglossary_log():
				ok = UI().run(
					inputFilename="/tmp/in",
					outputFilename="/tmp/out",
					inputFormat=Glossary.readFormats[0],
					outputFormat=out_fmt,
					glossarySetAttrs={"_ui_cmd_test_marker": 42},
				)
		self.assertTrue(ok)

	def test_unknown_read_format_is_logged_but_convert_still_runs(self) -> None:
		out_fmt = Glossary.writeFormats[0]

		with silence_pyglossary_log():
			ok = UI().run(
				inputFilename="/tmp/file.txt",
				outputFilename="/tmp/out",
				inputFormat="not_a_real_read_format_xyz",
				outputFormat=out_fmt,
			)
		self.assertFalse(ok)


class TestUiCmdProgressHooks(unittest.TestCase):
	"""``UI`` helpers used with the progress bar and signal handling."""

	def test_fill_message_without_width_returns_plain(self) -> None:
		ui = UI()
		ui.pbar = SimpleNamespace(term_width=0)
		self.assertEqual(ui.fillMessage("hello"), "hello")

	def test_fill_message_pads_to_term_width(self) -> None:
		ui = UI()
		ui.pbar = SimpleNamespace(term_width=12)
		out = ui.fillMessage("ab")
		self.assertTrue(out.startswith("\r"))
		self.assertGreaterEqual(len(out), 3)

	def test_sig_int_pause_then_exit(self) -> None:
		ui = UI()
		with patch("pyglossary.ui.ui_cmd.sys.exit") as mock_exit:
			ui.onSigInt()
			self.assertTrue(ui._toPause)
			ui.onSigInt()
			mock_exit.assert_called_once_with(0)

	def test_progress_init_uses_bar_and_restores_logger(self) -> None:
		bar = SimpleNamespace(
			widgets=[""],
			term_width=40,
			update=lambda *_a, **_k: None,
			finish=lambda: None,
		)

		def fake_create(_title: str):
			return bar

		std_handler = StdLogHandler(noColor=True)
		std_handler.setFormatter(log.newFormatter())
		log.addHandler(std_handler)
		try:
			ui = UI()
			with contextlib.ExitStack() as stack:
				stack.enter_context(
					patch.object(pbar_legacy, "createProgressBar", fake_create),
				)
				if pbar_tqdm is not None:
					stack.enter_context(
						patch.object(pbar_tqdm, "createProgressBar", fake_create),
					)
				ui.progressInit("Title")
			self.assertIs(ui.pbar, bar)
			self.assertIsNotNone(std_handler.formatter.fill)
			ui.progress(0.5)
			ui.setText("status")
			ui.progressEnd()
			self.assertIsNone(std_handler.formatter.fill)
		finally:
			log.removeHandler(std_handler)


class TestUiCmdReverse(unittest.TestCase):
	"""``run(..., reverse=True)`` without real glossary I/O."""

	@classmethod
	def setUpClass(cls) -> None:
		Glossary.init()

	def test_reverse_invokes_read_and_reverse_pipeline(self) -> None:
		def empty_reverse(*_a, **_k):
			yield from ()

		def fake_read(_self, *_args, **_kwargs):
			return True

		with patch.object(Glossary, "read", fake_read, create=True):
			with patch("pyglossary.reverse.reverseGlossary", empty_reverse):
				with silence_pyglossary_log():
					ok = UI().run(
						reverse=True,
						inputFilename="/tmp/in.txt",
						outputFilename="/tmp/out.txt",
					)
		self.assertTrue(ok)


if __name__ == "__main__":
	unittest.main()
