# Copyright (c) 2012-2015 Tyler Kennedy <tk@tkte.ch>. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# --
#
# Code to convert Python strings to/from Java's modified UTF-8 encoding.
# The code is from https://github.com/TkTech/mutf8 (MIT License) with fixes
# by @gentlegiantJGC (https://github.com/TkTech/mutf8/pull/7).

__all__ = ["decode_modified_utf8", "encode_modified_utf8"]


def decode_modified_utf8(s: bytes) -> str:
	"""
	Decodes a bytestring containing modified UTF-8 as defined in section
	4.4.7 of the JVM specification.

	:param s: bytestring to be converted.
	:returns: A unicode representation of the original string.
	"""
	s_out = []
	s_len = len(s)
	s_ix = 0

	while s_ix < s_len:
		b1 = s[s_ix]
		s_ix += 1

		if b1 == 0:
			raise UnicodeDecodeError(
				"mutf-8",
				s,
				s_ix - 1,
				s_ix,
				"Embedded NULL byte in input.",
			)
		if b1 < 0x80:
			# ASCII/one-byte codepoint.
			s_out.append(chr(b1))
		elif (b1 & 0xE0) == 0xC0:
			# Two-byte codepoint.
			if s_ix >= s_len:
				raise UnicodeDecodeError(
					"mutf-8",
					s,
					s_ix - 1,
					s_ix,
					"2-byte codepoint started, but input too short to finish.",
				)

			s_out.append(
				chr(
					(b1 & 0x1F) << 0x06 | (s[s_ix] & 0x3F),
				),
			)
			s_ix += 1
		elif (b1 & 0xF0) == 0xE0:
			# Three-byte codepoint.
			if s_ix + 1 >= s_len:
				raise UnicodeDecodeError(
					"mutf-8",
					s,
					s_ix - 1,
					s_ix,
					"3-byte or 6-byte codepoint started, but input too"
					" short to finish.",
				)

			b2 = s[s_ix]
			b3 = s[s_ix + 1]

			if b1 == 0xED and (b2 & 0xF0) == 0xA0:
				# Possible six-byte codepoint.
				if s_ix + 4 >= s_len:
					raise UnicodeDecodeError(
						"mutf-8",
						s,
						s_ix - 1,
						s_ix,
						"3-byte or 6-byte codepoint started, but input too"
						" short to finish.",
					)

				b4 = s[s_ix + 2]
				b5 = s[s_ix + 3]
				b6 = s[s_ix + 4]

				if b4 == 0xED and (b5 & 0xF0) == 0xB0:
					# Definite six-byte codepoint.
					s_out.append(
						chr(
							0x10000
							+ (
								(b2 & 0x0F) << 0x10
								| (b3 & 0x3F) << 0x0A
								| (b5 & 0x0F) << 0x06
								| (b6 & 0x3F)
							),
						),
					)
					s_ix += 5
					continue

			s_out.append(
				chr(
					(b1 & 0x0F) << 0x0C | (b2 & 0x3F) << 0x06 | (b3 & 0x3F),
				),
			)
			s_ix += 2
		else:
			raise RuntimeError

	return "".join(s_out)


def encode_modified_utf8(u: str) -> bytes:
	"""
	Encodes a unicode string as modified UTF-8 as defined in section 4.4.7
	of the JVM specification.

	:param u: unicode string to be converted.
	:returns: A decoded bytearray.
	"""
	final_string = bytearray()

	for c in (ord(char) for char in u):
		if c == 0x00:
			# NULL byte encoding shortcircuit.
			final_string.extend([0xC0, 0x80])
		elif c <= 0x7F:
			# ASCII
			final_string.append(c)
		elif c <= 0x7FF:
			# Two-byte codepoint.
			final_string.extend(
				[
					(0xC0 | (0x1F & (c >> 0x06))),
					(0x80 | (0x3F & c)),
				],
			)
		elif c <= 0xFFFF:
			# Three-byte codepoint.
			final_string.extend(
				[
					(0xE0 | (0x0F & (c >> 0x0C))),
					(0x80 | (0x3F & (c >> 0x06))),
					(0x80 | (0x3F & c)),
				],
			)
		else:
			# Six-byte codepoint.
			final_string.extend(
				[
					0xED,
					0xA0 | ((c >> 0x10) - 1 & 0x0F),
					0x80 | ((c >> 0x0A) & 0x3F),
					0xED,
					0xB0 | ((c >> 0x06) & 0x0F),
					0x80 | (c & 0x3F),
				],
			)

	return bytes(final_string)
