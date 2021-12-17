import unittest
import locale
import random
from functools import cmp_to_key


def toBytes(s):
	return bytes(s, "utf-8") if isinstance(s, str) else bytes(s)


def sortKeyBytes(ba: bytes):
	assert isinstance(ba, bytes)
	# ba.lower() + ba is wrong
	return (
		ba.lower(),
		ba,
	)


def stardictStrCmp(s1, s2):
	"""
	use this function to sort index items in StarDict dictionary
	s1 and s2 must be utf-8 encoded strings
	"""
	s1 = toBytes(s1)
	s2 = toBytes(s2)
	a = asciiStrCaseCmp(s1, s2)
	if a == 0:
		return strCmp(s1, s2)
	return a


# the slow way in Python 3 (where there is no cmp arg in list.sort)
sortKeyOld = cmp_to_key(stardictStrCmp)  # TOO SLOW


def asciiStrCaseCmp(ba1, ba2):
	"""
	ba1 and ba2 are instances of bytes
	imitate g_ascii_strcasecmp function of glib library gstrfuncs.c file
	"""
	commonLen = min(len(ba1), len(ba2))
	for i in range(commonLen):
		c1 = asciiLower(ba1[i])
		c2 = asciiLower(ba2[i])
		if c1 != c2:
			return c1 - c2
	return len(ba1) - len(ba2)


def strCmp(ba1, ba2):
	"""
	ba1 and ba2 are instances of bytes
	imitate strcmp of standard C library

	Attention! You may have a temptation to replace this function with
	built-in cmp() function. Hold on! Most probably these two function behave
	identically now, but cmp does not document how it compares strings.
	There is no guaranty it will not be changed in future.
	Since we need predictable sorting order in StarDict dictionary, we need
	to preserve this function despite the fact there are other ways to
	implement it.
	"""
	commonLen = min(len(ba1), len(ba2))
	for i in range(commonLen):
		c1 = ba1[i]
		c2 = ba2[i]
		if c1 != c2:
			return c1 - c2
	return len(ba1) - len(ba2)


def isAsciiAlpha(c):
	"""
	c is int
	"""
	return ord("A") <= c <= ord("Z") or ord("a") <= c <= ord("z")


def isAsciiLower(c):
	return ord("a") <= c <= ord("z")


def isAsciiUpper(c):
	"""
	c is int
	imitate ISUPPER macro of glib library gstrfuncs.c file
	"""
	return ord("A") <= c <= ord("Z")


def asciiLower(c):
	"""
	c is int
	returns int (ascii character code)

	imitate TOLOWER macro of glib library gstrfuncs.c file

	This function converts upper case Latin letters to corresponding
	lower case letters, other chars are not changed.

	c must be non-Unicode string of length 1.
	You may apply this function to individual bytes of non-Unicode string.
	The following encodings are allowed: single byte encoding like koi8-r,
	cp1250, cp1251, cp1252, etc, and utf-8 encoding.

	Attention! Python Standard Library provides str.lower() method.
	It is not a correct replacement for this function.
	For non-unicode string str.lower() is locale dependent, it not only
	converts Latin letters to lower case, but also locale specific letters
	will be converted.
	"""
	return c - ord("A") + ord("a") if isAsciiUpper(c) else c


def getRandomBytes(avgLen, sigma):
	length = round(random.gauss(avgLen, sigma))
	return bytes([
		random.choice(range(256))
		for _ in range(length)
	])


class AsciiLowerUpperTest(unittest.TestCase):
	def set_locale_iter(self):
		for localeName in locale.locale_alias.values():
			try:
				locale.setlocale(locale.LC_ALL, localeName)
			except Exception as e:
				if "unsupported locale setting" not in str(e):
					print(e)
				continue
			yield localeName

	def test_isalpha(self):
		for _ in self.set_locale_iter():
			for code in range(256):
				self.assertEqual(
					isAsciiAlpha(code),
					bytes([code]).isalpha(),
				)

	def test_islower(self):
		for _ in self.set_locale_iter():
			for code in range(256):
				self.assertEqual(
					isAsciiLower(code),
					bytes([code]).islower(),
				)

	def test_isupper(self):
		for _ in self.set_locale_iter():
			for code in range(256):
				self.assertEqual(
					isAsciiUpper(code),
					bytes([code]).isupper(),
				)

	def test_lower(self):
		for _ in self.set_locale_iter():
			for code in range(256):
				self.assertEqual(
					asciiLower(code),
					ord(bytes([code]).lower()),
				)


class SortRandomTest(unittest.TestCase):
	def set_locale_iter(self):
		for localeName in locale.locale_alias.values():
			try:
				locale.setlocale(locale.LC_ALL, localeName)
			except Exception as e:
				if "unsupported locale setting" not in str(e):
					raise e
				continue
			# print(localeName)
			yield localeName

	def test_sort_1(self):
		bsList = [
			getRandomBytes(30, 10)
			for _ in range(100)
		]
		for _ in self.set_locale_iter():
			self.assertEqual(
				sorted(
					bsList,
					key=sortKeyOld,
				),
				sorted(
					bsList,
					key=sortKeyBytes,
				)
			)


if __name__ == "__main__":
	unittest.main()
