def cleanWinArabicStr(u):
	"""
		u is a utf-8 encoded string
	"""
	replaceList = [
		('ی', 'ي'),
		('ک', 'ك'),
		('ٔ', 'ء'),
		('\ufffd', ''),

	] + [(chr(i), chr(i+144)) for i in range(1632, 1642)]
	for item in replaceList:
		u = u.replace(item[0], item[1])
	return u


def recodeToWinArabic(u):
	"""
		u is a utf-8 encoded string
	"""
	u = cleanWinArabicStr(u)
	return u.encode('windows-1256', 'replace')
