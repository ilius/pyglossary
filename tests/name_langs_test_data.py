nameLangsTestData = [
	# multi-word lang names that we detect wrong:
	# ("Eurfa Cymraeg, Welsh-English Eurfa/Freedict dictionary", "Welsh", "English"),  # cym-eng
	# ("Norwegian Nynorsk-Norwegian Bokmål FreeDict Dictionary", "Norwegian Nynorsk", "Norwegian"),  # nno-nob
	# cases that detects badly and should skip detecting
	# ("Farajbeik Farsi ( Windows Farsi )", None, None),
	# ("Computer And IT Dictionary for Persian v4.01", None, None),
	# (
	# 	"French (and/or English) to Pârsi (Persian) epistemological Dict. (Latin chars)",
	# 	"French",
	# 	"Persian",
	# ),
	# lang codes that are English words (and not language name)
	("an arabic dictionary", None, None),
	("english cities or towns", None, None),
	("Castellano >Turko Diccionario", None, None),
	("LeXiCoN castelán-galego", None, None),
	("Aragonés-Castellán", None, None),
	("Arab2English", None, None),
	("The Romanization of Korean", None, None),
	("Deutschland auf Google Maps", None, None),
	("Glossary of Latin-Genus-Names", None, None),
	("Dictionario Interlingua - Nederlandese", None, None),
	("Papiamento - Dutch", None, None),
	("Loghatname(Alef)", None, None),
	("Lunfardo (Argentina)", None, None),
	("Medciclopedia", None, None),
	("spanis learner's dictionary", None, None),
	("Dutch - Papiamento", None, None),
	("Dahl's Russian Dictionary", None, None),
	("Great Encyclopedic Glossary", None, None),
	("Efremova (Russian Explanatory Dictionary)", None, None),
	("RUSSIAN LEARNER'S DICTIONARY", None, None),
	("One-Click Engllish-Urdu Dictionary v1.3", None, None),
	("Acronyms from A - Z", None, None),
	("hFarsi - advanced version", None, None),
	("Mathematics Glossary - Mohammad Reza Majidee", None, None),
	("Industrial Engineering Version 2.0", None, None),
	("Geology Science (M.M.Ma'leki)", None, None),
	("Farsi Aviation Dictionary", None, None),
	("Persian Computer Encyclopedia", None, None),
	("Mokhtari Law Dict. (v1.0)", None, None),
	("Hafez Poems", None, None),
	("INGLESPANISH", None, None),
	("Mehran - All about Computer", None, None),
	("Surinaams-Nederlands Trafasi", None, None),
	("Technisch E-NL Woordenboek", None, None),
	("Nederlands - Surinaams Trafasi", None, None),
	("Collins Cobuild 5", None, None),
	("Glossary of Computer and Internet Terms", None, None),
	("Customs and Excise Glossary", None, None),
	("Currency In Each Country", None, None),
	("9300+ Computer Acronyms", None, None),
	("Legal Systems of All Countries", None, None),
	("QURAN", None, None),
	("Britannica Concise Encyclopedia", None, None),
	("Collins English Dictionary", None, None),
	("XML Acronym Demystifier", None, None),
	("Solar Physics Glossary", None, None),
	("English Phonetics", None, None),
	("Flavours of Malaysia/ Malaysian delights", None, None),
	("Wordset.org", None, None),
	("Astronomy and Physics Terms by ExploreSpace.com", None, None),
	("Sorani-Kurmanji Ferheng/FreeDict Dictionary", None, None),  # ckb-kmr
	("Aryanpour (en-fa, fa-en)", "English", "Persian"),
	("Castellano-Catalán", "Spanish", "Catalan"),
	("MB_Dictionary Spanish_to_Persian", "Spanish", "Persian"),
	("Deutsch-English FreeDict+WikDict dictionary (de-en)", "German", "English"),
	("Persisch-Deutsch; Deutsch-Persisch (Alefbâye 2om)", "Persian", "German"),
	("Indonesia-Nederlands", "Indonesian", "Dutch"),
	("Lexin Svensk-Spanskt Lexikon", "Swedish", "Spanish"),
	("Azhdari :: German  To Persian Glossary  1.1", "German", "Persian"),
	("Latvian-Russian Dictionary", "Latvian", "Russian"),
	("AACS Mongolian-English", "Mongolian", "English"),
	("Urdu to English Gloassry", "Urdu", "English"),
	("ADO'S WOORDENBOEK TURKS-NEDERLANDS", "Turkish", "Dutch"),
	("Babylon Turkish-English", "Turkish", "English"),
	("German to Persian", "German", "Persian"),
	("deutsch-spanisch", "German", "Spanish"),
	("Schiffahrtsausdrücke Deutsch - Holländisch", "German", "Dutch"),
	("ADO's Deutsch-Niederländisch", "German", "Dutch"),
	("Elif - German / English Tourist Dic.", "German", "English"),
	("Babylon German-English", "German", "English"),
	("WinCept Glass Dictionary (GER>ENG)", "German", "English"),
	("Babylon German-English", "German", "English"),
	("technical terms German-English", "German", "English"),
	("Runasimi (Quechua) - Español", "Quechua", "Quechua"),
	("Persisch-Deutsch (Alefbā-ye 2om, 2. persisches Alphabet)", "Persian", "German"),
	("Azhdari ::: Persian To German Glossary version 1.1", "Persian", "German"),
	("Farsi to arabic", "Persian", "Arabic"),
	("Persian Italian Glossary", "Persian", "Italian"),
	("Ourstat - Farsi to English Dictionary", "Persian", "English"),
	("HmT - Persian to English Glossary", "Persian", "English"),
	("Arianpour Persian-English (OpenDictionary)", "Persian", "English"),
	("Malay to English", "Malay", "English"),
	("Korean-English Dictionary", "Korean", "English"),
	("Babylon Korean-English", "Korean", "English"),
	("Babylon Chinese(S)-English", "Chinese", "English"),
	("euskera-español", "Basque", "Spanish"),
	("Babylon Japanese-English", "Japanese", "English"),
	("Animal names in Latin and English", "Latin", "English"),
	("Dictionary Portuguese - Dutch", "Portuguese", "Dutch"),
	("Finnish To farsi", "Finnish", "Persian"),
	("Català-Castellà", "Catalan", "Spanish"),
	("Esp-Deu Wörterbuch", "Spanish", "German"),
	("ADO's SPANISCH-DEUTSCH", "Spanish", "German"),
	("Spanish To Farsi", "Spanish", "Persian"),
	("JM Spanish-Danish Dictionary", "Spanish", "Danish"),
	("Spa-Fin", "Spanish", "Finnish"),
	("Spanish-Bulgarian", "Spanish", "Bulgarian"),
	("Babylon Spanish-English", "Spanish", "English"),
	(
		"A Spanish-English Dictionary (Granada University, Spain), 14.4",
		"Spanish",
		"English",
	),
	("Babylon Spanish-English", "Spanish", "English"),
	("Spanish-English Online Dictionaries", "Spanish", "English"),
	("Arabic to Farsi", "Arabic", "Persian"),
	("ADO's FRENCH-GERMAN", "French", "German"),
	("French to Farsi", "French", "Persian"),
	("MB_Dictionary French_to_Persian", "French", "Persian"),
	("French-Chinese GBK", "French", "Chinese"),
	("French-Chinese", "French", "Chinese"),
	("French-Bulgarian", "French", "Bulgarian"),
	("Babylon French-English", "French", "English"),
	("Nederlands-Indonesia", "Dutch", "Indonesian"),
	("Nederlands-Duits", "Dutch", "German"),
	("Nederlands - Kroatisch woordenboek", "Dutch", "Croatian"),
	("Woordenboek Dutch - Portugees", "Dutch", "Portuguese"),
	("Néerlandais-Français", "Dutch", "French"),
	("Bahasa Indonesia-Nederlands Adaptasi", "Indonesian", "Dutch"),
	("Nederlands-Bahasa Indonesia Adaptasi", "Dutch", "Indonesian"),
	("Dutch-English Online Dictionay", "Dutch", "English"),
	("Dutch_English 22000", "Dutch", "English"),
	("Babylon Dutch-English", "Dutch", "English"),
	("Russian-Latvian Dictionary", "Russian", "Latvian"),
	("Russian-Turkish Dictionary", "Russian", "Turkish"),
	("Russisch-Deutsch Woerterbuch", "Russian", "German"),
	("MHM Russian > Persian Dictionary", "Russian", "Persian"),
	("Babylon Russian-English", "Russian", "English"),
	("Italian to farsi", "Italian", "Persian"),
	("Italian Persian glossary", "Italian", "Persian"),
	("Italian>Farsi(Persian) Advanced V 3.0", "Italian", "Persian"),
	("Italian Persian glossary", "Italian", "Persian"),
	("Italiano - Español (GI)", "Italian", "Spanish"),
	("Babylon Italian-English", "Italian", "English"),
	("English To Urdu Lughat", "English", "Urdu"),
	("English-Urdu dictionary", "English", "Urdu"),
	("Babylon English-Turkish", "English", "Turkish"),
	("English-Turkish", "English", "Turkish"),
	("Eng-Tur_Computer/Electronics Terms", "English", "Turkish"),
	("WinCept Glass Dictionary (ENG>GER)", "English", "German"),
	("PONS Universelles Wörterbuch Englisch-Deutsch", "English", "German"),
	("Babylon English-German", "English", "German"),
	("English to Malay", "English", "Malay"),
	("Salaty English-Farsi Dict. (Text ver.)", "English", "Persian"),
	("HmT - English to Persian Glossary", "English", "Persian"),
	("Morteza English > Farsi", "English", "Persian"),
	("Dr.  ALLI  Malay - Farsi Dictionary", "Malay", "Persian"),
	("Arianpour English-Persian (OpenDictionary)", "English", "Persian"),
	("Salaty English-Farsi Dict. (Graphical ver.)", "English", "Persian"),
	("Accounting English-Persian", "English", "Persian"),
	("PAKcw English-Korean Dictionary", "English", "Korean"),
	("Babylon English-Korean", "English", "Korean"),
	("English-Spanish Online Dictionaries", "English", "Spanish"),
	("Babylon English-Spanish", "English", "Spanish"),
	("English_Spanish by Jaime Aguirre", "English", "Spanish"),
	(
		"An English-Spanish Dictionary (Granada University, Spain), 14.4",
		"English",
		"Spanish",
	),
	("Wadan English-Arabic Auditing Terms", "English", "Arabic"),
	("English 2 Arabic Glossary", "English", "Arabic"),
	("English 2 Arabic", "English", "Arabic"),
	("Babylon English-French", "English", "French"),
	("Babylon English-Dutch", "English", "Dutch"),
	("English-Dutch Online Dictionary", "English", "Dutch"),
	("Morteza English > Russian", "English", "Russian"),
	("english-russian", "English", "Russian"),
	("English/Russian - Mueller24", "English", "Russian"),
	("English-Russian Lingvistica'98 dictionary", "English", "Russian"),
	("Babylon English-Russian", "English", "Russian"),
	("Babylon English-English", "English", "English"),
	("Afrikaans-German FreeDict Dictionary", "Afrikaans", "German"),  # afr-deu
	("Afrikaans-English FreeDict Dictionary", "Afrikaans", "English"),  # afr-eng
	("Arabic-English FreeDict Dictionary", "Arabic", "English"),  # ara-eng
	("Breton-French FreeDict Dictionary (Geriadur Tomaz)", "Breton", "French"),  # bre-fra
	("Czech-English FreeDict Dictionary", "Czech", "English"),  # ces-eng
	("Danish-English FreeDict Dictionary", "Danish", "English"),  # dan-eng
	("German-Italian FreeDict Dictionary", "German", "Italian"),  # deu-ita
	("German-Kurdish Ferheng/FreeDict Dictionary", "German", "Kurdish"),  # deu-kur
	("German-Dutch FreeDict Dictionary", "German", "Dutch"),  # deu-nld
	("German-Portuguese FreeDict Dictionary", "German", "Portuguese"),  # deu-por
	("German-Turkish Ferheng/FreeDict Dictionary", "German", "Turkish"),  # deu-tur
	("English-Afrikaans FreeDict Dictionary", "English", "Afrikaans"),  # eng-afr
	("English-Arabic FreeDict Dictionary", "English", "Arabic"),  # eng-ara
	("English-Czech dicts.info/FreeDict Dictionary", "English", "Czech"),  # eng-ces
	(
		"Eurfa Saesneg, English-Welsh Eurfa/Freedict dictionary",
		"English",
		"Welsh",
	),  # eng-cym
	("English-Danish FreeDict Dictionary", "English", "Danish"),  # eng-dan
	("English - Modern Greek XDXF/FreeDict dictionary", "English", "Greek"),  # eng-ell
	("English-French FreeDict Dictionary", "English", "French"),  # eng-fra
	("English-Irish FreeDict Dictionary", "English", "Irish"),  # eng-gle
	("English-Hindi FreeDict Dictionary", "English", "Hindi"),  # eng-hin
	("English-Croatian FreeDict Dictionary", "English", "Croatian"),  # eng-hrv
	("English-Hungarian FreeDict Dictionary", "English", "Hungarian"),  # eng-hun
	("English-Italian FreeDict Dictionary", "English", "Italian"),  # eng-ita
	("English-Latin FreeDict Dictionary", "English", "Latin"),  # eng-lat
	("English-Lithuanian FreeDict Dictionary", "English", "Lithuanian"),  # eng-lit
	("English-Dutch FreeDict Dictionary", "English", "Dutch"),  # eng-nld
	(
		"English - Polish Piotrowski+Saloni/FreeDict dictionary",
		"English",
		"Polish",
	),  # eng-pol
	("English-Portuguese FreeDict Dictionary", "English", "Portuguese"),  # eng-por
	("English-Romanian FreeDict Dictionary", "English", "Romanian"),  # eng-rom
	("English-Serbian FreeDict Dictionary", "English", "Serbian"),  # eng-srp
	("English-Swahili xFried/FreeDict Dictionary", "English", "Swahili"),  # eng-swh
	("English-Turkish FreeDict Dictionary", "English", "Turkish"),  # eng-tur
	("French-Breton FreeDict Dictionary (Geriadur Tomaz)", "French", "Breton"),  # fra-bre
	("French-English FreeDict Dictionary", "French", "English"),  # fra-eng
	("French-Dutch FreeDict Dictionary", "French", "Dutch"),  # fra-nld
	(
		"Scottish Gaelic-German FreeDict Dictionary",
		"Scottish Gaelic",
		"German",
	),  # gla-deu
	("Irish-English FreeDict Dictionary", "Irish", "English"),  # gle-eng
	("Irish-Polish FreeDict Dictionary", "Irish", "Polish"),  # gle-pol
	("Croatian-English FreeDict Dictionary", "Croatian", "English"),  # hrv-eng
	("Hungarian-English FreeDict Dictionary", "Hungarian", "English"),  # hun-eng
	("íslenska - English FreeDict Dictionary", "Icelandic", "English"),  # isl-eng
	("Italian-German FreeDict Dictionary", "Italian", "German"),  # ita-deu
	("Italian-English FreeDict Dictionary", "Italian", "English"),  # ita-eng
	("Japanese-German FreeDict Dictionary", "Japanese", "German"),  # jpn-deu
	("Japanese-English FreeDict Dictionary", "Japanese", "English"),  # jpn-eng
	("Japanese-French FreeDict Dictionary", "Japanese", "French"),  # jpn-fra
	("Japanese-Russian FreeDict Dictionary", "Japanese", "Russian"),  # jpn-rus
	("Khasi - German FreeDict Dictionary", "Khasi", "German"),  # kha-deu
	("Khasi-English FreeDict Dictionary", "Khasi", "English"),  # kha-eng
	("Kurdish-German Ferheng/FreeDict Dictionary", "Kurdish", "German"),  # kur-deu
	("Kurdish-English Ferheng/FreeDict Dictionary", "Kurdish", "English"),  # kur-eng
	("Kurdish-Turkish Ferheng/FreeDict Dictionary", "Kurdish", "Turkish"),  # kur-tur
	("Lateinisch-Deutsch FreeDict-Wörterbuch", "Latin", "German"),  # lat-deu
	("Latin-English FreeDict Dictionary", "Latin", "English"),  # lat-eng
	("Lithuanian-English FreeDict Dictionary", "Lithuanian", "English"),  # lit-eng
	("Macedonian - Bulgarian FreeDict Dictionary", "Macedonian", "Bulgarian"),  # mkd-bul
	("Dutch-German FreeDict Dictionary", "Dutch", "German"),  # nld-deu
	("Dutch-English Freedict Dictionary", "Dutch", "English"),  # nld-eng
	("Nederlands-French FreeDict Dictionary", "Dutch", "French"),  # nld-fra
	("Lenga d'òc - Català FreeDict Dictionary", "", ""),  # oci-cat
	("Polish-Irish FreeDict Dictionary", "Polish", "Irish"),  # pol-gle
	("Portuguese-German FreeDict Dictionary", "Portuguese", "German"),  # por-deu
	("Portuguese-English FreeDict Dictionary", "Portuguese", "English"),  # por-eng
	("Sanskrit-German FreeDict Dictionary", "Sanskrit", "German"),  # san-deu
	("Slovak-English FreeDict Dictionary", "Slovak", "English"),  # slk-eng
	("Slovenian-English FreeDict Dictionary", "Slovene", "English"),  # slv-eng
	("Spanish - Asturian FreeDict Dictionary", "Spanish", "Asturian"),  # spa-ast
	("Spanish-English FreeDict Dictionary", "Spanish", "English"),  # spa-eng
	("Spanish-Portuguese FreeDict Dictionary", "Spanish", "Portuguese"),  # spa-por
	("Serbian - English FreeDict Dictionary", "Serbian", "English"),  # srp-eng
	("Swedish-English FreeDict Dictionary", "Swedish", "English"),  # swe-eng
	("Swahili-English xFried/FreeDict Dictionary", "Swahili", "English"),  # swh-eng
	("Swahili-Polish SSSP/FreeDict Dictionary", "Swahili", "Polish"),  # swh-pol
	("Turkish-German FreeDict Dictionary", "Turkish", "German"),  # tur-deu
	("Turkish-English FreeDict Dictionary", "Turkish", "English"),  # tur-eng
	("Wolof - French FreeDict dictionary", "Wolof", "French"),  # wol-fra
]

# lang codes that are also in /usr/share/dict/words
# {'kea', 'as', 'mao', 'arn', 'pa', 'sag', 'tha', 'be', 'fro', 'my', 'haw', 'so', 'is', 'en', 'ae', 'fa', 'te',
# 'li', 'div', 'tur', 'urd', 'ak', 'arm', 'mi', 'os', 'ar', 'sh', 'run', 'hat', 'pi', 'geo', 'ben', 'bis', 'za',
# 'ave', 'bel', 'got', 'de', 'an', 'bam', 'kor', 'pus', 'cor', 'mac', 'her', 'mal', 'se', 'pan', 'fra', 'ca',
# 'ay', 'alb', 'bo', 'lat', 'spa', 'ka', 'ger', 'san', 'che', 'per', 'may', 'ga', 'bod', 'hi', 'swa', 'mar',
# 'or', 'vie', 'id', 'ton', 'no', 'ell', 'ta', 'cha', 'nep', 'lim', 'ie', 'ewe', 'mon', 'yor', 'mo', 'eu',
# 'hau', 'arc', 'lin', 'es', 'nob', 'ava', 'sin', 'aka', 'ady', 'tib', 'ce', 'ho', 'kan', 'pol', 'wo', 'sot',
# 'ti', 'da', 'yo', 'ne', 'aa', 'st', 'ha', 'el', 'lo', 'cos', 'om', 'non', 'bur', 'wa', 'sa', 'io', 'vol',
# 'am', 'to', 'sun', 'ory', 'hin', 'fi', 'ko', 'kon', 'ice', 'dan', 'kin', 'kat', 'ba', 'tat', 'th', 'ast',
# 'chi', 'nor', 'na', 'ug', 'fin', 'mas', 'ara', 'cat', 'lug', 'he', 'la', 'rum', 'it', 'ur', 'lit', 'tam',
# 'fry', 'si'}
