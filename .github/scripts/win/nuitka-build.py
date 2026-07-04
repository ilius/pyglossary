import os
import subprocess
import sys


def main() -> None:
	default_ui = os.getenv("DEFAULT_UI", "tk")
	app_name = os.getenv("APPNAME", "main")
	dist_dir = os.getenv("DIST_DIR", "dist.nuitka")

	print(f"DIST_DIR: {dist_dir}")
	print(f"APPNAME: {app_name}")
	print(f"DEFAULT_UI: {default_ui}")

	if default_ui == "wx":
		ui_opts = [
			"--include-package=wx",
			"--include-module=wx._xml",
			"--nofollow-import-to=pyglossary.ui.ui_tk",
			"--nofollow-import-to=pyglossary.ui.ui_tk_wizard",
			"--nofollow-import-to=pyglossary.ui.ui_slint",
			"--nofollow-import-to=slint",
		]
	elif default_ui == "slint":
		ui_opts = [
			"--include-package=slint",
			"--include-package-data=slint",
			"--nofollow-import-to=pyglossary.ui.ui_tk",
			"--nofollow-import-to=pyglossary.ui.ui_tk_wizard",
			"--nofollow-import-to=pyglossary.ui.ui_wx",
			"--nofollow-import-to=tkinter",
			"--nofollow-import-to=wx",
		]
	else:
		ui_opts = [
			"--enable-plugin=tk-inter",
			"--include-module=tkinter",
			"--nofollow-import-to=pyglossary.ui.ui_wx",
			"--nofollow-import-to=pyglossary.ui.ui_slint",
			"--nofollow-import-to=wx",
			"--nofollow-import-to=slint",
		]

	cmd = [
		sys.executable,
		"-m",
		"nuitka",
		"--standalone",
		"--assume-yes-for-downloads",
		"--plugin-enable=dll-files",
		"--plugin-enable=anti-bloat",
		"--follow-imports",
		"--windows-console-mode=disable",
		"--windows-icon-from-ico=res/pyglossary.ico",
		*ui_opts,
		"--include-package=pyglossary",
		"--include-module=lzo",
		"--include-module=pymorphy3",
		"--include-module=_json",
		"--include-module=lxml",
		"--include-module=polib",
		"--include-module=yaml",
		"--include-module=bs4",
		"--include-module=html5lib",
		"--include-module=icu",
		"--include-module=colorize_pinyin",
		"--include-package-data=pyglossary",
		"--include-data-files=about=about",
		"--include-data-files=_license-dialog=_license-dialog",
		"--include-data-files=_license-dialog=license-dialog",
		"--noinclude-pytest-mode=nofollow",
		"--noinclude-setuptools-mode=nofollow",
		"--nofollow-import-to=pyglossary.ui.ui_gtk",
		"--nofollow-import-to=pyglossary.ui.ui_gtk4",
		"--nofollow-import-to=pyglossary.ui.ui_qt",
		"--nofollow-import-to=gi",
		"--nofollow-import-to=gtk",
		"--nofollow-import-to=pyqt4",
		"--nofollow-import-to=pyqt5",
		"--nofollow-import-to=pyqt6",
		"--nofollow-import-to=*.tests",
		"--plugin-disable=pyqt5",
		f"{app_name}.py",
		f"--output-dir={dist_dir}",
		f"--output-filename={app_name}.exe",
	]
	subprocess.check_call(cmd)


if __name__ == "__main__":
	main()
