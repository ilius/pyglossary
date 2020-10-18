'\nThis is a python implementation of wcwidth() and wcswidth().\n\nhttps://github.com/jquast/wcwidth\n\nfrom Markus Kuhn\'s C code, retrieved from:\n\n    http://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c\n\nThis is an implementation of wcwidth() and wcswidth() (defined in\nIEEE Std 1002.1-2001) for Unicode.\n\nhttp://www.opengroup.org/onlinepubs/007904975/functions/wcwidth.html\nhttp://www.opengroup.org/onlinepubs/007904975/functions/wcswidth.html\n\nIn fixed-width output devices, Latin characters all occupy a single\n"cell" position of equal width, whereas ideographic CJK characters\noccupy two such cells. Interoperability between terminal-line\napplications and (teletype-style) character terminals using the\nUTF-8 encoding requires agreement on which character should advance\nthe cursor by how many cell positions. No established formal\nstandards exist at present on which Unicode character shall occupy\nhow many cell positions on character terminals. These routines are\na first attempt of defining such behavior based on simple rules\napplied to data provided by the Unicode Consortium.\n\nFor some graphical characters, the Unicode standard explicitly\ndefines a character-cell width via the definition of the East Asian\nFullWidth (F), Wide (W), Half-width (H), and Narrow (Na) classes.\nIn all these cases, there is no ambiguity about which width a\nterminal shall use. For characters in the East Asian Ambiguous (A)\nclass, the width choice depends purely on a preference of backward\ncompatibility with either historic CJK or Western practice.\nChoosing single-width for these characters is easy to justify as\nthe appropriate long-term solution, as the CJK practice of\ndisplaying these characters as double-width comes from historic\nimplementation simplicity (8-bit encoded characters were displayed\nsingle-width and 16-bit ones double-width, even for Greek,\nCyrillic, etc.) and not any typographic considerations.\n\nMuch less clear is the choice of width for the Not East Asian\n(Neutral) class. Existing practice does not dictate a width for any\nof these characters. It would nevertheless make sense\ntypographically to allocate two character cells to characters such\nas for instance EM SPACE or VOLUME INTEGRAL, which cannot be\nrepresented adequately with a single-width glyph. The following\nroutines at present merely assign a single-cell width to all\nneutral characters, in the interest of simplicity. This is not\nentirely satisfactory and should be reconsidered before\nestablishing a formal standard in this area. At the moment, the\ndecision which Not East Asian (Neutral) characters should be\nrepresented by double-width glyphs cannot yet be answered by\napplying a simple rule from the Unicode database content. Setting\nup a proper standard for the behavior of UTF-8 character terminals\nwill require a careful analysis not only of each Unicode character,\nbut also of each presentation form, something the author of these\nroutines has avoided to do so far.\n\nhttp://www.unicode.org/unicode/reports/tr11/\n\nLatest version: http://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c\n'
from __future__ import division
_B=None
_A='auto'
import os,sys,warnings
from .table_wide import WIDE_EASTASIAN
from .table_zero import ZERO_WIDTH
from .unicode_versions import list_versions
_UNICODE_CMPTABLE=_B
_PY3=sys.version_info[0]>=3
ZERO_WIDTH_CF=set([0,847,8203,8204,8205,8206,8207,8232,8233,8234,8235,8236,8237,8238,8288,8289,8290,8291])
def _bisearch(ucs,table):
	'\n    Auxiliary function for binary search in interval table.\n\n    :arg int ucs: Ordinal value of unicode character.\n    :arg list table: List of starting and ending ranges of ordinal values,\n        in form of ``[(start, end), ...]``.\n    :rtype: int\n    :returns: 1 if ordinal value ucs is found within lookup table, else 0.\n    ';B=ucs;A=table;E=0;C=len(A)-1
	if B<A[0][0]or B>A[C][1]:return 0
	while C>=E:
		D=(E+C)//2
		if B>A[D][1]:E=D+1
		elif B<A[D][0]:C=D-1
		else:return 1
	return 0
def wcwidth(wc,unicode_version=_A):
	"\n    Given one Unicode character, return its printable length on a terminal.\n\n    :param str wc: A single Unicode character.\n    :param str unicode_version: A Unicode version number, such as\n        ``'6.0.0'``, the list of available version levels may be\n        listed by pairing function :func:`list_versions`.\n\n        Any version string may be specified without error -- the nearest\n        matching version is selected.  When ``latest`` (default), the\n        highest Unicode version level is used.\n    :return: The width, in cells, necessary to display the character of\n        Unicode string character, ``wc``.  Returns 0 if the ``wc`` argument has\n        no printable effect on a terminal (such as NUL '\\0'), -1 if ``wc`` is\n        not printable, or has an indeterminate effect on the terminal, such as\n        a control character.  Otherwise, the number of column positions the\n        character occupies on a graphic terminal (1 or 2) is returned.\n    :rtype: int\n\n    The following have a column width of -1:\n\n        - C0 control characters (U+001 through U+01F).\n\n        - C1 control characters and DEL (U+07F through U+0A0).\n\n    The following have a column width of 0:\n\n    - Non-spacing and enclosing combining characters (general\n      category code Mn or Me in the Unicode database).\n\n    - NULL (``U+0000``).\n\n    - COMBINING GRAPHEME JOINER (``U+034F``).\n\n    - ZERO WIDTH SPACE (``U+200B``) *through*\n      RIGHT-TO-LEFT MARK (``U+200F``).\n\n    - LINE SEPARATOR (``U+2028``) *and*\n      PARAGRAPH SEPARATOR (``U+2029``).\n\n    - LEFT-TO-RIGHT EMBEDDING (``U+202A``) *through*\n      RIGHT-TO-LEFT OVERRIDE (``U+202E``).\n\n    - WORD JOINER (``U+2060``) *through*\n      INVISIBLE SEPARATOR (``U+2063``).\n\n    The following have a column width of 1:\n\n    - SOFT HYPHEN (``U+00AD``).\n\n    - All remaining characters, including all printable ISO 8859-1\n      and WGL4 characters, Unicode control characters, etc.\n\n    The following have a column width of 2:\n\n        - Spacing characters in the East Asian Wide (W) or East Asian\n          Full-width (F) category as defined in Unicode Technical\n          Report #11 have a column width of 2.\n\n         - Some kinds of Emoji or symbols.\n    ";A=ord(wc)
	if A in ZERO_WIDTH_CF:return 0
	if A<32 or 127<=A<160:return-1
	B=_wcmatch_version(unicode_version)
	if _bisearch(A,ZERO_WIDTH[B]):return 0
	return 1+_bisearch(A,WIDE_EASTASIAN[B])
def wcswidth(pwcs,n=_B,unicode_version=_A):
	'\n    Given a unicode string, return its printable length on a terminal.\n\n    :param str pwcs: Measure width of given unicode string.\n    :param int n: When ``n`` is None (default), return the length of the\n        entire string, otherwise width the first ``n`` characters specified.\n    :param str unicode_version: An explicit definition of the unicode version\n        level to use for determination, may be ``auto`` (default), which uses\n        the Environment Variable, ``UNICODE_VERSION`` if defined, or the latest\n        available unicode version, otherwise.\n    :rtype: int\n    :returns: The width, in cells, necessary to display the first ``n``\n        characters of the unicode string ``pwcs``.  Returns ``-1`` if\n        a non-printable character is encountered.\n    ';C=len(pwcs)if n is _B else n;D=slice(0,C);A=0
	for E in pwcs[D]:
		B=wcwidth(E,unicode_version)
		if B<0:return-1
		A+=B
	return A
def _wcversion_value(ver_string):'\n    Integer-mapped value of given dotted version string.\n\n    :param str ver_string: Unicode version string, of form ``n.n.n``.\n    :rtype: tuple(int)\n    :returns: tuple of digit tuples, ``tuple(int, [...])``.\n    ';A=tuple(map(int,ver_string.split('.')));return A
def _wcmatch_version(given_version):
	"\n    Return nearest matching supported Unicode version level.\n\n    If an exact match is not determined, the nearest lowest version level is\n    returned after a warning is emitted.  For example, given supported levels\n    ``4.1.0`` and ``5.0.0``, and a version string of ``4.9.9``, then ``4.1.0``\n    is selected and returned:\n\n    >>> _wcmatch_version('4.9.9')\n    '4.1.0'\n    >>> _wcmatch_version('8.0')\n    '8.0.0'\n    >>> _wcmatch_version('1')\n    '4.1.0'\n\n    :param str given_version: given version for compare, may be ``auto``\n        (default), to select Unicode Version from Environment Variable,\n        ``UNICODE_VERSION``. If the environment variable is not set, then the\n        latest is used.\n    :rtype: str\n    :returns: unicode string, or non-unicode ``str`` type for python 2\n        when given ``version`` is also type ``str``.\n    ";I='latest';A=given_version;D=not _PY3 and isinstance(A,str)
	if D:B=[A.encode()for A in list_versions()]
	else:B=list_versions()
	C=B[-1]
	if A in(_A,_A):A=os.environ.get('UNICODE_VERSION',I if not D else C.encode())
	if A in(I,I):return C if not D else C.encode()
	if A in B:return A if not D else A.encode()
	try:E=_wcversion_value(A)
	except ValueError:warnings.warn("UNICODE_VERSION value, {given_version!r}, is invalid. Value should be in form of `integer[.]+', the latest supported unicode version {latest_version!r} has been inferred.".format(given_version=A,latest_version=C));return C if not D else C.encode()
	F=B[0];J=_wcversion_value(F)
	if E<=J:warnings.warn('UNICODE_VERSION value, {given_version!r}, is lower than any available unicode version. Returning lowest version level, {earliest_version!r}'.format(given_version=A,earliest_version=F));return F if not D else F.encode()
	for (G,K) in enumerate(B):
		try:H=_wcversion_value(B[G+1])
		except IndexError:return C if not D else C.encode()
		if E==H[:len(E)]:return B[G+1]
		if H>E:return K
	assert False,('Code path unreachable',A,B)