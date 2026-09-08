#!/usr/bin/env python3
"""
Self-contained build script for the macOS Slint-UI build of PyGlossary.

Usage: build.py [stage]
  stage: uv | venv | deps-brew | deps-python | patch | nuitka-build |
         copy-assets | dmg | all (default)

Unlike scripts/ci/mac/ (tk build, split across 5 files), this keeps every
stage in one script and computes its own brew/compiler env vars per-stage,
so it does not depend on a prior GitHub Actions step exporting them into
$GITHUB_ENV -- it also runs standalone locally via `make -C scripts/ci/mac/slint`.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR / ".." / ".." / ".." / ".."

APPNAME = os.getenv("APPNAME", "PyGlossarySlint")
DIST_DIR = os.getenv("DIST_DIR", "dist.nuitka.slint")
MAIN_SCRIPT = os.getenv("MAIN_SCRIPT", "main.py")
SLINT_VERSION = os.getenv("SLINT_VERSION", "1.17.0b2")
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.13")

ARCH = platform.machine()
OS_TAG = f"macos-{ARCH}-{platform.mac_ver()[0]}"


def log(msg: str) -> None:
	print(f"[mac-slint] {msg}")


def git_describe(*extra_args: str) -> str:
	return subprocess.check_output(
		["git", "describe", *extra_args],
		text=True,
	).strip()


def step_uv() -> None:
	if shutil.which("uv") is None:
		log("Installing uv...")
		subprocess.run(
			"curl -LsSf https://astral.sh/uv/install.sh | sh",
			shell=True,
			check=True,
		)


def step_venv() -> None:
	step_uv()
	if not (REPO_ROOT / ".venv").is_dir():
		subprocess.run(
			["uv", "venv", ".venv", "--python", PYTHON_VERSION],
			check=True,
		)


# Only the native-toolchain deps required to build PyICU/python-lzo from
# source. No GUI toolkit (tk/qt/gtk/wx) packages -- the Slint build ships
# its own self-contained native widget renderer.
def step_deps_brew() -> None:
	log("Installing brew dependencies...")
	subprocess.run(
		["brew", "install", "libffi", "icu4c", "lzo", "pkg-config"],
		check=True,
	)


# Returns compiler/linker flags for the brew-installed native deps
# (icu4c, lzo, libffi) needed to build PyICU / python-lzo from source
# and to link them into the nuitka standalone binary.
def resolve_brew_env() -> dict:
	brew_prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
	prefix_icu4c = subprocess.check_output(
		["brew", "--prefix", "icu4c"], text=True
	).strip()
	prefix_lzo = subprocess.check_output(["brew", "--prefix", "lzo"], text=True).strip()
	prefix_libffi = subprocess.check_output(
		["brew", "--prefix", "libffi"], text=True
	).strip()

	env = dict(os.environ)
	env["PKG_CONFIG_PATH"] = (
		f"{brew_prefix}/lib/pkgconfig:{prefix_icu4c}/lib/pkgconfig:"
		f"{prefix_lzo}/lib/pkgconfig:{prefix_libffi}/lib/pkgconfig"
	)
	env["LDFLAGS"] = (
		f"-L{prefix_libffi}/lib -L{prefix_icu4c}/lib -L{prefix_lzo}/lib "
		f"-L{brew_prefix}/lib"
	)
	env["CPPFLAGS"] = (
		f"-I{prefix_icu4c}/include -I{prefix_libffi}/include -I{prefix_lzo}/include"
	)
	env["DYLD_LIBRARY_PATH"] = (
		f"{prefix_icu4c}/lib:{prefix_libffi}/lib:{prefix_lzo}/lib:{brew_prefix}/lib"
	)
	env["CC"] = "clang"
	env["CXX"] = "clang++"
	return env


def venv_env(env: dict | None = None) -> dict:
	env = dict(env or os.environ)
	venv_bin = REPO_ROOT / ".venv" / "bin"
	env["VIRTUAL_ENV"] = str(REPO_ROOT / ".venv")
	env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
	return env


def step_deps_python() -> None:
	step_uv()
	env = venv_env(resolve_brew_env())

	subprocess.run(["uv", "pip", "install", "-U", "nuitka"], check=True, env=env)
	subprocess.run(
		["uv", "pip", "install", f"slint=={SLINT_VERSION}"],
		check=True,
		env=env,
	)

	# Compiled plugin dependencies: static-link so the nuitka standalone
	# binary doesn't depend on brew's dylibs at runtime.
	static_env = dict(env)
	static_env["STATIC_DEPS"] = "true"
	for pkg in ("PyICU", "python-lzo"):
		subprocess.run(
			["uv", "pip", "install", "--no-binary", pkg, pkg],
			check=True,
			env=static_env,
		)

	subprocess.run(
		["uv", "pip", "install", "-r", "requirements.txt"],
		check=True,
		env=env,
	)


def step_patch() -> None:
	log("Patching sources for nuitka build...")
	if not (MAIN_SCRIPT and APPNAME):
		raise SystemExit("Missing env vars MAIN_SCRIPT/APPNAME")
	shutil.copyfile(MAIN_SCRIPT, f"{APPNAME}.py")
	Path("__init__.py").unlink(missing_ok=True)
	arg_main = Path("pyglossary/ui/argparse_main.py")
	arg_main.write_text(
		arg_main.read_text(encoding="utf-8").replace('default="auto"', 'default="slint"'),
		encoding="utf-8",
	)


def step_nuitka_build() -> None:
	env = venv_env(resolve_brew_env())

	log("Env vars:")
	log(f"LDFLAGS: {env['LDFLAGS']}")
	log(f"CPPFLAGS: {env['CPPFLAGS']}")
	log(f"DYLD_LIBRARY_PATH: {env['DYLD_LIBRARY_PATH']}")

	cmd = [
		str(REPO_ROOT / ".venv" / "bin" / "python"),
		"-m",
		"nuitka",
		"--standalone",
		"--assume-yes-for-downloads",
		"--follow-imports",
		"--macos-create-app-bundle",
		"--macos-app-icon=res/pyglossary.icns",
		f"--macos-signed-app-name={APPNAME}",
		f"--macos-app-name={APPNAME}",
		"--macos-app-mode=gui",
		"--include-package=pyglossary",
		"--include-package=slint",
		"--include-package-data=slint",
		"--nofollow-import-to=pyglossary.ui.ui_gtk",
		"--nofollow-import-to=pyglossary.ui.ui_gtk4",
		"--nofollow-import-to=pyglossary.ui.ui_qt6",
		"--nofollow-import-to=pyglossary.ui.ui_tk",
		"--nofollow-import-to=pyglossary.ui.ui_tk_wizard",
		"--nofollow-import-to=pyglossary.ui.ui_wx",
		"--nofollow-import-to=tkinter",
		"--nofollow-import-to=gi",
		"--nofollow-import-to=gtk",
		"--nofollow-import-to=wx",
		"--nofollow-import-to=pyqt4",
		"--nofollow-import-to=pyqt5",
		"--nofollow-import-to=pyqt6",
		"--nofollow-import-to=PySide6",
		"--nofollow-import-to=*.tests",
		"--noinclude-pytest-mode=nofollow",
		"--noinclude-setuptools-mode=nofollow",
		"--plugin-disable=pyqt5",
		"--include-module=pymorphy3",
		"--include-module=lxml",
		"--include-module=polib",
		"--include-module=yaml",
		"--include-module=bs4",
		"--include-module=html5lib",
		"--include-module=icu",
		"--include-module=colorize_pinyin",
		"--include-package-data=pyglossary",
		"--include-data-files=about=about",
		"--include-module=_json",
		"--include-module=_bisect",
		"--include-data-files=_license-dialog=_license-dialog",
		"--include-data-dir=res=.",
		"--include-data-files=_license-dialog=license-dialog",
		"--nofollow-import-to=unittest",
		f"--output-dir={DIST_DIR}",
		f"--output-filename={APPNAME}",
		f"{APPNAME}.py",
	]
	subprocess.check_call(cmd, env=env)


def step_copy_assets() -> None:
	log("Copying runtime assets into app bundle...")
	target = Path(DIST_DIR) / f"{APPNAME}.app" / "Contents" / "MacOS"
	if not target.is_dir():
		sys.stderr.write(f"target_path not found: {target}\n")
		raise SystemExit(1)
	for name in (
		"about",
		"AUTHORS",
		"_license-dialog",
		"config.json",
		"plugins-meta",
		"help",
		"res",
		"pyglossary",
	):
		src = Path(name)
		if not src.exists():
			sys.stderr.write(f"source not found: {name}\n")
			continue
		if src.is_dir():
			shutil.copytree(
				src,
				target / src.name,
				dirs_exist_ok=True,
				symlinks=True,
			)
		else:
			shutil.copy(src, target, follow_symlinks=False)


def step_dmg() -> None:
	log("Creating DMG...")
	version = git_describe("--abbrev=1")
	version_with_hash = git_describe()
	subprocess.run(
		[
			"hdiutil",
			"create",
			"-verbose",
			"-volname",
			f"{APPNAME}-{version_with_hash}",
			"-srcfolder",
			f"{DIST_DIR}/{APPNAME}.app",
			"-ov",
			"-format",
			"UDZO",
			"-fs",
			"HFS+J",
			f"{APPNAME}-{version}-{OS_TAG}.dmg",
		],
		check=True,
	)


def step_all() -> None:
	step_uv()
	step_venv()
	step_deps_brew()
	step_deps_python()
	step_patch()
	step_nuitka_build()
	step_copy_assets()
	step_dmg()


STAGES = {
	"uv": step_uv,
	"venv": step_venv,
	"deps-brew": step_deps_brew,
	"deps-python": step_deps_python,
	"patch": step_patch,
	"nuitka-build": step_nuitka_build,
	"copy-assets": step_copy_assets,
	"dmg": step_dmg,
	"all": step_all,
}


def main() -> None:
	os.chdir(REPO_ROOT)
	stage = sys.argv[1] if len(sys.argv) > 1 else "all"
	if stage not in STAGES:
		sys.stderr.write(f"Unknown stage: {stage}\n")
		sys.stderr.write(
			"Usage: build.py [uv|venv|deps-brew|deps-python|patch|"
			"nuitka-build|copy-assets|dmg|all]\n"
		)
		raise SystemExit(1)
	STAGES[stage]()


if __name__ == "__main__":
	main()
