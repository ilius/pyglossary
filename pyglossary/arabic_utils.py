# -*- coding: utf-8 -*-


def cleanWinArabicStr(u: str) -> str:
	"""
		u is a utf-8 encoded string
	"""
	replaceList = [
		("ی", "ي"),
		("ک", "ك"),
		("ٔ", "ء"),
		("\ufffd", ""),
		('٠', '0'), ('١', '1'), ('٢', '2'), ('٣', '3'), ('٤', '4'),
		('٥', '5'), ('٦', '6'), ('٧', '7'), ('٨', '8'), ('٩', '9'),
		('۰', '0'), ('۱', '1'), ('۲', '2'), ('۳', '3'), ('۴', '4'),
		('۵', '5'), ('۶', '6'), ('۷', '7'), ('۸', '8'), ('۹', '9'),
	]
	# [(chr(1632+i), chr(48+i)) for i in range(10)]
	# [(chr(1776+i), chr(48+i)) for i in range(10)]
	for item in replaceList:
		u = u.replace(item[0], item[1])
	return u
