# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

datas = [
	("about", "."),
	("license-dialog", "."),
	("help", "."),
	("res/*", "res"),
	("pyglossary/*.py", "."),
	("pyglossary/plugins/*", "plugins"),
	("pyglossary/plugin_lib/*", "plugin_lib"),
	("pyglossary/langs/*", "langs"),
	("pyglossary/ui/*.py", "ui"),
	("pyglossary/ui/progressbar/*.py", "ui/progressbar"),
	("pyglossary/ui/gtk3_utils/*.py", "ui/gtk3_utils"),
	("pyglossary/ui/wcwidth/*.py", "ui/wcwidth"),
	("doc/babylon/*", "doc/babylon"),
	("doc/non-gui_examples/*", "doc/non-gui_examples"),
]

a = Analysis(
	['pyglossary.pyw'],
	pathex=['D:\\pyglossary'],
	binaries=[],
	datas=datas,
	hiddenimports=[],
	hookspath=[],
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False,
)
pyz = PYZ(
	a.pure, a.zipped_data,
	cipher=block_cipher,
)
exe = EXE(
	pyz,
	a.scripts,
	[],
	exclude_binaries=True,
	name='pyglossary',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=True,
)
coll = COLLECT(
	exe,
	a.binaries,
	a.zipfiles,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name='pyglossary',
)
