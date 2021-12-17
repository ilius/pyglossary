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
	# are there alternatives to "creationTime"
	# and "lastUpdated"?
}
