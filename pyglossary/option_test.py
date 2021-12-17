#!/usr/bin/python3

import sys
from os.path import join, dirname, abspath
import unittest
import random

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.option import *


class TestOptionValidateBoolNumber(unittest.TestCase):
	def caseOK(self, cls, raw: str, value: "Optional[bool]"):
		opt = cls()
		valueActual, ok = opt.evaluate(raw)
		self.assertTrue(ok, "evaluate failed")
		self.assertEqual(valueActual, value)
		ok2 = opt.validate(valueActual)
		self.assertEqual(ok2, True, "validate failed")

	def caseFailed(self, cls, raw: str, value: "Optional[bool]"):
		opt = cls()
		valueActual, ok = opt.evaluate(raw)
		self.assertFalse(ok)
		self.assertEqual(valueActual, value)

	def test_bool_ok(self):
		self.caseOK(BoolOption, "True", True)
		self.caseOK(BoolOption, "False", False)

		self.caseOK(BoolOption, "true", True)
		self.caseOK(BoolOption, "false", False)

		self.caseOK(BoolOption, "TRUE", True)
		self.caseOK(BoolOption, "FALSE", False)

		self.caseOK(BoolOption, "1", True)
		self.caseOK(BoolOption, "0", False)

		self.caseOK(BoolOption, "yes", True)
		self.caseOK(BoolOption, "no", False)

		self.caseOK(BoolOption, "YES", True)
		self.caseOK(BoolOption, "NO", False)

	def test_bool_failed(self):
		self.caseFailed(BoolOption, "Y", None)
		self.caseFailed(BoolOption, "N", None)
		self.caseFailed(BoolOption, "YESS", None)
		self.caseFailed(BoolOption, "NOO", None)
		self.caseFailed(BoolOption, "123", None)
		self.caseFailed(BoolOption, "a", None)

	def test_int_ok(self):
		self.caseOK(IntOption, "0", 0)
		self.caseOK(IntOption, "1", 1)
		self.caseOK(IntOption, "-1", -1)
		self.caseOK(IntOption, "1234", 1234)

	def test_int_failed(self):
		self.caseFailed(IntOption, "abc", None)
		self.caseFailed(IntOption, "12f", None)
		self.caseFailed(IntOption, "fff", None)

	def test_file_size_ok(self):
		self.caseOK(FileSizeOption, "0", 0)
		self.caseOK(FileSizeOption, "1", 1)
		self.caseOK(FileSizeOption, "1234", 1234)

		self.caseOK(FileSizeOption, "123k", 123000)
		self.caseOK(FileSizeOption, "123m", 123000000)
		self.caseOK(FileSizeOption, "1.7g", 1700000000)

		self.caseOK(FileSizeOption, "123kib", 123 * 1024)
		self.caseOK(FileSizeOption, "123KiB", 123 * 1024)
		self.caseOK(FileSizeOption, "123ki", 123 * 1024)
		self.caseOK(FileSizeOption, "123Ki", 123 * 1024)

		self.caseOK(FileSizeOption, "123mib", 123 * 1024 ** 2)
		self.caseOK(FileSizeOption, "123MiB", 123 * 1024 ** 2)
		self.caseOK(FileSizeOption, "123mi", 123 * 1024 ** 2)
		self.caseOK(FileSizeOption, "123Mi", 123 * 1024 ** 2)

		self.caseOK(FileSizeOption, "1.7gib", int(1.7 * 1024 ** 3))
		self.caseOK(FileSizeOption, "1.7GiB", int(1.7 * 1024 ** 3))
		self.caseOK(FileSizeOption, "1.7gi", int(1.7 * 1024 ** 3))
		self.caseOK(FileSizeOption, "1.7Gi", int(1.7 * 1024 ** 3))

	def test_file_size_failed(self):
		self.caseFailed(FileSizeOption, "-1", None)
		self.caseFailed(FileSizeOption, "123kg", None)
		self.caseFailed(FileSizeOption, "123k.1", None)

	def test_float_ok(self):
		self.caseOK(FloatOption, "0", 0.0)
		self.caseOK(FloatOption, "1", 1.0)
		self.caseOK(FloatOption, "-1", -1.0)
		self.caseOK(FloatOption, "1234", 1234.0)
		self.caseOK(FloatOption, "1.5", 1.5)
		self.caseOK(FloatOption, "-7.9", -7.9)

	def test_float_failed(self):
		self.caseFailed(FloatOption, "abc", None)
		self.caseFailed(FloatOption, "12f", None)
		self.caseFailed(FloatOption, "fff", None)


class TestOptionValidateStr(unittest.TestCase):
	def newTester(self, customValue: bool, values: "List[str]"):
		def test(raw: str, valid: bool):
			opt = StrOption(customValue=customValue, values=values)
			valueActual, evalOkActual = opt.evaluate(raw)
			self.assertEqual(evalOkActual, True, "evaluate failed")
			self.assertEqual(valueActual, raw)
			validActual = opt.validate(valueActual)
			self.assertEqual(validActual, valid, "validate failed")
		return test

	def test_1(self):
		test = self.newTester(False, ["a", "b", "c"])
		test("a", True)
		test("b", True)
		test("c", True)
		test("d", False)
		test("123", False)

	def test_2(self):
		test = self.newTester(True, ["a", "b", "3"])
		test("a", True)
		test("b", True)
		test("c", True)
		test("d", True)
		test("123", True)


class TestOptionValidateDict(unittest.TestCase):
	def caseOK(self, raw: str, value: "Optional[Dict]"):
		opt = DictOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertTrue(ok, "evaluate failed")
		self.assertEqual(valueActual, value)
		ok2 = opt.validate(valueActual)
		self.assertEqual(ok2, True, "validate failed")

	def caseEvalFail(self, raw: str):
		opt = DictOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertFalse(ok)
		self.assertEqual(valueActual, None)

	def test_dict_ok(self):
		self.caseOK("", None)
		self.caseOK("{}", {})
		self.caseOK('{"a": 1}', {"a": 1})
		self.caseOK('{"a": "b", "123":456}', {"a": "b", "123": 456})

	def test_dict_syntaxErr(self):
		self.caseEvalFail("123abc")
		self.caseEvalFail('{')
		self.caseEvalFail("(")
		self.caseEvalFail('{"a": 1')
		self.caseEvalFail('{"a": 1]')
		self.caseEvalFail('][')

	def test_dict_notDict(self):
		self.caseEvalFail("123")
		self.caseEvalFail("[]")
		self.caseEvalFail("[1, 2, 3]")
		self.caseEvalFail('["a", 2, 3.5]')
		self.caseEvalFail('{10, 20, 30}')


class TestOptionValidateList(unittest.TestCase):
	def caseOK(self, raw: str, value: "Optional[Dict]"):
		opt = ListOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertTrue(ok, "evaluate failed")
		self.assertEqual(valueActual, value)
		ok2 = opt.validate(valueActual)
		self.assertEqual(ok2, True, "validate failed")

	def caseEvalFail(self, raw: str):
		opt = ListOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertFalse(ok, f"evaluale did not fail, valueActual={valueActual!r}")
		self.assertEqual(valueActual, None)

	def test_list_ok(self):
		self.caseOK("", None)
		self.caseOK("[]", [])
		self.caseOK('["a", "b"]', ["a", "b"])
		self.caseOK("[1, 2, 3]", [1, 2, 3])
		self.caseOK('["a", 2, 3.5]', ["a", 2, 3.5])

	def test_list_syntaxErr(self):
		self.caseEvalFail("123abc")
		self.caseEvalFail('{')
		self.caseEvalFail("(")
		self.caseEvalFail('{"a": 1')
		self.caseEvalFail('{"a": 1]')
		self.caseEvalFail('][')

	def test_list_notList(self):
		self.caseEvalFail("123")
		self.caseEvalFail('{10, 20, 30}')
		self.caseEvalFail('{"a": 1}')
		self.caseEvalFail('{"a": "b", "123":456}')


if __name__ == "__main__":
	unittest.main()
