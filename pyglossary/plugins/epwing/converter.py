# Convert EPWING dictionaries to Yomichan format.
# Based on yomichan-import (https://github.com/FooSoft/yomichan-import) under the MIT License

import re
import os
import json
import zipfile
import logging
from typing import List, Dict, Any, Optional, Iterator

log = logging.getLogger("pyglossary")

class dbTerm:
    def __init__(
        self,
        expression: str,
        reading: str = "",
        definition_tags: List[str] = None,
        rules: List[str] = None,
        score: int = 0,
        glossary: List[Any] = None,
        sequence: int = 0,
        term_tags: List[str] = None
    ):
        self.expression = expression
        self.reading = reading
        self.definition_tags = definition_tags or []
        self.rules = rules or []
        self.score = score
        self.glossary = glossary or []
        self.sequence = sequence
        self.term_tags = term_tags or []

    def add_definition_tags(self, *tags: str):
        for tag in tags:
            if tag not in self.definition_tags:
                self.definition_tags.append(tag)

    def add_term_tags(self, *tags: str):
        for tag in tags:
            if tag not in self.term_tags:
                self.term_tags.append(tag)

    def add_rules(self, *rules: str):
        for rule in rules:
            if rule not in self.rules:
                self.rules.append(rule)

    def crush(self) -> List[Any]:
        return [
            self.expression,
            self.reading,
            " ".join(self.definition_tags),
            " ".join(self.rules),
            self.score,
            self.glossary,
            self.sequence,
            " ".join(self.term_tags)
        ]

class dbKanji:
    def __init__(
        self,
        character: str,
        onyomi: List[str] = None,
        kunyomi: List[str] = None,
        tags: List[str] = None,
        meanings: List[str] = None,
        stats: Dict[str, str] = None
    ):
        self.character = character
        self.onyomi = onyomi or []
        self.kunyomi = kunyomi or []
        self.tags = tags or []
        self.meanings = meanings or []
        self.stats = stats or {}

    def crush(self) -> List[Any]:
        return [
            self.character,
            " ".join(self.onyomi),
            " ".join(self.kunyomi),
            " ".join(self.tags),
            self.meanings,
            self.stats
        ]

class EpwingExtractor:
    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        raise NotImplementedError

    def extract_kanji(self, heading: str, text: str) -> List[dbKanji]:
        heading = self.translate(heading)
        text = self.translate(text)
        return []

    def get_font_narrow(self) -> Dict[int, str]:
        return {}

    def get_font_wide(self) -> Dict[int, str]:
        return {}

    def get_revision(self) -> str:
        return "epwing"

    def translate(self, text: str) -> str:
        font_narrow = self.get_font_narrow()
        font_wide = self.get_font_wide()
        
        def repl(match):
            mode = match.group(1)
            code = int(match.group(2))
            font = font_narrow if mode == 'n' else font_wide
            return font.get(code, "")
        
        text = re.sub(r'{{([nw])_(\d+)}}', repl, text)
        text = re.sub(r'\n+', '\n', text)
        return text

class KoujienExtractor(EpwingExtractor):
    def __init__(self):
        self.parts_exp = re.compile(r'([^（【〖]+)(?:【(.*)】)?(?:〖(.*)〗)?(?:（(.*)）)?')
        self.read_group_exp = re.compile(r'[-‐・]+')
        self.exp_var_exp = re.compile(r'\(([^\)]*)\)')
        self.meta_exp = re.compile(r'（([^）]*)）')
        self.v5_exp = re.compile(r'(動.[四五](［[^］]+］)?)|(動..二)')
        self.v1_exp = re.compile(r'(動..一)')

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        
        match = self.parts_exp.match(heading)
        if not match:
            return []

        expressions = []
        readings = []

        expression = match.group(2)
        if expression:
            expression = self.meta_exp.sub('', expression)
            for split in expression.split('・'):
                split_inc = self.exp_var_exp.sub(r'\1', split)
                expressions.append(split_inc)
                if split != split_inc:
                    split_exc = self.exp_var_exp.sub('', split)
                    expressions.append(split_exc)

        reading = match.group(1)
        if reading:
            reading = self.read_group_exp.sub('', reading)
            readings.append(reading)

        tags = []
        for line in text.split('\n'):
            m = self.meta_exp.search(line)
            if m:
                for tag in m.group(1).split('・'):
                    tags.append(tag)

        terms = []
        if not expressions:
            for r in readings:
                term = dbTerm(expression=r, glossary=[text], sequence=sequence)
                self.export_rules(term, tags)
                terms.append(term)
        else:
            for e in expressions:
                for r in readings:
                    term = dbTerm(expression=e, reading=r, glossary=[text], sequence=sequence)
                    self.export_rules(term, tags)
                    terms.append(term)
        return terms

    def export_rules(self, term: dbTerm, tags: List[str]):
        for tag in tags:
            if tag == "形":
                term.add_rules("adj-i")
            elif tag == "動サ変" and (term.expression.endswith("する") or term.expression.endswith("為る")):
                term.add_rules("vs")
            elif term.expression == "来る":
                term.add_rules("vk")
            elif self.v5_exp.search(tag):
                term.add_rules("v5")
            elif self.v1_exp.search(tag):
                term.add_rules("v1")

    def get_revision(self) -> str:
        return "koujien"

    def get_font_wide(self) -> Dict[int, str]:
        return {
            41531: "⟨", 41532: "⟩", 42017: "⇿", 42018: "🈑", 42023: "🈩",
            42024: "🈔", 42025: "㊇", 42026: "3", 42027: "❷", 42028: "❶",
            42031: "❸", 42037: "❹", 42043: "❺", 42045: "❻", 42057: "❼",
            42083: "❽", 42284: "❾", 42544: "❿", 42561: "鉏", 43611: "⓫",
            43612: "⓬", 44142: "𑖀", 44856: "㉑", 44857: "㉒", 46374: "〔",
            46375: "〕", 46390: "①", 46391: "②", 46392: "③", 46393: "④",
            46394: "⑤", 46395: "⑥", 46396: "⑦", 46397: "⑧", 46398: "⑨",
            46399: "⑩", 46400: "⑪", 46401: "⑫", 46402: "⑬", 46403: "⑭",
            46404: "⑮", 46405: "⑯", 46406: "⑰", 46407: "⑱", 46408: "⑲",
            46409: "⑳", 46677: "⇀", 46420: "⇨", 47175: "(季)", 56383: "㋐",
            56384: "㋑", 56385: "㋒", 56386: "㋓", 56387: "㋔", 56388: "㋕",
            56389: "㋖", 56390: "㋗", 56391: "㋘", 56392: "㋙", 56393: "㋚",
            56394: "㋛", 56395: "㋜", 56396: "㋝", 56397: "㋞", 56398: "▷",
        }

class DaijirinExtractor(KoujienExtractor):
    def get_revision(self) -> str:
        return "daijirin2"

    def get_font_narrow(self) -> Dict[int, str]:
        # Considerably expanded Gaiji mapping for Daijirin (Ported from Go base)
        return {
            49441: "á", 49442: "à", 49443: "â", 49444: "ä", 49445: "ã", 49446: "ā",
            49447: "é", 49448: "è", 49449: "ê", 49450: "ë", 49451: "ē",
            49452: "í", 49453: "î", 49454: "ï", 49455: "ñ",
            49456: "ó", 49457: "ò", 49458: "ô", 49459: "ö", 49460: "ř",
            49461: "ú", 49462: "ü", 49463: "~", 49464: "ç", 49465: "ˇ",
            49466: "ɡ", 49467: "ŋ", 49468: "ʒ", 49469: "ʃ", 49470: "ɔ", 49471: "ð",
            49472: "Á", 49473: "Í", 49474: "Ú", 49475: "É", 49476: "Ó",
            49477: "À", 49478: "È", 49479: "Ò", 49480: "ì", 49481: "ù",
            49482: "ý", 49484: "ɑ", 49485: "ə", 49487: "ɛ", 49488: "θ",
            49489: "ʌ", 49490: "ɒ", 49500: "æ", 50037: "ヰ", 50038: "ヱ",
        }

class DaijisenExtractor(KoujienExtractor):
    def __init__(self):
        super().__init__()
        # Specialized regex for Daijisen matching daijisen.go
        self.parts_exp = re.compile(r'([^【]+)(?:【(.*)】)?')
        self.exp_shapes_exp = re.compile(r'[×△＝‐]+')
        self.exp_multi_exp = re.compile(r'】[^【】]*【')
        self.exp_var_exp = re.compile(r'（([^）]*)）')
        self.read_group_exp = re.compile(r'[-‐・]+')
        self.meta_exp = re.compile(r'［([^］]*)］')

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        
        match = self.parts_exp.match(heading)
        if not match:
            return []

        expressions = []
        expression_raw = match.group(2)
        if expression_raw:
            # Replaced multi-bracket links with separator
            expression = self.exp_multi_exp.sub('・', expression_raw)
            # Remove shapes and special hyphens
            expression = self.exp_shapes_exp.sub('', expression)
            
            for split in expression.split('・'):
                split_inc = self.exp_var_exp.sub(r'\1', split)
                expressions.append(split_inc)
                if split != split_inc:
                    split_exc = self.exp_var_exp.sub('', split)
                    expressions.append(split_exc)

        reading = match.group(1)
        if reading:
            reading = self.read_group_exp.sub('', reading)
            reading = self.exp_var_exp.sub('', reading)

        tags = []
        for line in text.split('\n'):
            m = self.meta_exp.search(line)
            if m:
                for tag in m.group(1).split('・'):
                    tags.append(tag)

        terms = []
        if not expressions:
            term = dbTerm(expression=reading, glossary=[text], sequence=sequence)
            self.export_rules(term, tags)
            terms.append(term)
        else:
            for e in expressions:
                term = dbTerm(expression=e, reading=reading, glossary=[text], sequence=sequence)
                self.export_rules(term, tags)
                terms.append(term)
        return terms

    def get_revision(self) -> str:
        return "daijisen2"

# Simplified EPWING Reader in Pure Python
# This handles the basic uncompressed HONMON reading.
class EpwingBook:
    def __init__(self, path: str):
        self.path = path
        self.subbooks = []
        self._load()

    def _load(self):
        # Read CATALOGS
        catalogs_path = os.path.join(self.path, "CATALOGS")
        if not os.path.exists(catalogs_path):
            catalogs_path = os.path.join(self.path, "catalogs")
        
        if not os.path.exists(catalogs_path):
             raise FileNotFoundError(f"CATALOGS not found in {self.path}")

        with open(catalogs_path, "rb") as f:
            data = f.read()
            # Find subdirectories that exist in the book path
            # EPWING 4 and 6 have different CATALOGS layouts.
            # A simple approach: find any 8-char or shorter strings that match directory names.
            possible_dirs = [d for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, d))]
            for d in possible_dirs:
                if d in ("DATA", "GAIJI", "MOVIE", "STREAM"): continue # Skip common ones
                if d.encode("ascii") in data:
                    subbook_path = os.path.join(self.path, d)
                    # Try to find title near the directory name in CATALOGS?
                    # Or just use the directory name as title for mapping.
                    self.subbooks.append(EpwingSubbook(subbook_path, d.upper()))

class EpwingSubbook:
    def __init__(self, path: str, title: str):
        self.path = path
        self.title = title
    
    def entries(self) -> Iterator[Dict[str, str]]:
        honmon_path = os.path.join(self.path, "DATA", "HONMON")
        if not os.path.exists(honmon_path):
            return

        with open(honmon_path, "rb") as f:
            # We will read in 2KB blocks (standard EPWING page size) or just the whole file if small.
            # For 500MB, reading the whole file into RAM is fine on modern machines (like users).
            data = f.read()
            
            # Simple scanner for heading and text
            pos = 0
            while True:
                # 1F 09: Entry start (heading)
                start = data.find(b"\x1f\x09", pos)
                if start == -1:
                    break
                
                # 1F 0A: Text start
                text_start = data.find(b"\x1f\x0a", start)
                if text_start == -1:
                    pos = start + 2
                    continue
                
                # Find the end of this entry.
                # Usually it's either the next 1F 09 or end of 2KB block?
                # For simplified scanner, find the next 1F 09.
                next_entry = data.find(b"\x1f\x09", text_start)
                if next_entry == -1:
                    end = len(data)
                else:
                    end = next_entry
                
                heading_raw = data[start+2:text_start]
                text_raw = data[text_start+2:end]
                
                def clean(raw):
                    processed = bytearray()
                    i = 0
                    while i < len(raw):
                        if raw[i] == 0x1f:
                             # Font markers
                             if i+3 < len(raw) and raw[i+1] in (0x61, 0x62): # 1F 61 (narrow), 1F 62 (wide)
                                 code = int.from_bytes(raw[i+2:i+4], "big")
                                 marker = f"{{{{{'n' if raw[i+1]==0x61 else 'w'}_{code}}}}}"
                                 processed.extend(marker.encode("ascii"))
                                 i += 4
                             else:
                                 i += 1
                        elif raw[i] == 0x1e:
                             # 1E 00/01: font switch?
                             i += 2
                        elif raw[i] < 0x20:
                             # Skip other control codes
                             i += 1
                        else:
                             processed.append(raw[i])
                             i += 1
                    
                    for enc in ("euc-jp", "cp932", "shift-jis", "utf-8"):
                        try:
                            # Use errors="replace" for the last fallback or just ignore
                            return processed.decode(enc)
                        except:
                            continue
                    return processed.decode("ascii", errors="ignore")
                
                yield {
                    "heading": clean(heading_raw),
                    "text": clean(text_raw)
                }
                
                pos = end

class MeikyouExtractor(KoujienExtractor):
    def __init__(self):
        super().__init__()
        self.parts_exp = re.compile(r'([^（【〖\[]+)(?:【(.*)】)?(?:\[(.*)\])?(?:（(.*)）)?')
        self.exp_shapes_exp = re.compile(r'[▼▽]+')
        self.exp_bracketed_exp = re.compile(r'(?:[〈《])([^〉》]*)(?:[〉》])')
        self.exp_terms_exp = re.compile(r'([^（]*)?(?:（(.*)）)?')
        self.read_group_exp = re.compile(r'[-‐・]+')
        self.meta_exp = re.compile(r'〘([^〙]*)〙')

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        
        match = self.parts_exp.match(heading)
        if not match:
            return []

        expressions = []
        readings = []

        # Expression from 【...】
        exp_match = match.group(2)
        if exp_match:
            exp_match = self.exp_shapes_exp.sub('', exp_match)
            exp_match = self.exp_bracketed_exp.sub(r'\1', exp_match)
            terms_match = self.exp_terms_exp.match(exp_match)
            if terms_match:
                for group in terms_match.groups():
                    if group:
                        for split in group.split('・'):
                            expressions.append(split)

        # Expression from [...] (foreign/meta)
        foreign_match = match.group(3)
        if foreign_match:
            # Simplified foreign meta removal (Go version has a long list, we just split)
            foreign_match = foreign_match.replace("＋", " ")
            for split in foreign_match.split('・'):
                expressions.append(split)

        reading = match.group(1)
        if reading:
            reading = self.read_group_exp.sub('', reading)
            readings.append(reading)

        tags = []
        for line in text.split('\n'):
            m = self.meta_exp.search(line)
            if m:
                for tag in m.group(1).split('・'):
                    tags.append(tag)

        terms = []
        if not expressions:
            for r in readings:
                term = dbTerm(expression=r, glossary=[text], sequence=sequence)
                self.export_rules(term, tags)
                terms.append(term)
        else:
            for e in expressions:
                for r in readings:
                    term = dbTerm(expression=e, reading=r, glossary=[text], sequence=sequence)
                    self.export_rules(term, tags)
                    terms.append(term)
        return terms

    def get_revision(self) -> str:
        return "meikyou1"

    def get_font_narrow(self) -> Dict[int, str]:
        # Basic mapping for Meikyou
        return {41550: "ī"}

class GakkenExtractor(KoujienExtractor):
    def __init__(self):
        super().__init__()
        self.parts_exp = re.compile(r'([ぁ-んァ-ヶー‐・]*)(?:【(.*)】)?')
        self.read_group_exp = re.compile(r'[-‐・]+')
        # Ported from gakken.go cosmetics replacer
        self.cosmetics = {
            "(1)": "①", "(2)": "②", "(3)": "③", "(4)": "④", "(5)": "⑤",
            "カ゛": "ガ", "キ゛": "ギ", "ク゛": "グ", "ケ゛": "ゲ", "コ゛": "ゴ",
            "タ゛": "ダ", "チ゛": "ヂ", "ツ゛": "ヅ", "テ゛": "デ", "ト゛": "ド",
            "ハ゛": "バ", "ヒ゛": "ビ", "フ゛": "ブ", "ヘ゛": "ベ", "ホ゛": "ボ",
            "サ゛": "ザ", "シ゛": "ジ", "ス゛": "ズ", "セ゛": "ゼ", "ソ゛": "ゾ"
        }

    def _apply_cosmetics(self, text: str) -> str:
        for k, v in self.cosmetics.items():
            text = text.replace(k, v)
        return text

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        text = self._apply_cosmetics(text)
        
        match = self.parts_exp.match(heading)
        if not match:
            return []

        expressions = []
        readings = []

        expression_raw = match.group(2)
        if expression_raw:
            expression = self.meta_exp.sub('', expression_raw)
            for split in re.split(r'・|】【', expression):
                split_inc = self.exp_var_exp.sub(r'\1', split)
                expressions.append(split_inc)
                if split != split_inc:
                    split_exc = self.exp_var_exp.sub('', split)
                    expressions.append(split_exc)

        reading = match.group(1)
        if reading:
            reading = self.read_group_exp.sub('', reading)
            readings.append(reading)

        tags = []
        for line in text.split('\n'):
            m = self.meta_exp.search(line)
            if m:
                for tag in m.group(1).split('・'):
                    tags.append(tag)

        if not readings:
            readings = [""]

        terms = []
        if not expressions:
            for r in readings:
                if not r: continue
                term = dbTerm(expression=r, glossary=[text], sequence=sequence)
                self.export_rules(term, tags)
                terms.append(term)
        else:
            for e in expressions:
                for r in readings:
                    term = dbTerm(expression=e, reading=r, glossary=[text], sequence=sequence)
                    self.export_rules(term, tags)
                    terms.append(term)
        return terms

    def get_revision(self) -> str:
        return "gakken"

class WadaiExtractor(KoujienExtractor):
    def __init__(self):
        super().__init__()
        self.parts_exp = re.compile(r'([^＜]+)(?:＜([^＞【]+)(?:【([^】]+)】)?＞)?')
        self.literal_parts_exp = re.compile(r'(¶)?(.*)')
        self.read_parts_exp = re.compile(r'([^１２３４５６７８９０]+)(.*)')
        self.quoted_exp = re.compile(r'「?([^」]+)')
        self.alpha_exp = re.compile(r'[a-z]+')

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        
        match = self.parts_exp.match(heading)
        if not match:
            return []

        preset = False
        literal = match.group(1)
        lit_match = self.literal_parts_exp.match(literal)
        if lit_match:
            preset = bool(lit_match.group(1))
            literal = lit_match.group(2)

        reading = match.group(2) or ""
        read_match = self.read_parts_exp.match(reading)
        if read_match:
            reading = read_match.group(1)

        expressions = (match.group(3) or "").split('・')
        if not expressions or expressions == [""]:
            expressions = [""]

        terms = []
        for expression in expressions:
            if preset:
                expression = literal
                reading = ""
            elif not expression:
                expression = literal

            quoted_match = self.quoted_exp.match(reading)
            if quoted_match:
                reading = quoted_match.group(1)

            if self.alpha_exp.match(expression) and reading:
                expression = reading
                reading = ""

            expression = expression.strip()
            if not expression:
                continue

            term = dbTerm(expression=expression, reading=reading, glossary=[text], sequence=sequence)
            terms.append(term)
        return terms

    def get_revision(self) -> str:
        return "wadai1"

class KotowazaExtractor(EpwingExtractor):
    def __init__(self):
        self.read_group_exp = re.compile(r'([^ぁ-ゖァ-ヺ]*)(\([^)]*\))')
        self.read_group_alts_exp = re.compile(r'\(([^)]*)\)')
        self.read_group_no_alts_exp = re.compile(r'\(([^・)]*)\)')
        self.word_group_exp = re.compile(r'＝([^〔＝]*)〔＝([^〕]*)〕')

    def extract_terms(self, heading: str, text: str, sequence: int) -> List[dbTerm]:
        heading = self.translate(heading)
        text = self.translate(text)
        
        queue = [heading]
        reduced_expressions = []

        while queue:
            expression = queue.pop(0)
            match = self.word_group_exp.search(expression)
            if not match:
                reduced_expressions.append(expression)
            else:
                replacements = [match.group(1)]
                replacements.extend(match.group(2).split('・'))
                for repl in replacements:
                    queue.append(expression.replace(match.group(0), repl))

        terms = []
        for red_exp in reduced_expressions:
            expression = self.read_group_exp.sub(r'\1', red_exp)
            read_alts_exp = self.read_group_exp.sub(r'\2', red_exp)
            read_alts_exp = self.read_group_no_alts_exp.sub(r'\1', read_alts_exp)

            readings = []
            read_queue = [read_alts_exp]
            while read_queue:
                read_item = read_queue.pop(0)
                match = self.read_group_alts_exp.search(read_item)
                if not match:
                    readings.append(read_item)
                else:
                    for repl in match.group(1).split('・'):
                        read_queue.append(read_item.replace(match.group(0), repl))

            for r in readings:
                term = dbTerm(expression=expression, reading=r, glossary=[text], sequence=sequence)
                terms.append(term)
        return terms

    def get_revision(self) -> str:
        return "kotowaza1"

def convert_epwing_to_yomichan(input_path: str, output_path: str, title: str = "", stride: int = 10000, pretty: bool = False):
    log.info(f"EPWING (Pure Python): Converting {input_path}...")
    book = EpwingBook(input_path)
    
    # Expanded extractors map matching Go version titles exactly
    extractors_map = {
        "大辞林": DaijirinExtractor(),
        "大辞泉": DaijisenExtractor(),
        "広辞苑": KoujienExtractor(),
        "KOUJIEN": KoujienExtractor(),
        "明鏡国語辞典": MeikyouExtractor(),
        "学研": GakkenExtractor(),
        "古語辞典": GakkenExtractor(),
        "故事ことわざ辞典": GakkenExtractor(),
        "故事ことわざの辞典": KotowazaExtractor(),
        "研究社": WadaiExtractor(),
        "付属資料": KoujienExtractor(),
    }

    all_terms = []
    all_kanji = []
    revisions = []
    titles = []
    sequence = 0
    
    for subbook in book.subbooks:
        extractor = None
        for key, ext in extractors_map.items():
            if key in subbook.title:
                extractor = ext
                break
        
        if not extractor:
             log.warning(f"EPWING: Skipping unknown subbook '{subbook.title}'")
             continue
        
        log.info(f"EPWING: Processing subbook '{subbook.title}'")
        
        for entry in subbook.entries():
            # Translate font markers in entry["heading"] and entry["text"]
            # This is a bit laborious, but we can do it if needed.
            # For now, let's just pass them as is, the extractor handles text.
            
            terms = extractor.extract_terms(entry["heading"], entry["text"], sequence)
            all_terms.extend(terms)
            all_kanji.extend(extractor.extract_kanji(entry["heading"], entry["text"]))
            sequence += 1
        
        revisions.append(extractor.get_revision())
        titles.append(subbook.title)
    
    if not title:
        title = ", ".join(titles)

    log.info(f"EPWING: Writing {len(all_terms)} terms to {output_path}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
        index = {
            "title": title,
            "revision": ";".join(revisions),
            "sequenced": True,
            "format": 3,
            "author": "pyglossary-epwing-pure",
            "url": "https://github.com/FooSoft/yomichan-import"
        }
        z.writestr("index.json", json.dumps(index, indent=4 if pretty else None, ensure_ascii=False))
        
        for i in range(0, len(all_terms), stride):
            batch = all_terms[i:i+stride]
            bank_num = (i // stride) + 1
            content = [t.crush() for t in batch]
            z.writestr(f"term_bank_{bank_num}.json", json.dumps(content, indent=4 if pretty else None, ensure_ascii=False))
        
        for i in range(0, len(all_kanji), stride):
            batch = all_kanji[i:i+stride]
            bank_num = (i // stride) + 1
            content = [k.crush() for k in batch]
            z.writestr(f"kanji_bank_{bank_num}.json", json.dumps(content, indent=4 if pretty else None, ensure_ascii=False))

    log.info("EPWING: Conversion successful.")
