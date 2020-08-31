#!/bin/bash

# example
# ./submission.sh test/file_list_for_db_small.txt test/file_list_for_query_small.txt ./tmp ./results.txt

# to run elasticsearch only:
#FOOTPRINT_DB_FOLDER=/var/fasttmp/tofani/mirex/db docker-compose up elasticsearch

working_dir=$3
export WORKING_DIR=$3
export FOOTPRINT_DB_FOLDER=$3/es_data

#mkdir -p $working_dir/cache/*
mkdir -p $working_dir/es_data/*
mkdir -p $working_dir/audios/*
#rm -rf $working_dir/cache/*
#rm -rf $working_dir/es_data/*
#rm -rf $working_dir/audios/*
docker-compose run --rm elasticsearch mkdir -p /usr/share/elasticsearch/data
docker-compose run --rm elasticsearch chmod -R 777 /usr/share/elasticsearch/data
docker-compose run --rm mirex rm -rf /cache/*
docker-compose down
docker-compose up -d elasticsearch


files_map=$working_dir/files_map.csv
queries_map=$working_dir/queries_map.csv
touch $files_map
touch $queries_map
echo "key,file" >> $files_map
echo "key,file" >> $queries_map


ffmpeg_path=(which ffmpeg)
if [ ! -f $ffmpeg_path ]; then
  echo "FFmpeg not found. Installing ffmpeg..."
  rm -rf $(find ffmpeg-git* -type d | head -n 1)
  wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
  tar xvf ffmpeg-git-amd64-static.tar.xz
  rm ffmpeg-git-amd64-static.tar.xz
  ffmpeg_path=$(find ffmpeg-git* -type d | head -n 1)/ffmpeg
else
  echo "ffmpeg found at $ffmpeg_path"
fi

n=1
while read line; do
  cache_db_file=/cache/audios/db_$n.wav
  working_dir_db_file=$working_dir/audios/db_$n.wav
  if [ ! -f $working_dir_db_file ]; then
    $ffmpeg_path -nostdin -i $line -acodec pcm_s16le -ac 1 -ar 44100 $working_dir_db_file
    n=$((n+1))
    echo "$line,$cache_db_file" >> $files_map
  else
    echo "skipping (db): file $n -> $line"
  fi
done < $1

n=1
while read line; do
  cache_query_file=/cache/audios/query_$n.wav
  working_dir_query_file=$working_dir/audios/query_$n.wav

  if [ ! -f $working_dir_query_file ]; then
    $(find ffmpeg-git* -type d | head -n 1)/ffmpeg -nostdin -i $line -acodec pcm_s16le -ac 1 -ar 44100 $working_dir_query_file
    n=$((n+1))
    echo "$line,$cache_query_file" >> $files_map
  else
    echo "skipping (query): file $n -> $line"
  fi
done < $2

docker-compose run --rm mirex ln -s /footprint/footprint-repo/footprint /home/footprint
docker-compose run --rm mirex python3 main.py


cp '$working_dir/results.txt' $4
cat $3
