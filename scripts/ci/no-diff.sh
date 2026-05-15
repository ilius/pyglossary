CHANGES=$(GIT_PAGER= git diff --name-only HEAD --)
if [ -n "$CHANGES" ]; then
	echo "There are changes after running gen:"
	echo "$CHANGES"
	GIT_PAGER= git diff
	exit 1
fi
