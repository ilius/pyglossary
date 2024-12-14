from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyglossary.ui.argparse_utils import StoreConstAction

if TYPE_CHECKING:
	import argparse

	from pyglossary.option import Option


def registerConfigOption(
	parser: argparse.ArgumentParser,
	key: str,
	option: Option,
) -> None:
	if not option.hasFlag:
		return
	flag = option.customFlag
	if not flag:
		flag = key.replace("_", "-")

	if option.typ != "bool":
		parser.add_argument(
			f"--{flag}",
			dest=key,
			default=None,
			help=option.comment,
		)
		return

	if not option.comment:
		print(f"registerConfigOption: option has no comment: {option}")
		return

	if not option.falseComment:
		parser.add_argument(
			f"--{flag}",
			dest=key,
			action="store_true",
			default=None,
			help=option.comment,
		)
		return

	parser.add_argument(
		dest=key,
		action=StoreConstAction(
			f"--{flag}",
			same_dest=f"--no-{flag}",
			const_value=True,
			dest=key,
			default=None,
			help=option.comment,
		),
	)
	parser.add_argument(
		dest=key,
		action=StoreConstAction(
			f"--no-{flag}",
			same_dest=f"--{flag}",
			const_value=False,
			dest=key,
			default=None,
			help=option.falseComment,
		),
	)


def evaluateReadOptions(
	options: dict[str, Any],
	inputFilename: str,
	inputFormat: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
	from pyglossary.glossary_v2 import Glossary

	inputArgs = Glossary.detectInputFormat(
		inputFilename,
		formatName=inputFormat,
	)
	if not inputArgs:
		return None, f"Could not detect format for input file {inputFilename}"
	inputFormat = inputArgs.formatName
	optionsProp = Glossary.plugins[inputFormat].optionsProp
	for optName, optValue in options.items():
		if optName not in Glossary.formatsReadOptions[inputFormat]:
			return None, f"Invalid option name {optName} for format {inputFormat}"
		prop = optionsProp[optName]
		optValueNew, ok = prop.evaluate(optValue)
		if not ok or not prop.validate(optValueNew):
			return (
				None,
				f"Invalid option value {optName}={optValue!r} for format {inputFormat}",
			)
		options[optName] = optValueNew

	return options, None


def evaluateWriteOptions(
	options: dict[str, Any],
	inputFilename: str,
	outputFilename: str,
	outputFormat: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
	from pyglossary.glossary_v2 import Glossary

	outputArgs = Glossary.detectOutputFormat(
		filename=outputFilename,
		formatName=outputFormat,
		inputFilename=inputFilename,
	)
	if outputArgs is None:
		return None, "failed to detect output format"
	outputFormat = outputArgs.formatName
	optionsProp = Glossary.plugins[outputFormat].optionsProp
	for optName, optValue in options.items():
		if optName not in Glossary.formatsWriteOptions[outputFormat]:
			return None, f"Invalid option name {optName} for format {outputFormat}"
		prop = optionsProp[optName]
		optValueNew, ok = prop.evaluate(optValue)
		if not ok or not prop.validate(optValueNew):
			return (
				None,
				f"Invalid option value {optName}={optValue!r} "
				f"for format {outputFormat}",
			)
		options[optName] = optValueNew

	return options, None


def parseReadWriteOptions(
	args: argparse.Namespace,
) -> tuple[tuple[dict[str, Any], dict[str, Any]] | None, str | None]:
	from pyglossary.ui.ui_cmd import parseFormatOptionsStr

	readOptions = parseFormatOptionsStr(args.readOptions)
	if readOptions is None:
		return None, ""
	if args.jsonReadOptions:
		newReadOptions = json.loads(args.jsonReadOptions)
		if not isinstance(newReadOptions, dict):
			return None, (
				"invalid value for --json-read-options, "
				f"must be an object/dict, not {type(newReadOptions)}"
			)
		readOptions.update(newReadOptions)

	writeOptions = parseFormatOptionsStr(args.writeOptions)
	if writeOptions is None:
		return None, ""
	if args.jsonWriteOptions:
		newWriteOptions = json.loads(args.jsonWriteOptions)
		if not isinstance(newWriteOptions, dict):
			return None, (
				"invalid value for --json-write-options, "
				f"must be an object/dict, not {type(newWriteOptions)}"
			)
		writeOptions.update(newWriteOptions)

	return (readOptions, writeOptions), None
