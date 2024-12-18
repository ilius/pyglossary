__all__ = [
	"c_author",
	"c_name",
	"c_publisher",
	"c_sourceLang",
	"c_targetLang",
	"infoKeysAliasDict",
]

c_name = "name"
c_sourceLang = "sourceLang"
c_targetLang = "targetLang"
c_copyright = "copyright"
c_author = "author"
c_publisher = "publisher"

infoKeysAliasDict = {
	"title": c_name,
	"bookname": c_name,
	"dbname": c_name,
	##
	"sourcelang": c_sourceLang,
	"inputlang": c_sourceLang,
	"origlang": c_sourceLang,
	##
	"targetlang": c_targetLang,
	"outputlang": c_targetLang,
	"destlang": c_targetLang,
	##
	"license": c_copyright,
	##
	# do not map "publisher" to "author"
	##
	"date": "creationTime",
	# are there alternatives to "lastUpdated"?
}
