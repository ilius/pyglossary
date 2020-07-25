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
