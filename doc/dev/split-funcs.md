# Functions to split

Generated on 2026-11-16 from commit `3157c4fe`, using Python AST metrics and
coverage collected from the main test suite plus the UI test suite
(`tests/*_test.py` and `pyglossary/ui/tests/*_test.py`).

## Combined rankings

Merged from the cyclomatic complexity and statement count rankings, sorted by
`CC * 2 + Stmt` (descending).

| CC | Stmt | LOC | Coverage | Function |
| ---: | ---: | ---: | ---: | --- |
| 15 | 33 | 55 | 79.4% | `pyglossary/plugin_handler.py:276` (`detectOutputFormat`) |
| 12 | 36 | 65 | 73.0% | `pyglossary/plugins/aard2_slob/writer.py:187` (`addEntry`) |
| 14 | 31 | 39 | 56.2% | `pyglossary/plugins/yomichan/reader.py:345` (`_readSubStructuredContent`) |
| 12 | 32 | 54 | 2.9% | `pyglossary/plugins/tmx_plugin/reader.py:94` (`__iter__`) |
| 11 | 34 | 60 | 83.3% | `pyglossary/glossary_v2.py:968` (`_write`) |
| 10 | 36 | 61 | 63.2% | `pyglossary/ebook_base.py:461` (`write`) |
| 10 | 35 | 58 | 0.0% | `pyglossary/exp/edlin/reader.py:92` (`__iter__`) |
| 10 | 35 | 45 | 100.0% | `pyglossary/plugins/epwing/converter.py:390` (`extract_terms`) |
| 13 | 28 | 40 | 93.1% | `pyglossary/plugins/quickdic6/reader.py:118` (`_extract_rows_from_indexentry`) |
| 12 | 30 | 41 | 75.8% | `pyglossary/plugins/aard2_slob/reader.py:64` (`open`) |
| 12 | 30 | 32 | 83.9% | `pyglossary/plugins/dsl/lex.py:130` (`lexTagAttrValue`) |
| 9 | 36 | 47 | 75.7% | `pyglossary/plugins/stardict/reader.py:413` (`readSynFile`) |
| 13 | 27 | 41 | 3.4% | `pyglossary/logger.py:201` (`emit`) |
| 8 | 36 | 77 | 91.9% | `pyglossary/plugins/aard2_slob/_writer.py:67` (`__init__`) |
| 7 | 38 | 49 | 97.4% | `pyglossary/plugin_prop.py:170` (`fromModule`) |
| 8 | 35 | 80 | 87.8% | `pyglossary/plugins/dicformids/writer.py:126` (`write`) |
| 7 | 37 | 59 | 100.0% | `pyglossary/plugins/pocketbook_sdic/writer.py:128` (`_pack_blocks`) |
| 7 | 37 | 59 | 71.1% | `pyglossary/plugins/stardict_merge_syns/writer.py:53` (`_writeMultipartMergeSyns`) |
| 13 | 24 | 25 | 80.0% | `pyglossary/plugins/freedict/parser.py:629` (`_parseSenseChild`) |
| 12 | 26 | 45 | 3.8% | `pyglossary/glossary_progress.py:81` (`_byteProgressIter`) |
| 12 | 25 | 65 | 100.0% | `pyglossary/glossary_v2.py:1095` (`_resolveSortParams`) |
| 12 | 25 | 38 | 96.2% | `pyglossary/plugins/freedict/layout.py:259` (`_sense_sense`) |
| 5 | 36 | 69 | 100.0% | `pyglossary/plugins/appledict/writer.py:322` (`write`) |

## User interface

UI functions from both rankings, merged and sorted by `CC * 2 + Stmt`
(descending).

| CC | Stmt | LOC | Coverage | Function |
| ---: | ---: | ---: | ---: | --- |
| 7 | 155 | 271 | 0.0% | `pyglossary/ui/ui_gtk3.py:1309` (`__init__`) |
| 7 | 99 | 340 | 0.0% | `pyglossary/ui/ui_tk/ui.py:105` (`__init__`) |
| 25 | 59 | 87 | 16.9% | `pyglossary/ui/ui_cmd_interactive/ui.py:717` (`printNonInteractiveCommand`) |
| 3 | 94 | 161 | 0.0% | `pyglossary/ui/ui_gtk4/mainwin.py:195` (`__init__`) |
| 19 | 59 | 132 | 0.0% | `pyglossary/ui/main.py:153` (`mainPrepare`) |
| 20 | 47 | 69 | 0.0% | `pyglossary/ui/ui_qt6/ui.py:807` (`run`) |
| 19 | 44 | 65 | 0.0% | `pyglossary/ui/ui_wx/ui.py:685` (`run`) |
| 10 | 59 | 76 | 0.0% | `pyglossary/ui/ui_qt6/ui.py:191` (`__init__`) |
| 17 | 41 | 100 | 0.0% | `pyglossary/ui/ui_tk_wizard.py:269` (`run`) |
| 7 | 61 | 103 | 0.0% | `pyglossary/ui/ui_tk_wizard.py:92` (`__init__`) |
| 17 | 40 | 86 | 0.0% | `pyglossary/ui/ui_tk/ui.py:720` (`run`) |
| 15 | 44 | 80 | 2.1% | `pyglossary/ui/ui_cmd_interactive/ui.py:394` (`askWriteOptions`) |
| 15 | 44 | 78 | 2.1% | `pyglossary/ui/ui_cmd_interactive/ui.py:314` (`askReadOptions`) |
| 15 | 43 | 75 | 91.3% | `pyglossary/ui/ui_cmd.py:254` (`run`) |
| 14 | 44 | 52 | 0.0% | `pyglossary/ui/ui_web/websocket_handler.py:380` (`read_next_message`) |
| 13 | 44 | 108 | 0.0% | `pyglossary/ui/ui_web/websocket_main.py:204` (`handle_list_dir_request`) |
| 9 | 51 | 68 | 0.0% | `pyglossary/ui/ui_wx/ui.py:96` (`__init__`) |
| 18 | 31 | 45 | 2.6% | `pyglossary/ui/ui_cmd_interactive/ui.py:810` (`main`) |
| 14 | 38 | 70 | 0.0% | `pyglossary/ui/ui_qt6/ui.py:487` (`_browse_input`) |
| 15 | 33 | 56 | 0.0% | `pyglossary/ui/runner.py:166` (`getRunner`) |
| 13 | 37 | 47 | 2.4% | `pyglossary/ui/terminal_theme.py:118` (`_query_osc11_rgb`) |
| 7 | 48 | 61 | 0.0% | `pyglossary/ui/ui_slint/ui.py:67` (`__init__`) |
| 16 | 29 | 49 | 0.0% | `pyglossary/ui/ui_slint/ui.py:432` (`run`) |
| 15 | 31 | 42 | 0.0% | `pyglossary/ui/tools/diff_glossary.py:296` (`run`) |
| 12 | 36 | 43 | 0.0% | `pyglossary/ui/ui_web/websocket_handler.py:320` (`_handle_one_request`) |
| 14 | 30 | 53 | 0.0% | `pyglossary/ui/ui_web/ui_controller.py:110` (`start_convert_job`) |
| 15 | 25 | 45 | 0.0% | `pyglossary/ui/ui_gtk4/mainwin.py:455` (`run`) |
| 14 | 27 | 48 | 0.0% | `pyglossary/ui/ui_gtk3.py:1593` (`run`) |
| 12 | 31 | 37 | 0.0% | `pyglossary/ui/ui_qt6/ui.py:147` (`eventFilter`) |
| 13 | 28 | 45 | 3.6% | `pyglossary/ui/ui_cmd_interactive/interactive_prompt.py:161` (`fs_ls`) |
| 12 | 30 | 74 | 0.0% | `pyglossary/ui/tools/view_glossary.py:107` (`viewGlossary`) |
| 4 | 46 | 329 | 100.0% | `pyglossary/ui/argparse_main.py:26` (`defineFlags`) |
| 4 | 42 | 53 | 0.0% | `pyglossary/ui/ui_wx/format_widgets.py:336` (`__init__`) |
| 3 | 44 | 104 | 0.0% | `pyglossary/ui/ui_tk/format_widgets.py:58` (`__init__`) |
| 12 | 23 | 38 | 0.0% | `pyglossary/ui/ui_wx/ui.py:390` (`_browse_input`) |
| 2 | 42 | 58 | 0.0% | `pyglossary/ui/ui_qt6/general_options.py:45` (`__init__`) |
| 2 | 41 | 61 | 0.0% | `pyglossary/ui/ui_wx/general_options.py:35` (`__init__`) |
| 2 | 38 | 49 | 0.0% | `pyglossary/ui/ui_gtk4/sort_options.py:52` (`__init__`) |

## Method

- **CC** (cyclomatic complexity): 1 + decision points (`if`/`elif`, conditional
  expressions, `for`, `while`, `except`, `assert`, boolean operands,
  comprehensions, `match` cases). Nested functions and classes are measured
  separately and not counted toward the enclosing function.
- **LOC**: inclusive physical line span of the function definition.
- **Statements**: number of AST statement nodes in the function body,
  excluding bodies of nested functions/classes.
- **Coverage**: executed executable statement lines divided by total
  executable statement lines in the function. `n/a` means the module was not
  imported by the test runs; `0.0%` means the module was imported but none of
  the function's statements ran.
- Excluded: vendored `pyglossary/plugin_lib/`, test modules and
  `pyglossary/ui/tests/`.
- Candidate targets are ranked by `CC * 2 + Stmt`.
- UI functions are collected in their own table, merging the top entries from
  both rankings.
