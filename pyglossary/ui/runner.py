from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from pyglossary import core
from pyglossary.glossary_v2 import Error
from pyglossary.ui.base import UIBase

if TYPE_CHECKING:
	import argparse
	import logging
	from collections.abc import Callable
	from typing import Any


ui_list = ["gtk", "gtk4", "tk", "web"]
if os.sep == "\\":
	ui_list = ["tk", "gtk", "gtk4", "web"]

log: logging.Logger | None = None


def canRunGUI() -> bool:
	if core.sysName == "linux":
		return bool(os.getenv("DISPLAY"))

	if core.sysName == "darwin":
		try:
			import tkinter  # noqa: F401
		except ModuleNotFoundError:
			return False

	return True


def shouldUseCMD(args: argparse.Namespace) -> bool:
	if not canRunGUI():
		return True
	if args.interactive:
		return True
	return bool(args.inputFilename and args.outputFilename)


def base_ui_run(  # noqa: PLR0913
	inputFilename: str = "",
	outputFilename: str = "",
	inputFormat: str = "",
	outputFormat: str = "",
	reverse: bool = False,
	config: dict[str, Any] | None = None,
	readOptions: dict[str, Any] | None = None,
	writeOptions: dict[str, Any] | None = None,
	convertOptions: dict[str, Any] | None = None,
	glossarySetAttrs: dict[str, Any] | None = None,
) -> bool:
	from pyglossary.glossary_v2 import ConvertArgs, Glossary

	assert log
	if reverse:
		log.error("--reverse does not work with --ui=none")
		return False
	ui = UIBase(progressbar=False)
	ui.loadConfig(**config)
	glos = Glossary(ui=ui)
	glos.config = ui.config
	glos.progressbar = False
	if glossarySetAttrs:
		for attr, value in glossarySetAttrs.items():
			setattr(glos, attr, value)
	try:
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				inputFormat=inputFormat,
				outputFormat=outputFormat,
				readOptions=readOptions,
				writeOptions=writeOptions,
				**convertOptions,
			),
		)
	except Error as e:
		log.critical(str(e))
		glos.cleanup()
		return False
	return True


def getRunner(
	args: argparse.Namespace,
	ui_type: str,
	logArg: logging.Logger,
) -> Callable | None:
	global log
	log = logArg

	if ui_type == "none":
		return base_ui_run

	if ui_type == "auto" and shouldUseCMD(args):
		ui_type = "cmd"

	uiArgs = {
		"progressbar": args.progressbar is not False,
	}

	if ui_type == "cmd":
		if args.interactive:
			from pyglossary.ui.ui_cmd_interactive import UI
		elif args.inputFilename and args.outputFilename:
			from pyglossary.ui.ui_cmd import UI
		elif not args.no_interactive:
			from pyglossary.ui.ui_cmd_interactive import UI
		else:
			log.error("no input file given, try --help")
			return None
		return UI(**uiArgs).run

	if ui_type == "auto":
		if not args.no_interactive and sys.stdin.isatty():
			ui_list.insert(3, "cmd_interactive")
		log.debug(f"{ui_list = }")

		for ui_type2 in ui_list:
			try:
				ui_module = __import__(
					f"pyglossary.ui.ui_{ui_type2}",
					fromlist=f"ui_{ui_type2}",
				)
			except ImportError as e:  # noqa: PERF203
				log.error(str(e))
			else:
				return ui_module.UI(**uiArgs).run
		log.error(
			"no user interface module found! "
			f'try "{sys.argv[0]} -h" to see command line usage',
		)
		return None

	ui_module = __import__(
		f"pyglossary.ui.ui_{ui_type}",
		fromlist=f"ui_{ui_type}",
	)
	return ui_module.UI(**uiArgs).run
