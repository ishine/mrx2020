./submission.sh test/file_list_for_db_small.txt test/file_list_for_query_small.txt ./tmp ./results.txt
./builder test/file_list_for_db_small.txt ./test/dir_for_db
./matcher test/file_list_for_query_small.txt ./test/dir_for_db ./test/result.txt
