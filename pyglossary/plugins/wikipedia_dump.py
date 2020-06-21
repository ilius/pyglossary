# -*- coding: utf-8 -*-

from time import time as now
import re

from formats_common import *

enable = False
format = "WikipediaDump"
description = "Wikipedia Dump(Static HTML)"
extensions = [".wiki"]
optionsProp = {
	"encoding": EncodingOption(),
}
depends = {}

BeautifulSoup = None

def loadBeautifulSoup():
	global BeautifulSoup
	try:
		import bs4 as BeautifulSoup
	except:
		import BeautifulSoup
	if int(BeautifulSoup.__version__.split(".")[0]) < 4:
		raise ImportError(
			"BeautifulSoup is too old, required at least version 4, "
			f"{BeautifulSoup.__version__ !r} found.\n"
			"Please run `sudo pip3 install lxml beautifulsoup4 html5lib`"
		)

class Reader(object):
	specialPattern = re.compile(r".*~[^_]")
	def __init__(self, glos):
		self._glos = glos
		self._rootDir = ""
		self._articlesDir = ""
		self._len = None
		self._specialCount = 0
		# self._alts = {}
		# { word => alts }
		# where alts is str (one word), or list of strs
		# we can't recognize alternates unless we keep all data in memory
		# or scan the whole directiry and read all files twice

	def open(self, dirname):
		if not isdir(dirname):
			raise IOError(f"{dirname} is not a directory")
		self._rootDir = dirname
		self._articlesDir = join(self._rootDir, "articles")

	def close(self):
		self._rootDir = ""
		self._articlesDir = ""
		self._len = None
		# self._alts = {}

	def __len__(self):
		if not self._articlesDir:
			log.error(
				"WikipediaDump: called len(reader) while it's not open"
			)
			return 0
		if self._len is None:
			t0 = now()
			log.info("Counting articles...")
			self._len = sum(
				len(files)
				for _, _, files in os.walk(self._articlesDir)
			)
			log.debug(f"Counting articles took {now()-t0:.2f} seconds", )
			log.info(f"Found {self._len} articles")
		return self._len

	def __iter__(self):
		if not self._articlesDir:
			log.error(
				"WikipediaDump: trying to iterate over reader"
				" while it's not open"
			)
			raise StopIteration
		for dirpath, dirs, files in os.walk(self._articlesDir):
			# dirpathRel = dirpath[len(self._articlesDir):].lstrip("/")
			# dirParts = dirpathRel.split(os.sep)  # test on windows FIXME
			# prefix = "".join([
			#	chr(int(x, 16)) if len(x)==2 else x
			#	for x in dirParts
			# ])
			dirs.sort()
			files.sort()
			for fname_html in files:
				fpath = join(dirpath, fname_html)
				fname, ext = splitext(fname_html)
				# fpathRel = join(dirpathRel, fname_html)
				if ext != ".html":
					log.warning(f"unkown article extension: {fname_ext}")
					continue
				if self.isSpecialByPath(fname):  # , prefix
					# log.debug(f"Skipping special page file: {fpathRel}")
					self._specialCount += 1
					yield None  # updates progressbar
					continue
				word = fname.replace("_", " ").replace("~", ":")
				defi = self.parseArticle(word, fpath)
				if not defi:
					yield None  # updates progressbar
					continue

				yield self._glos.newEntry(word, defi)
		log.info(f"Skipped {self._specialCount} special page files")

	def isSpecialByPath(self, fname):  # , d_prefix
		"""
			fname: str
			d_prefix: str, with length of 3
				this is the joint string version of directory relative path
		"""
		return re.match(self.specialPattern, fname)
		# assert len(d_prefix) == 3
		# f_prefix = fname[:3].lower()
		# if f_prefix == d_prefix:
		#	return False
		# if len(f_prefix) < 3:
		#	if f_prefix == d_prefix.rstrip("_"):
		#		return False
		# return True
		# if "~" not in fname:
		#	return False
		# if fname[0] == dirParts[0]:
		#	return False
		# if list(fname[:3]) != dirParts:
		#	log.debug(f"dirParts={dirParts!r}, fname={fname!r}")
		# l_fname = fname.lower()
		# for ext in ("png", "jpg", "jpeg", "gif", "svg", "pdf", "js"):
		#	if "." + ext in l_fname:
		#		return True
		# return True

	def parseArticle(self, word, fpath):
		if BeautifulSoup is None:
			loadBeautifulSoup()
		try:
			with open(fpath) as fileObj:
				text = fileObj.read()
		except UnicodeDecodeError:
			log.error(f"error decoding file {fpath!r}, not UTF-8")
			return
		except:
			log.exception(f"error reading file {fpath!r}")
			return

		root = BeautifulSoup(text, "lxml")
		body = root.body
		if not body:
			return

#		if body.p and body.p.text.startswith("Redirecting to "):
#			toWord = body.p.text[len("Redirecting to "):]
#			try:
#				fromWords = self._alts[toWord]
#			except KeyError:
#				self._alts[toWord] = word
#			else:
#				if isinstance(fromWords, str):
#					self._alts[toWord] = [fromWords, word]
#				else:
#					fromWords.append(word)
#			return
#		try:
#			alts = self._alts[word]

		if body.p and body.p.text.startswith("Redirecting to "):
			toWord = body.p.text[len("Redirecting to "):]
			return f"↳ <a href=\"bword://{toWord}\">{toWord}</a>"
			# "↳" does not look good for RTL languages FIXME

		try:
			content = body.find(id="column-content").find(id="content")
		except AttributeError:
			content = None
		if not content:
			log.warning(f"could not find \"content\" element: {fpath}")
			return

		try:
			firstHeading = content.find("h1", class_="firstHeading").text
		except AttributeError:
			log.warning(f"could not find \"firstHeading\" element: {fpath}")
			return

		if firstHeading != word:
			log.debug(f"word={firstHeading!r}, firstHeading={word!r}")

		bodyContent = content.find(id="bodyContent")
		if not bodyContent:
			log.warning(f"could not find \"bodyContent\" element: {fpath}")
			return

		# FIXME
		return "".join([str(tag) for tag in bodyContent.contents])
