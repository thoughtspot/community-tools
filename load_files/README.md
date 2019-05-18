# Load Files

load_files consists of bash scripts that automate the process of loading files using ThoughtSpot's bulk loader
`tsload`.   There are currently two versions:
* load_files, which is designed to load multiple files from a directory  
* load_single_file, which is designed to load a single file at a time, with the file name being 
passed in as a parameter.

Each script is described below, but for full details on configuring the script see the comments inside
of each script.

## load_files

Loads one or more files from a given directory or hierarchy of directories using ThoughtSpot's `tsload` and then 
moves to an archive location.

### Loads Data into Default DBNAME & SCHEMANAME
usage:  `load_files` -f <configuration-file>

<configuration-file> is a configuration file (bash) that provides the parameters.  The `load.csf` file provides a 
template to start with.

### Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* The table names are the same as the names of the files with some allowed deviations (see below), 
e.g. SalesData.csv goes into a SalesData table.
* The formats for dates, datetimes, boolean, and nulls are the same for all files.
* (optional) Email has been configured on the cluster so that results can be sent to an admin.

Note that because you can run the load script with different configurations, it's possible to support multiple 
databases and formats by creating multiple configuration files and running the script with the correct files.

### File names
`load_files` determines which table to update based on the name of the file.  To do so it looks for all
files with the extension specified in the DATA_FILE_EXTENSION variable.  It then truncates anything after
`-`.  If you have table names with additional characters, you can specify SED patterns to be removed.  The reason 
for this code is to allow file names that have additional information, such as the timestamp of the file.

### Directory Structure
The `load_files` script assumes there is a root directory for a database.  The schema for the root folder can be
specified in the configuration file.  It defaults to `falcon_default_schema`. 

You can also have additional schemas under the root folder.  The name of the directory will be used as the schema name
with the convention and formatting for files being the same in all directories.

For example, say you have a database called `MY_COOL_DATABASE` and have two different schemas called `SCHEMA_A` and 
`SCHEMA_B` with tables in each.  You can create a directory for the data with two sub-directories named SCHEMA_A and
SCHEMA_B.  Then put the data to be loaded into those files.

### Process

The intended overall process for loading data using load_files is to automatically extract delimited 
files from the source system.  Then a semaphore file is written to the staging area that 
indicates all of the data has been staged for upload _*OR*_ the script is called directly or run manually.  

The load_files script is run via cron or other scheduling tool on regular intervals.  If the semaphore file exists 
then the script will load all of the data and move the files to a location for recovery.  After 
the files have been loaded the results are emailed to an admin.

**_WARNING:  Whatever process you implement, you must ensure that files are completely written before `tsload`
runs.  Failure to do so may result in partial data loads or errors._**

### Deploy and configure

`load_files` assumes a particular file structure.  The first time you run it, it will create the sub-directories needed.
The subdirectories are relative to the ROOT_DIR defined in the file.  For example, let's say you have a mounted drive
`/tsmnt` and want to use that for `load_files`.  You might create a `/bin` directory and put `load_files` in that directory.
Then configure to have ROOT_DIR point to `/tsmnt`.  The first time `tsload` is run, it will create multiple
subdirectories.  This data directory is where tsload expects to find the data file.  Note that you can create these 
directories manually and then they are not created.  

Once `load_files` has been deployed, edit the configuration file to use the variables and flags that are 
for file locations, etc.  Details of the configuration values are in the template `load.cfg`

## load_single_file

Loads a single file that is passed in as a parameter.

usage: `load_single_file $filename $loadtype`
where: 
* $filename is the name of the file to load 
* $loadtype is either 'full' or 'incremental'.  Full causes the `--empty_target` flag to be used.
  
### Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* The table names are the same as the names of the files with some allowed deviations (see below), 
e.g. SalesData.csv goes into a SalesData table
* The formats for dates, datetimes, boolean, and nulls are the same for all files
* (optionally) Email has been configured on the cluster so that results can be sent to an admin

### File names
load_single_file determines which table to update based on the name of the file.  To do so it looks for all
files with the extension specified in the DATA_FILE_EXTENSION variable.  It then truncates anything after
and `_` or `-`.  If you have table names with dashes or underscores you need to modify the line that strips
out details after these characters.  The reason for this code is to allow file names that have additional 
information, such as the timestamp of the file.

### Process

The intended overall process for loading data using load_single_file is to load a file using tsload.
The load_single_file script is typically called by another script that can pass in the name of the file
to load and the type of load to use.  

**_WARNING:  Whatever process you implement, you must ensure that files are completely written before `tsload`
runs.  Failure to do so may result in partial data loads._**

### Deploy and configure

Configure `load_single_file` to to point to the correct directories.  The data directory is where 
tsload expects to find the data file.  

Once `tsload` has been deployed, edit the file to use the variables and flags that are correct for your environment.
Note that there are two separate sections in the file to change.  At the top of the file are standard variables
for file locations, etc.  Lower down are the tsload flags to use for loading.  


