#!/bin/bash
cd "`dirname \"$0\"`"
for EXP in '*~' '*.pyc' '.hidden' ; do
  find . -name "$EXP" -exec rm '{}' \;
done
cd -
