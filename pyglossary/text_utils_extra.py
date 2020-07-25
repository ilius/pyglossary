def intToBytes2(n, stLen=0):
	bs = b''
	while n > 0:
		bs = bytes([n & 255]) + bs
		n >>= 8
	return bs.rjust(stLen, b'\x00')


def intToBytes3(n, stLen=0):
	return bytes((
		(n >> (i << 3)) & 0xff
		for i in range(int(ceil(log(n, 256))) - 1, -1, -1)
	)).rjust(stLen, b'\x00')


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
