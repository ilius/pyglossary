Feature-specific Requirements on [Termux](https://github.com/termux/termux-app)
---------------------------------------

- **Using `--remove-html-all` flag**

	+ `apt install libxml2 libxslt`
	+ `pip install lxml beautifulsoup4`


- **Reading from FreeDict, XDXF, JMDict, AppleDict Binary (.dictionary) or CC-CEDICT**

	+ `apt install libxml2 libxslt`
	+ `pip install lxml`

- **Reading from cc-kedict**

	+ `apt install libxml2 libxslt`
	+ `pip install lxml PyYAML`

- **Reading or writing Aard 2 (.slob)**

	+ `pip install PyICU`


- **Writing to Kobo E-Reader Dictionary**

	+ `pip install marisa-trie`


- **Reading from Zim**

	+ `apt install libzim`
	+ `pip install libzim`


- **Writing to AppleDict**

	+ `apt install libxml2 libxslt`
	+ `pip install lxml beautifulsoup4 html5lib`

