from pyglossary import Glossary


def takePhonetic_oxford_gb(glos):
	phonGlos = Glossary()  # phonetic glossary
	phonGlos.setInfo("name", glos.getInfo("name") + "_phonetic")
	for entry in glos:
		term = entry.s_word
		defi = entry.defi
		if not defi.startswith("/"):
			continue
		# Now set the phonetic to the `ph` variable.
		ph = ""
		for s in (
			"/ adj",
			"/ v",
			"/ n",
			"/ adv",
			"/adj",
			"/v",
			"/n",
			"/adv",
			"/ n",
			"/ the",
		):
			i = defi.find(s, 2, 85)
			if i == -1:
				continue
			ph = defi[: i + 1]
			break
		ph = (
			ph.replace(";", "\t")
			.replace(",", "\t")
			.replace("     ", "\t")
			.replace("    ", "\t")
			.replace("  ", "\t")
			.replace("//", "/")
			.replace("\t/\t", "\t")
			.replace("<i>US</i>\t", "\tUS: ")
			.replace("<i>US</i>", "\tUS: ")
			.replace("\t\t\t", "\t")
			.replace("\t\t", "\t")
		)
		# 	.replace("/", "")
		# 	.replace("\\n ", "\\n")
		# 	.replace("\\n ", "\\n")
		if ph:
			phonGlos.addEntryObj(phonGlos.newEntry(term, ph))
	return phonGlos
