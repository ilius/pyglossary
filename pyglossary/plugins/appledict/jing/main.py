from __future__ import annotations

"""Jing, a validator for RELAX NG and other schema languages."""

import logging
import subprocess
import sys
from os import path

__all__ = ["JingTestError", "main", "run"]

log = logging.getLogger("pyglossary")
log.setLevel(logging.DEBUG)


class JingTestError(subprocess.CalledProcessError):

	"""
	A exception that is raised when jing test failed, e.g. returned non-zero.
	the exit status will be stored in the `returncode` attribute.
	the `output` attribute also will store the output.
	"""

	def __init__(
		self,
		returncode: int,
		cmd: list[str],
		output: bytes,
	) -> None:
		super().__init__(returncode, cmd, output)

	def __str__(self) -> str:
		return "\n".join(
			[
				f"Jing check failed with exit code {self.returncode}:",
				"-" * 80,
				self.output,
			],
		)


def run(filename: str) -> None:
	"""
	Check whether the file named `filename` conforms to
	`AppleDictionarySchema.rng`.

	:returns: None
	:raises: JingTestError
	"""
	here = path.abspath(path.dirname(__file__))
	filename = path.abspath(filename)

	jing_jar_path = path.join(here, "jing", "bin", "jing.jar")
	rng_path = path.join(here, "DictionarySchema", "AppleDictionarySchema.rng")

	# -Xmxn Specifies the maximum size, in bytes, of the memory allocation pool
	# -- from `man 1 java`
	cmd = ["java", "-Xmx2G", "-jar", jing_jar_path, rng_path, filename]

	log.info("running Jing check:")
	log.info(str(cmd))
	log.info("...")

	pipe = subprocess.Popen(
		cmd,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
	)
	returncode = pipe.wait()
	output = pipe.communicate()[0]

	if returncode != 0:
		if returncode < 0:
			log.error(f"Jing was terminated by signal {-returncode}")
		elif returncode > 0:
			log.error(f"Jing returned {returncode}")
		raise JingTestError(returncode, cmd, output)

	log.info("Jing check successfully passed!")


def main() -> int:
	"""
	Run Jing test on given dictionary XML file with Apple Dictionary Schema.
	It's a command-line utility.
	"""
	if len(sys.argv) < 2:
		prog_name = path.basename(sys.argv[0])
		log.info(f"usage:\n  {prog_name} filename")
		return 1
	try:
		run(sys.argv[1])
		return 0
	except JingTestError as e:
		log.fatal(str(e))
		return e.returncode
