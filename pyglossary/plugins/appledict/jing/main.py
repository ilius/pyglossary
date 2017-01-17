"""Jing, a validator for RELAX NG and other schema languages."""

import logging
from os import path
import subprocess
import sys

__all__ = ['JingTestError', 'run', 'main']

log = logging.getLogger('root')
log.setLevel(logging.DEBUG)


class JingTestError(subprocess.CalledProcessError):
	"""this exception raised when jing test failed, e.g. returned non-zero.
	   the exit status will be stored in the `returncode` attribute.
	   the `output` attribute also will store the output.
	"""

	def __init__(self, returncode, cmd, output):
		super(JingTestError, self).__init__(returncode, cmd, output)

	def __str__(self):
		return 'Jing check failed with exit code %d:\n%s\n%s' %\
			(self.returncode, '-' * 80, self.output)


def run(filename):
	"""run(filename)

	check whether the file named `filename` conforms to
	`AppleDictionarySchema.rng`.

	:returns: None
	:raises: JingTestError
	"""
	here = path.abspath(path.dirname(__file__))
	filename = path.abspath(filename)

	jing_jar_path = path.join(here, 'jing', 'bin', 'jing.jar')
	rng_path = path.join(here, 'DictionarySchema', 'AppleDictionarySchema.rng')

	# -Xmxn Specifies the maximum size, in bytes, of the memory allocation
	#	   pool.
	# -- from `man 1 java`
	args = ['java', '-Xmx2G', '-jar', jing_jar_path, rng_path, filename]
	cmd = ' '.join(args)

	log.info('running Jing check:')
	log.info(cmd)
	log.info('...')

	pipe = subprocess.Popen(args,
							stdout=subprocess.PIPE,
							stderr=subprocess.STDOUT)
	returncode = pipe.wait()
	output = pipe.communicate()[0]

	if returncode != 0:
		if returncode < 0:
			log.error('Jing was terminated by signal %d' % -returncode)
		elif returncode > 0:
			log.error('Jing returned %d' % returncode)
		raise JingTestError(returncode, cmd, output)
	else:
		log.info('Jing check successfully passed!')


def main():
	"""a command-line utility, runs Jing test on given dictionary XML
	   file with Apple Dictionary Schema.
	"""
	if len(sys.argv) < 2:
		prog_name = path.basename(sys.argv[0])
		print("usage:\n  %s filename" % prog_name)
		exit(1)
	try:
		run(sys.argv[1])
	except JingTestError as e:
		log.fatal(str(e))
		exit(e.returncode)
