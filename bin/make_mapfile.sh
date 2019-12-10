#!/usr/bin/env bash
ROOTDIR=$1
OUTFILE=$2

echo "Writing MD5 from $ROOTDIR to $OUTFILE ..."

find "$ROOTDIR"  -type f | \
while read filepath;
    do md5sum "$filepath" >> "$OUTFILE"
done