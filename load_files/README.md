# Load Files

load_files is a bash script that is intended to automate the loading process using tsload.  
load_single_file is a bash script that does the same as load_files, except on a single file that's passed in
as a parameter.

## Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* The table names are the same as the names of the files, e.g. SalesData.csv goes into a SalesData table
* The formats for dates, date times, and boolean are the same for all files.
* Null values are the same for all files.
* Email has been configured so that results can be sent to an admin.

## Process

The intended overall process for loading data using load_files is to automatically extract csv 
files from the source system.  Then a semaphore file is written to the staging area that 
indicates all of the data hasbeen staged for upload _*OR*_ the script is called manually.  

The load_files script is run via cron or other scheduling tool on regular intervals.  If the semaphore file exists 
then the script will load all of the data and move the files to a location for recovery.  After 
the files have been loaded the results are emailed to an admin.

## Deploy and configure

To deploy load_files, simply copy it into a location that can run tsload and can see the data files to load.  Then edit the file to use the variables and flags that are correct for your environment.
Note that there are two separate locations to change.  At the top of the file are standard variables
for file locations, etc.  Lower down are the flags to use for loading.  

## More info
See the actual files for more details on usage and configuration.
