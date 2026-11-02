CHANGES=$(GIT_PAGER= git diff --name-only HEAD --)
if [ -n "$CHANGES" ]; then
	echo "There are changes after running gen:"
	echo "$CHANGES"
	GIT_PAGER= git diff
	exit 1
fi

UNTRACKED=$(GIT_PAGER= git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED" ]; then
	echo "There are untracked files after running gen:"
	echo "$UNTRACKED"
	exit 1
fi
