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
| Sort key        | (`headword_lower`)                                                         |
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
| word_title       | `False` | bool | Add headwords title to beginning of definition                  |

### Dictionary Applications/Tools

| Name & Website                                                                               | Source code                                                        | License | Platforms           | Language |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------- | ------------------- | -------- |
| [StarDict-Editor (Tools)](https://github.com/huzheng001/stardict-3/blob/master/tools/README) | [@huzheng001/stardict-3](https://github.com/huzheng001/stardict-3) | GPL     | Linux, Windows, Mac | C        |
