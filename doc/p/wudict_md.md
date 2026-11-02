## wudict markdown (.wudict.md)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/wudict_md/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute | Value |
| --------- | ----- |
| Name | WudictMarkdown |
| snake_case_name | wudict_md |
| Description | wudict markdown (.wudict.md) |
| Extensions | `.md` |
| Read support | Yes |
| Write support | Yes |
| Single-file | Yes |
| Kind | 📝 text |
| Sort-on-write | No (by default) |
| Sort key | (`headword_lower`) |
| Wiki | ― |
| Website | [WuDict markdown](https://github.com/wuweidict/wudict/blob/master/docs/WUDICT-MARKDOWN.md) |

### Read options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| resources | `True` | bool | Read and write resources (<name>.wudict.files) |

### Write options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| mode | `html` | str | html (default): each article's HTML kept; clean: markdown only, lossy |
| resources | `True` | bool | Read and write resources (<name>.wudict.files) |

### Dependencies for reading and writing

PyPI Links: [markdown-it-py](https://pypi.org/project/markdown-it-py)

To install, run:

```sh
pip3 install markdown-it-py
```

One dictionary per file: `# Title`, then `wudict: 1` on line 2, then
`key: value` header lines. Each entry is a `## headword` heading, with its
other spellings as more `##` headings right under it; its body is standard
markdown. See docs/WUDICT-MARKDOWN.md in the wudict repository.
