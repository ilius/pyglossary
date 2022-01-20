import sys
from os.path import dirname, abspath
import unittest
from time import time as now
from time import sleep

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary
from pyglossary.ui.ui_cmd_interactive import UI

from prompt_toolkit.application.current import get_app_session
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from contextlib import contextmanager


@contextmanager
def dummy_context_manager() -> "Generator[None, None, None]":
    yield


class MockInputAttacher(object):
	def __init__(self, mockInput):
		self.mockInput = mockInput
		self.detached = False

	@contextmanager
	def attach(self, input_ready_callback):
		input_ready_callback()
		while not self.detached:
			#self.mockInput.wait_for_keys()
			yield self.mockInput._keys


class MockInput(object):
	def __init__(self):
		self._keys = None
		self._timeout = 5  # seconds

	def send_keys(self, keys):
		keysPressList = []
		for key in keys:
			if isinstance(key, str):
				for char in key:
					keysPressList.append(KeyPress(key=char, data=char))
				continue
			keysPressList.append(KeyPress(key=key))
		self._keys = keysPressList

	def wait_for_keys(self):
		timeout = self._timeout
		t0 = now()
		while self._keys is None:
			if now() - t0 > timeout:
				raise RuntimeError("Timeout")
			sleep(0.1)

	def read_keys(self) -> "List[KeyPress]":
		self.wait_for_keys()
		keys, self._keys = self._keys, None
		return keys

	def fileno(self) -> int:
		raise NotImplementedError

	def typeahead_hash(self) -> str:
		return "dummy-%s" % id(self)

	@property
	def closed(self) -> bool:
		return False

	def raw_mode(self) -> "ContextManager[None]":
		print("raw_mode")
		return dummy_context_manager()

	def cooked_mode(self) -> "ContextManager[None]":
		print("cooked_mode")
		return dummy_context_manager()

	def attach(self, input_ready_callback: "Callable[[], None]") -> "ContextManager[None]":
		return MockInputAttacher(self).attach(input_ready_callback)

	def detach(self) -> "ContextManager[None]":
		print("detach")
		return dummy_context_manager()


origStdout = sys.stdout
origStdin = sys.stdin

class MockStdout(object):
	encoding = "utf-8"

	def __init__(self):
		self._waitForOut = None
		self._waitCallback = None

	def wait_for(self, out, callback):
		self._waitForOut = out
		self._waitCallback = callback

	def write(self, data):
		if isinstance(data, bytes):
			data = data.decode("utf-8")
		origStdout.write(data)
		if self._waitForOut:
			if self._waitForOut in data:
				self._waitCallback()
			self._waitForOut = self._waitCallback = None

	def flush(self):
		origStdout.flush()

	def isatty(self):
		return True

	def fileno(self) -> int:
		return origStdout.fileno()


class MockStdin(object):
	def read(self, n):
		return b""


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		# self.dataFileCRC32.update({})
		self.origInput = get_app_session().input

	def setUp(self):
		TestGlossaryBase.setUp(self)
		self.input = get_app_session()._input = MockInput()
		# sys.stdin = MockStdin()
		self.output = sys.stdout = MockStdout()
		self.ui = UI()

	def tearDown(self):
		sys.stdout = origStdout
		# sys.stdin = origStdin
		TestGlossaryBase.tearDown(self)
		self.input = None
		del self.ui
		self.ui = None

	def wait_and_send(self, inputMsg, outputStr):
		self.output.wait_for(
			inputMsg,
			lambda: self.input.send_keys([
				outputStr,
				Keys.Enter,
			]),
		)

	def test_1(self):
		inputFilename = self.downloadFile("100-en-fa.txt")

		inp = self.input
		out = self.output

		self.wait_and_send("Input file:", inputFilename)

		#inp.send_keys([Keys.Enter])

		self.ui.run()




