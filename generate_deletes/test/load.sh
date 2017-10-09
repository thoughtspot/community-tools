#!/bin/sh
cat table_1.csv | tsload --empty_target --target_database delete_from --target_table table_1 --source_data_format csv --date_format "%m/%d/%y" --date_time_format "%m/%d/%y %H:%M:%S"
cat table_2.csv | tsload --empty_target --target_database delete_from --target_table table_2 --source_data_format csv --date_format "%m/%d/%y" --date_time_format "%m/%d/%y %H:%M:%S"
