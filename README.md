# MIREX 2020 - Audio Fingerprinting / Cover Song Identification

### Requirements

It's required to have installed both docker and docker-compose. Further dependencies will be loaded as the docker container is built.

### Setup

#### Clone the repo:
`git clone https://github.com/arthurtofani/mrx2020.git`


#### Build docker image
`cd mrx2020`
run `docker-compose build`

(It may take a while)



### Running

#### Build

`./builder test/file_list_for_db_small.txt ./test/dir_for_db`


#### Match

 `./matcher test/file_list_for_query_small.txt ./test/dir_for_db ./test/result.txt`


(please change files and folders to your locations)
