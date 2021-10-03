
## Aard 2 (.slob) ##

### General Information ###
Attribute | Value
--------- | -------
Name | Aard2Slob
snake_case_name | aard2_slob
Description | Aard 2 (.slob)
Extensions | `.slob`
Read support | Yes
Write support | Yes
Single-file | Yes
Kind | 🔢 binary
Sort-on-write | No (by default)
Wiki | [@itkach/slob/wiki](https://github.com/itkach/slob/wiki)
Website | [aarddict.org](http://aarddict.org/)



### Write options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------
`compression` | `zlib` | str | Compression Algorithm
`content_type` |  | str | Content Type
`file_size_approx` | `0` | int | split up by given approximate file size<br />examples: 100m, 1g
`separate_alternates` | `False` | bool | add alternate headwords as separate entries to slob
`word_title` | `False` | bool | add headwords title to begining of definition

### Dependencies for reading and writing ###
PyPI Links: [PyICU](https://pypi.org/project/PyICU)

To install, run:

    pip3 install PyICU


### PyICU ###
See [doc/pyicu.md](../pyicu.md) file for more detailed instructions on how to install PyICU.

### Dictionary Applications/Tools ###
Name & Website | License | Platforms
-------------- | ------- | ---------
[Aard 2 for Android](http://aarddict.org/) | GPL | Android
[Aard2 for Web](http://aarddict.org/) | MPL | Web
