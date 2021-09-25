
### General Information ###
Name | Value
---- | -------
Name | Aard2Slob
snake_case_name | aard2_slob
Description | Aard 2 (.slob)
Extensions | `.slob`
Read support | Yes
Write support | Yes
Single-file | Yes
Kind | binary
Wiki | [wiki](https://github.com/itkach/slob/wiki)
Website | http://aarddict.org/


### Read options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------

### Write options ###
Name | Default | Type | Comment
---- | ------- | ---- | -------
`compression` | `zlib` | str | Compression Algorithm
`content_type` |  | str | Content Type
`file_size_approx` | `0` | int | split up by given approximate file size<br />examples: 100m, 1g
`separate_alternates` | `False` | bool | add alternate headwords as separate entries to slob
`word_title` | `False` | bool | add headwords title to begining of definition
