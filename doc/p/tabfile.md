
## Tabfile (.txt, .dic) ##

### General Information ###
Attribute | Value
--------- | -------
Name | Tabfile
snake_case_name | tabfile
Description | Tabfile (.txt, .dic)
Extensions | `.txt`, `.tab`, `.tsv`
Read support | Yes
Write support | Yes
Single-file | Yes
Kind | 📝 text
Sort-on-write | No (by default)
Wiki | [Tab-separated values](https://en.wikipedia.org/wiki/Tab-separated_values)
Website | ―


### Read options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------
`encoding` | `utf-8` | str | Encoding/charset

### Write options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------
`enable_info` | `True` | bool | Enable glossary info / metedata
`encoding` | `utf-8` | str | Encoding/charset
`file_size_approx` | `0` | int | Split up by given approximate file size<br />examples: 100m, 1g
`resources` | `True` | bool | Enable resources / data files
`word_title` | `False` | bool | Add headwords title to begining of definition



