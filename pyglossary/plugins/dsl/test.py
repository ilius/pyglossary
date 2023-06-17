import sys
from os.path import dirname

rootDir = dirname(dirname(dirname(dirname(__file__))))
sys.path.insert(0, rootDir)

from pyglossary.plugins.dsl.transform import Transformer

if __name__ == "__main__":
	input = sys.argv[1]
	tr = Transformer(
		input,
		current_key="HEADWORD",
	)
	result, err = tr.transform()
	if err:
		print(f"Error: {err} in {input!r}")
	else:
		print(result.output)
