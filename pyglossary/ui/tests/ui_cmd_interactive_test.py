# -*- coding: utf-8 -*-
"""Tests for interactive cmd UI: ``ConversionSession``, ``InteractivePrompt``, ``UI``."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from os.path import abspath, dirname, join
from unittest.mock import Mock, patch

_here = abspath(dirname(__file__))
rootDir = abspath(join(_here, "..", "..", ".."))
sys.path.insert(0, rootDir)

from prompt_toolkit.completion import WordCompleter

from pyglossary.glossary_v2 import Glossary
from pyglossary.option import Option
from pyglossary.ui.tests.logging_helpers import silence_pyglossary_log
from pyglossary.ui.ui_cmd_interactive.conversion_session import ConversionSession
from pyglossary.ui.ui_cmd_interactive.interactive_prompt import InteractivePrompt
from pyglossary.ui.ui_cmd_interactive.ui import UI


class TestConversionSession(unittest.TestCase):
	def test_get_run_kwargs_matches_ui_cmd_contract(self) -> None:
		s = ConversionSession()
		cfg = {"log_time": False}
		empty = s.get_run_kwargs(cfg)
		self.assertEqual(
			set(empty),
			{
				"inputFilename",
				"outputFilename",
				"inputFormat",
				"outputFormat",
				"config",
				"readOptions",
				"writeOptions",
				"convertOptions",
				"glossarySetAttrs",
			},
		)
		self.assertIs(empty["config"], cfg)

		s.inputFilename = "/in.txt"
		s.outputFilename = "/out.txt"
		s.inputFormat = "Tabfile"
		s.outputFormat = "Stardict"
		s.readOptions = {"a": 1}
		s.writeOptions = {"b": 2}
		s.convertOptions = {"sort": True}
		s.glossarySetAttrs = {"progressbar": False}
		self.assertEqual(
			s.get_run_kwargs(cfg),
			{
				"inputFilename": "/in.txt",
				"outputFilename": "/out.txt",
				"inputFormat": "Tabfile",
				"outputFormat": "Stardict",
				"config": cfg,
				"readOptions": {"a": 1},
				"writeOptions": {"b": 2},
				"convertOptions": {"sort": True},
				"glossarySetAttrs": {"progressbar": False},
			},
		)


class TestInteractivePrompt(unittest.TestCase):
	"""Prompt appearance (``cmdi.*``) and plain-text mode without ANSI."""

	def test_config_and_plain_prompt_message(self) -> None:
		p = InteractivePrompt()
		p.apply_config(
			{
				"cmdi.prompt.indent.str": ">>",
				"cmdi.prompt.indent.color": 5,
				"cmdi.prompt.msg.color": 3,
				"cmdi.msg.color": 7,
			},
		)
		with patch(
			"pyglossary.ui.ui_cmd_interactive.interactive_prompt.noColor",
			True,
		):
			text, colored = p.formatPromptMsg(2, "Hello", ":")
		self.assertFalse(colored)
		self.assertTrue(text.rstrip().endswith("Hello:"))
		self.assertIn(">>", text)


class TestUICmdInteractive(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		Glossary.init()

	def test_resolves_plugin_by_format_name(self) -> None:
		name = Glossary.readFormats[0]
		plugin = UI.pluginByNameOrDesc(name)
		self.assertIsNotNone(plugin)
		self.assertEqual(plugin.name, name)

	def test_unknown_format_returns_none(self) -> None:
		with silence_pyglossary_log():
			self.assertIsNone(UI.pluginByNameOrDesc("__no_such_format__"))

	def test_bounded_options_get_word_completer(self) -> None:
		ui = UI()
		opt = Option(typ="str", values=["a", "b"])
		self.assertEqual(UI.getOptionValueSuggestValues(opt), ["a", "b"])
		self.assertIsInstance(ui.getOptionValueCompleter(opt), WordCompleter)
		loose = Option(typ="str", values=None)
		self.assertIsNone(ui.getOptionValueCompleter(loose))

	def test_convert_mode_menu_updates_session(self) -> None:
		buf = io.StringIO()
		with contextlib.redirect_stdout(buf):
			ui = UI()
			ui.setIndirect()
			self.assertEqual(ui._session.convertOptions.get("direct"), False)
			self.assertIsNone(ui._session.convertOptions.get("sqlite"))
			ui.setSQLite()
			self.assertIsNone(ui._session.convertOptions.get("direct"))
			self.assertTrue(ui._session.convertOptions.get("sqlite"))

	def test_detect_input_format_when_file_matches(self) -> None:
		ui = UI()
		read_fmt = Glossary.readFormats[0]
		ext = Glossary.plugins[read_fmt].extensions[0]
		with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
			path = tmp.name
		try:
			ui._session.inputFilename = path
			with patch.object(
				Glossary,
				"detectInputFormat",
				return_value=Mock(formatName=read_fmt),
			) as det:
				ui.checkInputFormat(forceAsk=False)
				det.assert_called_once_with(path)
			self.assertEqual(ui._session.inputFormat, read_fmt)
		finally:
			os.unlink(path)

	def test_prints_repeatable_cli_command(self) -> None:
		ui = UI()
		ui.savedConfig = {}
		ui.config = {}
		in_fmt = Glossary.readFormats[0]
		out_fmt = Glossary.writeFormats[0]
		ui._session.inputFilename = "/tmp/in"
		ui._session.outputFilename = "/tmp/out"
		ui._session.inputFormat = in_fmt
		ui._session.outputFormat = out_fmt
		buf = io.StringIO()
		with contextlib.redirect_stdout(buf):
			ui.printNonInteractiveCommand()
		out = buf.getvalue()
		self.assertIn("pyglossary", out)
		self.assertIn(f"--read-format={in_fmt}", out)
		self.assertIn(f"--write-format={out_fmt}", out)


if __name__ == "__main__":
	unittest.main()
