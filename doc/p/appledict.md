## AppleDict Source

### General Information

| Attribute       | Value                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------- |
| Name            | AppleDict                                                                                     |
| snake_case_name | appledict                                                                                     |
| Description     | AppleDict Source                                                                              |
| Extensions      | `.apple`                                                                                      |
| Read support    | No                                                                                            |
| Write support   | Yes                                                                                           |
| Single-file     | No                                                                                            |
| Kind            | 📁 directory                                                                                   |
| Sort-on-write   | default_no                                                                                    |
| Sort key        | (`headword_lower`)                                                                            |
| Wiki            | ―                                                                                             |
| Website         | [Dictionary User Guide for Mac](https://support.apple.com/en-gu/guide/dictionary/welcome/mac) |

### Write options

| Name              | Default | Type | Comment                                  |
| ----------------- | ------- | ---- | ---------------------------------------- |
| clean_html        | `True`  | bool | use BeautifulSoup parser                 |
| css               |         | str  | custom .css file path                    |
| xsl               |         | str  | custom XSL transformations file path     |
| default_prefs     | `None`  | dict | default prefs in python dict format      |
| prefs_html        |         | str  | preferences XHTML file path              |
| front_back_matter |         | str  | XML file path with top-level tag         |
| jing              | `False` | bool | run Jing check on generated XML          |
| indexes           |         | str  | Additional indexes to dictionary entries |

### Dependencies for writing

PyPI Links: [lxml](https://pypi.org/project/lxml), [beautifulsoup4](https://pypi.org/project/beautifulsoup4), [html5lib](https://pypi.org/project/html5lib)

To install, run

```sh
pip3 install lxml beautifulsoup4 html5lib
```

### Also see:

See [doc/apple.md](../apple.md) for additional AppleDict instructions.

### Dictionary Applications/Tools

| Name & Website                                                                              | Source code | License | Platforms | Language |
| ------------------------------------------------------------------------------------------- | ----------- | ------- | --------- | -------- |
| [Dictionary Development Kit](https://github.com/SebastianSzturo/Dictionary-Development-Kit) | ―           | Unknown | Mac       |          |
