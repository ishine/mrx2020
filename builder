#!/bin/bash

# example
# ./builder test/file_list_for_db_small.txt ./test/dir_for_db

# to run elasticsearch only:
#FOOTPRINT_DB_FOLDER=/var/fasttmp/tofani/mirex/db docker-compose up elasticsearch

file_list_for_db=$1
path_for_db=$2

export FOOTPRINT_DB_FOLDER=$path_for_db/es_data
docker-compose run --rm elasticsearch mkdir -p /usr/share/elasticsearch/data
docker-compose run --rm elasticsearch chmod -R 777 /usr/share/elasticsearch/data
docker-compose down
docker-compose up -d elasticsearch

rm -rf ./tmp
mkdir -p ./tmp/audios
touch ./tmp/files_map.csv
echo "key,file" >> ./tmp/files_map.csv

n=1
while read line; do
  $(find ffmpeg-git* -type d | head -n 1)/ffmpeg -nostdin -i $line -acodec pcm_s16le -ac 1 -ar 44100 ./tmp/audios/$n.wav
  n=$((n+1))
  echo "$line,/cache/audios/$n.wav" >> ./tmp/files_map.csv
done < $file_list_for_db

docker-compose run --rm mirex ln -s /footprint/footprint-repo/footprint /home/footprint
docker-compose run --rm mirex python3 build.py


#./builder2 /var/fasttmp/tofani/mirex/datasets/db.txt /var/fasttmp/tofani/mirex/db
