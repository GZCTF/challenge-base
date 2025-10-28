#!/bin/sh
if [ -n "$GZCTF_FLAG" ]; then
    echo "$GZCTF_FLAG"
else
    echo "flag{default_flag}"
fi
