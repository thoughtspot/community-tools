# Load Files

load_files consists of bash scripts that automate the process of loading files using ThoughtSpot's bulk loader
`tsload`.   There are currently two versions:
* load_files, which is designed to load multiple files from a directory  
* load_single_file, which is designed to load a single file at a time, with the file name being 
passed in as a parameter.

Each script is described below, but for full details on configuring the script see the comments inside
of each script.

## load_files

Loads one or more files from a given directory using ThoughtSpot's `tsload` and then moves to an archive location.

usage:  `load_files`

### Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* The table names are the same as the names of the files with some allowed deviations (see below), 
e.g. SalesData.csv goes into a SalesData table.
* The formats for dates, datetimes, boolean, and nulls are the same for all files.
* (optionally) Email has been configured on the cluster so that results can be sent to an admin.

### File names
load_files determines which table to update based on the name of the file.  To do so it looks for all
files with the extension specified in the DATA_FILE_EXTENSION variable.  It then truncates anything after
and `_` or `-`.  If you have table names with dashes or underscores you need to modify the line that strips
out details after these characters.  The reason for this code is to allow file names that have additional 
information, such as the timestamp of the file.

### Process

The intended overall process for loading data using load_files is to automatically extract delimited 
files from the source system.  Then a semaphore file is written to the staging area that 
indicates all of the data has been staged for upload _*OR*_ the script is called manually.  

The load_files script is run via cron or other scheduling tool on regular intervals.  If the semaphore file exists 
then the script will load all of the data and move the files to a location for recovery.  After 
the files have been loaded the results are emailed to an admin.

**_WARNING:  Whatever process you implement, you must ensure that files are completely written before `tsload`
runs.  Failure to do so may result in partial data loads._**

### Deploy and configure

`load_files` assumes a particular file structure.  The first time you run it, it will create the sub-directories needed.
The subdirectories are relative to the ROOT_DIR defined in the file.  For example, let's say you have a mounted drive
`/tsmnt` and want to use that for `tsload`.  You might create a `/bin` directory and put `load_files` in that directory.
Then configure `load_files` to have ROOT_DIR point to `/tsmnt`.  The first time `tsload` is run, it will create multiple
subdirectories, one of which is called `/data`.  This data directory is where tsload expects to find the data file.  Note 
that you can create this directory manually and then it's not created.  

Once `tsload` has been deployed, edit the file to use the variables and flags that are correct for your environment.
Note that there are two separate sections in the file to change.  At the top of the file are standard variables
for file locations, etc.  Lower down are the tsload flags to use for loading.  

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


