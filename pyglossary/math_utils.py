from typing import List

def chBaseIntToList(number: int, base: int) -> List[int]:
	result = []
	if number < 0:
		raise ValueError("number must be posotive integer")
	while True:
		number, rdigit = divmod(number, base)
		result = [rdigit] + result
		if number == 0:
			return result
