def chBaseIntToList(number, base):
	result = []
	if number < 0:
		raise ValueError('number must be posotive integer')
	while True:
		number, rdigit = divmod(number, base)
		result = [rdigit] + result
		if number == 0:
			return result
