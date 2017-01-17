from .text_utils import replacePostSpaceChar


def faEditStr(st):
	return replacePostSpaceChar(
		st.replace('ي', 'ی')
		  .replace('ك', 'ک')
		  .replace('ۂ', 'هٔ')
		  .replace('ہ', 'ه'),
		'،',
	)
