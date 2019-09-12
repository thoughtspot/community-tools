# Load Files

`load_files` is a bash script that automate the process of loading files using ThoughtSpot's bulk loader
`tsload`.   The benefit of using `load_files` is that it's configurable and manages error handling, 
archiving loaded files as well as logging and reporting status.

`load_files` supports loading local files as well as directly loading from an AWS S3 bucket (as-of TS v5.2).

### Loads Data into Default DBNAME & SCHEMANAME
usage:  `load_files` -f <configuration-file>

<configuration-file> is a configuration file (bash) that provides the loading parameters.  The `load.csg` file provides a 
template to start with.

### Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* The table names are the same as the names of the files with some allowed deviations (see below), 
e.g. SalesData.csv goes into a SalesData table.
* The formats for dates, datetimes, boolean, and nulls are the same for all files.
* (optional) Email has been configured on the cluster so that load results can be sent to indicate status of the load.

Note that because you can run the load script with different configurations, it's possible to support multiple 
databases and formats by creating multiple configuration files and running the script with the correct files.

### File names
`load_files` determines which table to update based on the name of the file.  To do so it looks for all
files with the extension specified in the ${DATA_FILE_EXTENSION} variable.  It then truncates anything after
`-`.  If you have table names with additional characters, you can specify `sed` patterns to be removed.  
The `sed patterns allow file names that have additional information, such as the timestamp of the file.

### Directory Structure
The `load_files` script assumes there is a root directory for a database.  The schema for the root folder can be
specified in the configuration file.  It defaults to `falcon_default_schema`. 

You can also have additional schemas under the root folder.  The name of the directory will be used as the schema name
with the convention and formatting for files being the same in all directories.

For example, say you have a database called `MY_COOL_DATABASE` and have two different schemas called `SCHEMA_A` and 
`SCHEMA_B` with tables in each.  You can create a directory for the data with two sub-directories named SCHEMA_A and
SCHEMA_B, then put the data to be loaded into those sub-directories.

### Process

Because `load_files` uses `tsload`, it must be run directly on the TS cluster.  It can load files that are physically
on the cluster, written to a drive that is mounted on the cluster, or written to AWS S3.

`load_files` is typically run one of two ways.  The first approach is to write all of the data to be loaded and
then call `load_files` via SSH.  This approach is preferred.  The second approach is to use a semaphore (trigger) file
that is written after the files have been writing.  Then `load_files` is run via cron or other scheduling tool on 
regular intervals.  If the semaphore file exists then the script will load all of the data.  After 
the files have been loaded the results can be emailed to an admin.

**_WARNING:  Whatever process you implement, you must ensure that files are completely written before `tsload`
runs.  Failure to do so may result in partial data loads or errors._**

### Deploy and configure

`load_files` assumes a particular file structure.  The first time you run it, it will create the sub-directories needed.
The subdirectories are relative to the ROOT_DIR defined in the configuration file.  For example, let's say you have a 
mounted drive `/tsmnt` and want to use that for `load_files`.  You might create a `/bin` directory and put `load_files` 
in that directory.  Then configure to have ROOT_DIR point to `/tsmnt`.  The first time `tsload` is run, it will create 
multiple subdirectories.  This data directory is where tsload expects to find the data file.  Note that you can create these 
directories manually and then they are not created.  

Once `load_files` has been deployed, edit the configuration file to use the variables and flags that are 
for file locations, etc.  Details of the configuration values are in the template `load.cfg`.  You can have multiple
configuration files for different scenarios and databases.  

**_WARNING:_** The configuration flags
are documented and expected to exist, so removing any can cause `load_files` to fail.

You should not need to alter the base `load_files` script.  If you find bugs or have issues, please post on 
https://community.thoughtspot.com

# diff_csv_schema.sh

This script allows you to compare the structure of a csv input file to a target table in ThoughtSpot. It will highlight differences in column names as well as data types which might not match. The script will display a table which gives an easy overview.

The script takes three parameters:
--input   The input file which should be checked
--table   The table name, including database name and schema name, to check
--lines   Optional parameter to limit the number of lines of the input file it will parse. Large files will take a long time to parse. If not specified the full file will be parsed.

Usage: bash diff_csv_schema.sh --input <input file> --table <database name>.<schema name>.<table name> --lines <number>

Sample output:
Comparing input file <input file> to tablename <table name>
Parsing just 100 of the input file

Comparison results

===================================|==========|==============================================|==========|==========
<input file>                       |          |table name                                    |          |status
===================================|==========|==============================================|==========|==========
date_time                          |Text      |date_time                                     |date_time |OK
message_type                       |Text      |message_type                                  |varchar   |OK
mobile_number                      |Number    |mobile_number                                 |varchar   |REVIEW
network                            |Text      |network                                       |varchar   |OK
message_header                     |Number    |message_header                                |varchar   |REVIEW
price_pence                        |Number    |price_pence                                   |double    |OK
<missing>                          |          |campaign                                      |varchar   |ISSUE
<missing>                          |          |status                                        |varchar   |ISSUE
<missing>                          |          |message_body                                  |varchar   |ISSUE
===================================|==========|==============================================|==========|==========

In this example you quickly see that there are 3 columns missing in the source file and that two columns might need to be reviewed to see if the data types are as intended.
