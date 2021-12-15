## Tabfile (.txt, .dic)

### General Information

| Attribute       | Value                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| Name            | Tabfile                                                                    |
| snake_case_name | tabfile                                                                    |
| Description     | Tabfile (.txt, .dic)                                                       |
| Extensions      | `.txt`, `.tab`, `.tsv`                                                     |
| Read support    | Yes                                                                        |
| Write support   | Yes                                                                        |
| Single-file     | Yes                                                                        |
| Kind            | 📝 text                                                                     |
| Sort-on-write   | default_no                                                                 |
| Wiki            | [Tab-separated values](https://en.wikipedia.org/wiki/Tab-separated_values) |
| Website         | ―                                                                          |

### Read options

| Name     | Default | Type | Comment          |
| -------- | ------- | ---- | ---------------- |
| encoding | `utf-8` | str  | Encoding/charset |

### Write options

| Name             | Default | Type | Comment                                                         |
| ---------------- | ------- | ---- | --------------------------------------------------------------- |
| encoding         | `utf-8` | str  | Encoding/charset                                                |
| enable_info      | `True`  | bool | Enable glossary info / metedata                                 |
| resources        | `True`  | bool | Enable resources / data files                                   |
| file_size_approx | `0`     | int  | Split up by given approximate file size<br />examples: 100m, 1g |
| word_title       | `False` | bool | Add headwords title to begining of definition                   |




