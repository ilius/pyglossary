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
| Sort-on-write   | default_no                                                                     |
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

### Dictionary Applications/Tools

| Name & Website                                                         | Source code | License     | Platforms           | Language |
| ---------------------------------------------------------------------- | ----------- | ----------- | ------------------- | -------- |
| [LibreOffice Calc](https://www.libreoffice.org/discover/calc/)         | ―           | MPL/GPL     | Linux, Windows, Mac |          |
| [Microsoft Excel](https://www.microsoft.com/en-us/microsoft-365/excel) | ―           | Proprietary | Windows             |          |
