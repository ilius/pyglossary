def intToBinStr(n, stLen=0):
	bs = b''
	while n > 0:
		bs = bytes([n & 255]) + bs
		n >>= 8
	return bs.rjust(stLen, b'\x00')


def intToBinStr(n, stLen=0):
	return bytes((
		(n >> (i << 3)) & 0xff
		for i in range(int(ceil(log(n, 256)))-1, -1, -1)
	)).rjust(stLen, b'\x00')


def binStrToInt(bs):
	n = 0
	for c in bs:
		n = (n << 8) + c
	return n


def textProgress(n=100, t=0.1):
	import time
	for i in range(n):
		sys.stdout.write('\b\b\b\b##%3d' % (i+1))
		time.sleep(t)
	sys.stdout.write('\b\b\b')


def locate(lst, val):
	n = len(lst)
	if n == 0:
		return
	if val < lst[0]:
		return -0.5
	if val == lst[0]:
		return 0
	if val == lst[-1]:
		return n-1
	if val > lst[-1]:
		return n-0.5
	si = 0  # start index
	ei = n  # end index
	while ei-si > 1:
		mi = (ei+si)/2  # middle index
		if lst[mi] == val:
			return mi
		elif lst[mi] > val:
			ei = mi
			continue
		else:
			si = mi
			continue
	if ei-si == 1:
		return si+0.5


def locate2(lst, val, ind=1):
	n = len(lst)
	if n == 0:
		return
	if val < lst[0][ind]:
		return -0.5
	if val == lst[0][ind]:
		return 0
	if val == lst[-1][ind]:
		return n-1
	if val > lst[-1][ind]:
		return n-0.5
	si = 0
	ei = n
	while ei-si > 1:
		mi = (ei+si)/2
		if lst[mi][ind] == val:
			return mi
		elif lst[mi][ind] > val:
			ei = mi
			continue
		else:
			si = mi
		continue
	if ei-si == 1:
		return si+0.5


def xml2dict(xmlText):
	from xml.etree.ElementTree import XML, tostring
	xmlElems = XML(xmlText)
	for elem in xmlElems:
		elemText = tostring(elem)
		try:
			elem[0]
			elemElems = xml2dict()
		except:
			pass


def sortby(lst, n, reverse=False):
	nlist = [(x[n], x) for x in lst]
	nlist.sort(None, None, reverse)
	return [val for (key, val) in nlist]


def sortby_inplace(lst, n, reverse=False):
	lst[:] = [(x[n], x) for x in lst]
	lst.sort(None, None, reverse)
	lst[:] = [val for (key, val) in lst]
	return


def chBaseIntToStr(number, base):
	"""
		reverse function of int(str, base) and long(str, base)
	"""
	if not 2 <= base <= 36:
		raise ValueError('base must be in 2..36')
	abc = string.digits + string.ascii_letters
	result = ''
	if number < 0:
		number = -number
		sign = '-'
	else:
		sign = ''
	while True:
		number, rdigit = divmod(number, base)
		result = abc[rdigit] + result
		if number == 0:
			return sign + result
