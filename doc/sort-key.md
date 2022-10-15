# Sort Key

## Supported `sortKey` names / `--sort-key` argument values

| Name/Value             | Description               | Default for formats                               | Supports `--sort-locale` |
| ---------------------- | ------------------------- | ------------------------------------------------- | :----------------------: |
| `headword`             | Headword                  |                                                   | Yes                      |
| `headword_lower`       | Lowercase Headword        | All other formats (given `--sort`)                | Yes                      |
| `headword_bytes_lower` | ASCII-Lowercase Headword  |                                                   | No                       |
| `stardict`             | StarDict                  | [StarDict](./p/stardict.md)                       | No                       |
| `ebook`                | E-Book (prefix length: 2) | [EPUB-2](./p/epub2.md), [Mobipocket](./p/mobi.md) | No                       |
| `ebook_length3`        | E-Book (prefix length: 3) |                                                   | No                       |
| `dicformids`           | DictionaryForMIDs         | [DictionaryForMIDs](./p/dicformids.md)            | No                       |
| `random`               | Random                    |                                                   | Yes                      |
