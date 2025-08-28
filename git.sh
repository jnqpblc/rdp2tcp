#!/bin/bash
if [ -z "$1" ]; then printf "\n./git.sh <commint_msg>\n\n"
  else
MSG="$1"
git add .
git commit -m "$MSG"
git push
fi
