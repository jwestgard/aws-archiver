#!/bin/bash

MYDIR="$(dirname "$(realpath "$0")")"
echo "Enter the name of the file you want to read from"
read ndir
#INPUT=$MYDIR/aws_retrieval_request.csv
INPUT=$MYDIR/$ndir
OLDIFS=$IFS
IFS=','
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read bucketname filelocation fileserverlocation
do
        aws s3api restore-object --restore-request Days=7,GlacierJobParameters={Tier=Bulk} --bucket "$bucketname" --key "$filelocation"
        echo "Done Requesting for Restore "$filelocation""
done < $INPUT
IFS=$OLDIFS
