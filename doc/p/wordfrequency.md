## WordFrequency.info COCA lemma list (.wordfrequency)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/wordfrequency/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                           |
| --------------- | --------------------------------------------------------------- |
| Name            | WordFrequency                                                   |
| snake_case_name | wordfrequency                                                   |
| Description     | WordFrequency.info COCA lemma list (.wordfrequency)             |
| Extensions      | `.wordfrequency`                                                |
| Read support    | Yes                                                             |
| Write support   | No                                                              |
| Single-file     | Yes                                                             |
| Kind            | 📝 text                                                          |
| Wiki            | ―                                                               |
| Website         | [Word frequency data (COCA)](<https://www.wordfrequency.info/>) |

### Read options

| Name       | Default | Type | Comment          |
| ---------- | ------- | ---- | ---------------- |
| encoding   | `utf-8` | str  | Encoding/charset |
| gram_color | `green` | str  | Grammar color    |

### Input format

Tab-separated lemma frequency lists from [WordFrequency.info](https://www.wordfrequency.info/)
(COCA corpus), e.g. `lemmas_60k.txt`.

Use the `.wordfrequency` extension, or pass `formatName=WordFrequencyInfo` for `.txt` files.
