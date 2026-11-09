#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

rootDir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(rootDir))

from pyglossary.glossary_v2 import Glossary


def fail(message: str) -> int:
	print(message, file=sys.stderr)
	return 1


def pluginStem(plugin) -> str:
	return plugin.moduleName.split(".")[-1]


def findPlugins(plugins, lookup: str):
	byLname = [plugin for plugin in plugins if plugin.lname == lookup]
	if byLname:
		return byLname
	byModule = [plugin for plugin in plugins if pluginStem(plugin) == lookup]
	if byModule:
		return byModule
	return [
		plugin
		for plugin in plugins
		if plugin.lname.startswith(lookup) or pluginStem(plugin).startswith(lookup)
	]


def findTestFiles(testsDir: Path, stems: list[str], knownStems: set[str]) -> list[Path]:
	testFiles: list[Path] = []
	for stem in stems:
		for testFile in sorted(testsDir.glob(f"g_{stem}_test.py")):
			if testFile not in testFiles:
				testFiles.append(testFile)
		for testFile in sorted(testsDir.glob(f"g_{stem}_*_test.py")):
			testStem = testFile.name[len("g_") : -len("_test.py")]
			if testStem in knownStems:
				continue
			if testFile not in testFiles:
				testFiles.append(testFile)
	return testFiles


def main(argv: list[str]) -> int:
	if len(argv) != 2:
		return fail(
			'Must give plugins l_name as argument, for example "stardict" or '
			'"octopus_mdict"',
		)

	lookup = argv[1]
	Glossary.init(usePluginsJson=False, skipDisabledPlugins=False)
	plugins = list(Glossary.plugins.values())

	matches = findPlugins(plugins, lookup)
	if not matches:
		return fail(f"Did not find a plugin matching {lookup!r}")
	if len(matches) > 1:
		names = ", ".join(sorted(plugin.lname for plugin in matches))
		return fail(f"Multiple plugins match {lookup!r}: {names}")

	plugin = matches[0]
	moduleStem = pluginStem(plugin)
	stems = [moduleStem]
	if plugin.lname not in stems:
		stems.append(plugin.lname)

	knownStems = {pluginStem(item) for item in plugins}
	knownStems |= {item.lname for item in plugins}

	testsDir = rootDir / "tests"
	testFiles = findTestFiles(testsDir, stems, knownStems)
	if not testFiles:
		return fail(
			f"Did not find a test module for plugin {plugin.lname!r} "
			f"(module {moduleStem!r})",
		)

	modulePath = plugin.path
	if modulePath.with_suffix(".py").is_file():
		include = str(modulePath.with_suffix(".py"))
	else:
		include = str(modulePath / "*.py")

	pluginsDir = rootDir / "pyglossary" / "plugins"
	dataFile = pluginsDir / f"{plugin.lname}.cover"
	outDir = pluginsDir / f"{plugin.lname}.coverhtml"
	outDir.mkdir(parents=True, exist_ok=True)

	print(f"Using plugin {plugin.name!r} (lname {plugin.lname!r}, module {moduleStem!r})")
	print(f"Tests: {', '.join(testFile.name for testFile in testFiles)}")

	testModules = [testFile.name[: -len(".py")] for testFile in testFiles]
	runCommand = [
		sys.executable,
		"-m",
		"coverage",
		"run",
		f"--data-file={dataFile}",
		"-m",
		"unittest",
		*testModules,
	]
	print("+", " ".join(runCommand))
	try:
		subprocess.run(runCommand, cwd=testsDir, check=True)
	except subprocess.CalledProcessError as error:
		return error.returncode

	htmlCommand = [
		sys.executable,
		"-m",
		"coverage",
		"html",
		f"--data-file={dataFile}",
		f"--include={include}",
		f"--directory={outDir}",
	]
	print("+", " ".join(htmlCommand))
	htmlResult = subprocess.run(htmlCommand, cwd=rootDir, check=False)
	if htmlResult.returncode != 0:
		print(f"'coverage html' failed with {htmlResult.returncode}")

	indexPath = outDir / "index.html"
	if indexPath.is_file():
		print(f"file://{indexPath}")

	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
