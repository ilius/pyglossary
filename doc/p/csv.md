## CSV (.csv)

### General Information

| Attribute       | Value                                                                          |
| --------------- | ------------------------------------------------------------------------------ |
| Name            | Csv                                                                            |
| snake_case_name | csv                                                                            |
| Description     | CSV (.csv)                                                                     |
| Extensions      | `.csv`                                                                         |
| Read support    | Yes                                                                            |
| Write support   | Yes                                                                            |
| Single-file     | Yes                                                                            |
| Kind            | 📝 text                                                                         |
| Sort-on-write   | No (by default)                                                                |
| Sort key        | (`headword_lower`)                                                             |
| Wiki            | [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values) |
| Website         | ―                                                                              |

### Read options

| Name      | Default | Type | Comment          |
| --------- | ------- | ---- | ---------------- |
| encoding  | `utf-8` | str  | Encoding/charset |
| newline   | `\n`    | str  | Newline string   |
| delimiter | `,`     | str  | Column delimiter |

### Write options

| Name            | Default | Type | Comment                                        |
| --------------- | ------- | ---- | ---------------------------------------------- |
| encoding        | `utf-8` | str  | Encoding/charset                               |
| newline         | `\n`    | str  | Newline string                                 |
| resources       | `True`  | bool | Enable resources / data files                  |
| delimiter       | `,`     | str  | Column delimiter                               |
| add_defi_format | `False` | bool | enable adding defiFormat (m/h/x)               |
| enable_info     | `True`  | bool | Enable glossary info / metedata                |
| word_title      | `False` | bool | add headwords title to beginning of definition |

### Columns / file structure

Our supported CSV files consists of these columns:

- Main term (headword)
- Definiton / translation / article
- Comma-seperated alternative terms (optional) (needs to be quoted for multiple terms)

For example, with default `delimiter=","`, a line would like like:

```csv
word,translation,"inflection1,inflection2,inflection3"
```

Here is a simple script that creates such CSV file (without pyglossary library):
[doc/format-desc/csv-create.py](../format-desc/csv-create.py)

### Dictionary Applications/Tools

| Name & Website                                                         | Source code                                                  | License     | Platforms           | Language |
| ---------------------------------------------------------------------- | ------------------------------------------------------------ | ----------- | ------------------- | -------- |
| [LibreOffice Calc](https://www.libreoffice.org/discover/calc/)         | [git.libreoffice.org/core](https://git.libreoffice.org/core) | MPL/GPL     | Linux, Windows, Mac | C++      |
| [Microsoft Excel](https://www.microsoft.com/en-us/microsoft-365/excel) | ―                                                            | Proprietary | Windows             |          |

### Related Formats

- [Tabfile (.txt, .dic)](./tabfile.md)
