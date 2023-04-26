## Entry Filters

| Name                         | Default Enabled | Command Flags                        | Description                                                                 |
| ---------------------------- | --------------- | ------------------------------------ | --------------------------------------------------------------------------- |
| `trim_whitespaces`           | Yes             |                                      | Remove leading/trailing whitespaces from word(s) and definition             |
| `non_empty_word`             | Yes             |                                      | Skip entries with empty word                                                |
| `skip_resources`             | No              | `--skip-resources`                   | Skip resources / data files                                                 |
| `utf8_check`                 | No              | `--utf8-check`<br/>`--no-utf8-check` | Fix Unicode in word(s) and definition                                       |
| `lower`                      | No              | `--lower`<br/>`--no-lower`           | Lowercase word(s)                                                           |
| `skip_duplicate_headword`    | No              | `--skip-duplicate-headword`          | Skip entries with a duplicate headword                                      |
| `trim_arabic_diacritics`     | No              | `--trim-arabic-diacritics`           | Trim Arabic diacritics from headword                                        |
| `rtl`                        | No              | `--rtl`                              | Make definition right-to-left                                               |
| `remove_html_all`            | No              | `--remove-html-all`                  | Remove all HTML tags (not their contents) from definition                   |
| `remove_html`                | No              | `--remove-html`                      | Remove given comma-separated HTML tags (not their contents) from definition |
| `normalize_html`             | No              | `--normalize-html`                   | Normalize HTML tags in definition (WIP)                                     |
| `unescape_word_links`        | No              | `--unescape-word-links`              | Unescape Word Links                                                         |
| `lang`                       | Yes             |                                      | Language-specific cleanup/fixes                                             |
| `non_empty_word`             | Yes             |                                      | Skip entries with empty word                                                |
| `non_empty_defi`             | Yes             |                                      | Skip entries with empty definition                                          |
| `remove_empty_dup_alt_words` | Yes             |                                      | Remove empty and duplicate alternate words                                  |
| `prevent_duplicate_words`    | No              |                                      | Prevent duplicate words                                                     |
| `strip_full_html`            | No              |                                      | Replace a full HTML document with it's body                                 |
| `progressbar`                | No              |                                      | Progress Bar                                                                |
| `max_memory_usage`           | No              |                                      | Show Max Memory Usage                                                       |
