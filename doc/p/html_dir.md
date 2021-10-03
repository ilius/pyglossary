
## HTML Directory ##

### General Information ###
Attribute | Value
--------- | -------
Name | HtmlDir
snake_case_name | html_dir
Description | HTML Directory
Extensions | `.hdir`
Read support | No
Write support | Yes
Single-file | No
Kind | 📁 directory
Sort-on-write | No (by default)
Wiki | ―
Website | ―



### Write options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------
`css` |  | str | Path to css file
`dark` | `True` | bool | Use dark style
`encoding` | `utf-8` | str | Encoding/charset
`escape_defi` | `False` | bool | Escape definitions
`filename_format` | `{n:05d}.html` | str | Filename format, default: {n:05d}.html
`max_file_size` | `102400` | int | Maximum file size in bytes
`resources` | `True` | bool | Enable resources / data files
`word_title` | `True` | bool | Add headwords title to begining of definition


### Dependencies for writing ###
PyPI Links: [cachetools](https://pypi.org/project/cachetools)

To install, run

    pip3 install cachetools


