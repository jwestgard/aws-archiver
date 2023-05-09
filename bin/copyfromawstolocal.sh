#!/bin/bash -x

MYDIR="$(dirname "$(realpath "$0")")"
echo "Enter the name of the file you want to read from"
read ndir
INPUT=$MYDIR/$ndir
IFS=','
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read bucketname filelocation fileserverlocation
do

aws s3 cp "s3://$bucketname/$filelocation" "$fileserverlocation"

done < $INPUT
IFS=$OLDIFS
