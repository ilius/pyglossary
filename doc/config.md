
## Configuration Parameters ##

Name | Command Flags | Type | Default | Comment
---- | ------------- | ---- | ------- | -------
`log_time` | `--log-time`<br/>`--no-log-time` | bool | `False` | show date and time in logs
`cleanup` | `--cleanup`<br/>`--no-cleanup` | bool | `True` | cleanup cache or temporary files after conversion
`lower` | `--lower`<br/>`--no-lower` | bool | `False` | lowercase words before writing
`utf8_check` | `--utf8-check`<br/>`--no-utf8-check` | bool | `True` | ensure entries contain valid UTF-8 strings
`enable_alts` | `--alts`<br/>`--no-alts` | bool | `True` | 
`skip_resources` | `--skip-resources` | bool | `False` | skip resources (images, audio, etc)
`rtl` | `--rtl` | bool | `False` | mark all definitions as Right-To-Left (definitions must be HTML)
`remove_html` | `--remove-html` | str |  | remove given html tags (comma-separated) from definitions
`remove_html_all` | `--remove-html-all` | bool | `False` | remove all html tags from definitions
`normalize_html` | `--normalize-html` | bool | `False` | lowercase and normalize html tags in definitions
`save_info_json` | `--info` | bool | `False` | save glossary info as json file with .info extension
`ui_autoSetFormat` |  | bool | `True` | 
`reverse_matchWord` |  | bool | `True` | 
`reverse_showRel` |  | str | `Percent` | 
`reverse_saveStep` |  | int | `1000` | 
`reverse_minRel` |  | float | `0.3` | 
`reverse_maxNum` |  | int | `-1` | 
`reverse_includeDefs` |  | bool | `False` | 

## Configuration Files ##
The default configuration values are stored in [config.json](../config.json) file in source/installation directory.

The user configuration file - if exists - will override default configuration values.
The location of this file depends on the operating system:

- Linux or BSD: `~/.pyglossary/config.json`
- Mac: `~/Library/Preferences/PyGlossary/config.json`
- Windows: `C:\Users\USERNAME\AppData\Roaming\PyGlossary\config.json`
