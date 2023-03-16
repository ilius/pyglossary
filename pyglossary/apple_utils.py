# list of css params that are defined in Apple's WebKit and used in
# Apple dictionary files (binary and source formats)
# but to make the css work in other dictionaries, we have to substitute them

# default / system font of Mac OS X is Helvetica Neue / Neue Helvetica
# https://en.wikipedia.org/wiki/Helvetica
# list of fonts that are shipped with Mac OS X
# https://en.wikipedia.org/wiki/List_of_typefaces_included_with_macOS
# but we actually prefer to set font that are free and more widely available
# in all operating systems

import re
import typing.re

from .core import log

cssMapping: "dict[str, str]" = {
	# I didn't actually find these font values:
	"-apple-system-body": '"Helvetica Neue"',
	"-apple-system": '"Helvetica Neue"',

	# I also didn't find these values:
	"-webkit-border-bottom-left-radius": "5",
	"-webkit-border-bottom-right-radius": "5",
	"-webkit-border-radius": "5",
	"-webkit-border-top-left-radius": "5",
	"-webkit-border-top-right-radius": "5",
	# "-webkit-hyphens"  # used as key
	"-webkit-link": "rgb(0, 0, 238)",  # color of <a> links

	"-webkit-control": "normal normal normal normal 13px/normal system-ui",
	"-webkit-mini-control": "normal normal normal normal 9px/normal system-ui",
	"-webkit-small-control": "normal normal normal normal 11px/normal system-ui",

	"-apple-system-alternate-selected-text": "rgb(255, 255, 255)",
	"-apple-system-blue": "rgb(0, 122, 255)",
	"-apple-system-brown": "rgb(162, 132, 94)",
	"-apple-system-container-border": "rgba(0, 0, 0, 0.247)",
	"-apple-system-control-accent": "rgb(0, 122, 255)",
	"-apple-system-control-background": "rgb(255, 255, 255)",
	"-apple-system-even-alternating-content-background": "rgb(255, 255, 255)",
	"-apple-system-find-highlight-background": "rgb(255, 255, 0)",
	"-apple-system-gray": "rgb(142, 142, 147)",
	"-apple-system-green": "rgb(40, 205, 65)",
	"-apple-system-grid": "rgb(230, 230, 230)",
	"-apple-system-header-text": "rgba(0, 0, 0, 0.847)",
	"-apple-system-label": "rgba(0, 0, 0, 0.847)",
	"-apple-system-odd-alternating-content-background": "rgb(244, 245, 245)",
	"-apple-system-orange": "rgb(255, 149, 0)",
	"-apple-system-pink": "rgb(255, 45, 85)",
	"-apple-system-placeholder-text": "rgba(0, 0, 0, 0.247)",
	"-apple-system-purple": "rgb(175, 82, 222)",
	"-apple-system-quaternary-label": "rgba(0, 0, 0, 0.098)",
	"-apple-system-red": "rgb(255, 59, 48)",
	"-apple-system-secondary-label": "rgba(0, 0, 0, 0.498)",
	"-apple-system-selected-content-background": "rgb(0, 99, 225)",
	"-apple-system-selected-text": "rgb(0, 0, 0)",
	"-apple-system-selected-text-background": "rgba(128, 188, 254, 0.6)",
	"-apple-system-separator": "rgba(0, 0, 0, 0.098)",
	"-apple-system-tertiary-label": "rgba(0, 0, 0, 0.26)",
	"-apple-system-text-background": "rgb(255, 255, 255)",
	"-apple-system-unemphasized-selected-content-background": "rgb(220, 220, 220)",
	"-apple-system-unemphasized-selected-text": "rgb(0, 0, 0)",
	"-apple-system-unemphasized-selected-text-background": "rgb(220, 220, 220)",
	"-apple-system-yellow": "rgb(255, 204, 0)",
	"-apple-wireless-playback-target-active": "rgb(0, 122, 255)",
}

cssParamPattern = re.compile(
	r"(-(apple|webkit)-[a-z\-]+)",
)

def _subCSS(m: "typing.re.Match") -> str:
	key = m.group(0)
	value = cssMapping.get(key)
	if value is None:
		log.warning(f"unrecognized CSS param: {key!r}")
		return key
	return value

def substituteAppleCSS(cssText: str) -> str:
	return cssParamPattern.sub(_subCSS, cssText)
