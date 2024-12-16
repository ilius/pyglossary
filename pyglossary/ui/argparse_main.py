from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from pyglossary.ui.base import UIBase
from pyglossary.ui.option_ui import registerConfigOption

if TYPE_CHECKING:
	import argparse
	import logging


def defineFlags(parser: argparse.ArgumentParser, config: dict[str, Any]):
	defaultHasColor = config.get(
		"color.enable.cmd.windows" if os.sep == "\\" else "color.enable.cmd.unix",
		True,
	)
	parser.add_argument(
		"-v",
		"--verbosity",
		action="store",
		dest="verbosity",
		type=int,
		choices=(0, 1, 2, 3, 4, 5),
		required=False,
		default=int(os.getenv("VERBOSITY", "3")),
	)

	parser.add_argument(
		"--version",
		action="store_true",
	)
	parser.add_argument(
		"-h",
		"--help",
		dest="help",
		action="store_true",
	)
	parser.add_argument(
		"-u",
		"--ui",
		dest="ui_type",
		default="auto",
		choices=(
			"cmd",
			"gtk",
			"gtk4",
			"tk",
			"web",
			# "qt",
			"auto",
			"none",
		),
	)
	parser.add_argument(
		"--cmd",
		dest="ui_type",
		action="store_const",
		const="cmd",
		default=None,
		help="use command-line user interface",
	)
	parser.add_argument(
		"--gtk",
		dest="ui_type",
		action="store_const",
		const="gtk",
		default=None,
		help="use Gtk-based user interface",
	)
	parser.add_argument(
		"--gtk4",
		dest="ui_type",
		action="store_const",
		const="gtk4",
		default=None,
		help="use Gtk4-based user interface",
	)
	parser.add_argument(
		"--tk",
		dest="ui_type",
		action="store_const",
		const="tk",
		default=None,
		help="use Tkinter-based user interface",
	)
	parser.add_argument(
		"--web",
		dest="ui_type",
		action="store_const",
		const="web",
		default=None,
		help="use web browser interface",
	)
	parser.add_argument(
		"--interactive",
		"--inter",
		dest="interactive",
		action="store_true",
		default=None,
		help="switch to interactive command line interface",
	)
	parser.add_argument(
		"--no-interactive",
		"--no-inter",
		dest="no_interactive",
		action="store_true",
		default=None,
		help=(
			"do not automatically switch to interactive command line"
			" interface, for scripts"
		),
	)

	parser.add_argument(
		"-r",
		"--read-options",
		dest="readOptions",
		default="",
	)
	parser.add_argument(
		"-w",
		"--write-options",
		dest="writeOptions",
		default="",
	)

	parser.add_argument(
		"--json-read-options",
		dest="jsonReadOptions",
		default=None,
	)
	parser.add_argument(
		"--json-write-options",
		dest="jsonWriteOptions",
		default=None,
	)

	parser.add_argument(
		"--read-format",
		dest="inputFormat",
	)
	parser.add_argument(
		"--write-format",
		dest="outputFormat",
		action="store",
	)

	parser.add_argument(
		"--direct",
		dest="direct",
		action="store_true",
		default=None,
		help="if possible, convert directly without loading into memory",
	)
	parser.add_argument(
		"--indirect",
		dest="direct",
		action="store_false",
		default=None,
		help=(
			"disable `direct` mode, load full data into memory before writing"
			", this is default"
		),
	)
	parser.add_argument(
		"--sqlite",
		dest="sqlite",
		action="store_true",
		default=None,
		help=(
			"use SQLite as middle storage instead of RAM in direct mode,"
			"for very large glossaries"
		),
	)
	parser.add_argument(
		"--no-sqlite",
		dest="sqlite",
		action="store_false",
		default=None,
		help="do not use SQLite mode",
	)

	parser.add_argument(
		"--no-progress-bar",
		dest="progressbar",
		action="store_false",
		default=None,
	)
	parser.add_argument(
		"--no-color",
		dest="noColor",
		action="store_true",
		default=not defaultHasColor,
	)

	parser.add_argument(
		"--sort",
		dest="sort",
		action="store_true",
		default=None,
	)
	parser.add_argument(
		"--no-sort",
		dest="sort",
		action="store_false",
		default=None,
	)
	parser.add_argument(
		"--sort-key",
		action="store",
		dest="sortKeyName",
		default=None,
		help="name of sort key",
	)
	parser.add_argument(
		"--sort-encoding",
		action="store",
		dest="sortEncoding",
		default=None,
		help="encoding of sort (default utf-8)",
	)

	# _______________________________

	parser.add_argument(
		"--source-lang",
		action="store",
		dest="sourceLang",
		default=None,
		help="source/query language",
	)
	parser.add_argument(
		"--target-lang",
		action="store",
		dest="targetLang",
		default=None,
		help="target/definition language",
	)
	parser.add_argument(
		"--name",
		action="store",
		dest="name",
		default=None,
		help="glossary name/title",
	)

	# _______________________________

	parser.add_argument(
		"--reverse",
		dest="reverse",
		action="store_true",
	)

	parser.add_argument(
		"inputFilename",
		action="store",
		default="",
		nargs="?",
	)
	parser.add_argument(
		"outputFilename",
		action="store",
		default="",
		nargs="?",
	)

	# _______________________________

	for key, option in UIBase.configDefDict.items():
		registerConfigOption(parser, key, option)


def validateFlags(args: argparse.Namespace, log: logging.Logger) -> bool:
	from pyglossary.sort_keys import lookupSortKey, namedSortKeyList

	for param1, param2 in UIBase.conflictingParams:
		if getattr(args, param1) and getattr(args, param2):
			log.critical(
				"Conflicting flags: "
				f"--{param1.replace('_', '-')} and "
				f"--{param2.replace('_', '-')}",
			)
			return False

	if not args.sort:
		if args.sortKeyName:
			log.critical("Passed --sort-key without --sort")
			return False
		if args.sortEncoding:
			log.critical("Passed --sort-encoding without --sort")
			return False

	if args.sortKeyName and not lookupSortKey(args.sortKeyName):
		valuesStr = ", ".join(_sk.name for _sk in namedSortKeyList)
		log.critical(
			f"Invalid sortKeyName={args.sortKeyName!r}"
			f". Supported values:\n{valuesStr}",
		)
		return False

	return True


def configFromArgs(
	args: argparse.Namespace,
	log: logging.Logger,
) -> dict[str, Any]:
	config: dict[str, Any] = {}
	for key, option in UIBase.configDefDict.items():
		if not option.hasFlag:
			continue
		value = getattr(args, key, None)
		if value is None:
			continue
		log.debug(f"config: {key} = {value}")
		if not option.validate(value):
			log.error(f"invalid config value: {key} = {value!r}")
			continue
		config[key] = value
	return config
