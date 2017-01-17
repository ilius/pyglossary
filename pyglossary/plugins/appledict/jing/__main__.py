"""main entry point"""

import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from . import main


log = logging.getLogger('root')
console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(logging.Formatter(
	'%(asctime)s: %(message)s'
))
log.addHandler(console_output_handler)
log.setLevel(logging.INFO)

main.main()
