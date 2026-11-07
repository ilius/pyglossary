"""
Regression tests for the Slint UI's GC invariant (see `ui_slint.utils.load_slint`).

Each scenario runs in a subprocess, because the failure mode is SIGABRT. No
display is needed.
"""

import importlib.util
import subprocess
import sys
import textwrap
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))

_PRELUDE = f"""
import gc, sys, threading
sys.path.insert(0, {rootDir!r})
from pyglossary.ui.ui_slint import utils

def gcOnWorker():
	t = threading.Thread(target=gc.collect)
	t.start()
	t.join()

gc.disable()  # only explicit collections: deterministic
"""


@unittest.skipUnless(importlib.util.find_spec("slint"), "slint is not installed")
class TestSlintCompileCache(unittest.TestCase):
	def assertCleanRun(self, body: str) -> None:
		proc = subprocess.run(  # noqa: S603
			[sys.executable, "-c", _PRELUDE + textwrap.dedent(body)],
			capture_output=True,
			text=True,
			timeout=300,
			check=False,
		)
		self.assertEqual(
			proc.returncode,
			0,
			msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
		)
		self.assertNotIn("unsendable", proc.stderr)

	def test_repeated_loads_then_worker_gc(self):
		# opening/closing dialogs, then a GC on the conversion thread
		self.assertCleanRun("""
		for name in ("dialogs.slint", "main_window.slint"):
			assert utils.load_slint(name) is utils.load_slint(name), name
		for _ in range(20):
			utils.load_slint("dialogs.slint")
			utils.load_slint("main_window.slint")
		gcOnWorker()
		""")

	def test_clear_cache_then_main_gc_then_worker_gc(self):
		# the UI._shutdown sequence
		self.assertCleanRun("""
		utils.load_slint("dialogs.slint")
		utils.load_slint("main_window.slint")
		utils.clearSlintCache()
		gc.collect()
		gcOnWorker()
		""")


if __name__ == "__main__":
	unittest.main()
