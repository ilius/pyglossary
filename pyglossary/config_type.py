from typing import NotRequired, TypedDict

# NotRequired is added in Python 3.11


class ConfigType(TypedDict):
	log_time: NotRequired[bool]
	cleanup: NotRequired[bool]
	auto_sqlite: NotRequired[bool]
	lower: NotRequired[bool]
	utf8_check: NotRequired[bool]
	enable_alts: NotRequired[bool]
	skip_resources: NotRequired[bool]
	rtl: NotRequired[bool]
	remove_html: NotRequired[str]
	remove_html_all: NotRequired[bool]
	normalize_html: NotRequired[bool]
	save_info_json: NotRequired[bool]
	skip_duplicate_headword: NotRequired[bool]
	trim_arabic_diacritics: NotRequired[bool]
	unescape_word_links: NotRequired[bool]
	# color.enable.cmd.unix: bool
	# color.enable.cmd.windows: bool
	# color.cmd.critical: int
	# color.cmd.error: int
	# color.cmd.warning: int
	# cmdi.prompt.indent.str: str
	# cmdi.prompt.indent.color: int
	# cmdi.prompt.msg.color: int
	# cmdi.msg.color: int
	# ui_autoSetFormat: bool
	# tk.progressbar.color.fill: str
	# tk.progressbar.color.background: str
	# tk.progressbar.color.text: str
	# tk.progressbar.font: str
	reverse_matchWord: NotRequired[bool]
	reverse_showRel: NotRequired[str]
	reverse_saveStep: NotRequired[int]
	reverse_minRel: NotRequired[float]
	reverse_maxNum: NotRequired[float]
	reverse_includeDefs: NotRequired[bool]
