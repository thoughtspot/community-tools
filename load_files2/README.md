# Load Files

load_files.py is a Python script that automate the process of loading files using ThoughtSpot's bulk loader
`tsload`.   This script differs from the original bash script in two significant ways:
* You can run multiple loads simultaneously in separate processes
* All settings are done in a separate settings file rather than modifying the script.

## usage

```
usage: load_files.py [-h] [-f FILENAME]

optional arguments:
  -h, --help                       Show this help message and exit
  -f FILENAME, --filename FILENAME Name of the file with the settings in JSON.
```
                        
### Pre-conditions and assumptions

* The database has been created in ThoughtSpot using TQL
* All files to load have the same extension
* The table names are the same as the names of the files with some allowed deviations (see below), 
e.g. SalesData.csv goes into a SalesData table.
* The formats for dates, datetimes, boolean, and nulls are the same for all files.
* (optionally) Email has been configured on the cluster so that results can be sent to an admin.

### File names
`load_files.py` determines which table to update based on the name of the file.  To do so it looks for all
files with the extension specified in the settings file.  It then truncates anything after
`-`.  This means you can have filenames with additional detail, such as datetime, sequence number, etc. as long as
the additional data comes after a dash.

### Settings file

This script expects a settings file.  The default is a file named `settings.json` located in the same directory that
the file is running from.  If the file is located elsewhere or has a different name, specify the file name using the
--filename flag.

The settings file can only contain a valid JSON file.  The following is an example:

```
{
  "root_directory": "/Users/bill.back/ThoughtSpot/community-tools/load_files2/testing",
  "data_directory": "/Users/bill.back/ThoughtSpot/community-tools/load_files2/testing/data",
  "semaphore_filename": "load_now",
  "max_simultaneous_loads": "3",
  "max_archive_days": "14",
  "email_method": "osmail",
  "email_from": "bill.back@thoughtspot.com",
  "email_to": ["email1@addr.com", "email2@addr.com"],
  "move_files" : "true",
  "filename_extension": ".csv",
  "tsload.target_database": "test_db",
  "tsload.source_data_format": "csv",
  "tsload.empty_target": "true",
  "tsload.max_ignored_rows": "0",
  "tsload.has_header_row": "true",
  "tsload.trailing_field_separator": "false",
  "tsload.field_separator": "|",
  "tsload.escape_character": "\\\\",
  "tsload.enclosing_character": "\\\"",
  "tsload.null_value": "null",
  "tsload.date_format": "%M/%d/%y",
  "tsload.date_time_format": "%M/%d/%y %H:%M:%s",
  "tsload.boolean_representation": "True_False"
}
```

The following section describes the flags available:
* root_directory (required) - this is the directory that will be used for logs and archives.  The data folder can be under this
folder, but it's not required.
* data_directory (required) - this is the directory where files to be loaded will be placed.  The script will search this directory
for files with the correct extension to load.
* semaphore_filename (optional) - if this setting is provided, the script will look for a file with the given name in the
data directory before attempting to load data.  The use of this file is to ensure the data has been written before
and attempt to read is made.
* max_simultaneous_loads (optional) - this setting indicates the maximum number of loads that should occur 
simultaneously.  The recommended maximum is three.  If this flag is not provided, the maximum will be set to one.
* max_archive_days (optional) - if this setting is provided, it indicates how long to keep archives of loads.  Having
this flag can be helpful for cleaning up and not continuing to use more space for archiving.
* email_method (optional) - if this value is provided and is `osmail`, then mail on the system will be used.  This
setup is usually recommended since it doesn't require a password.  Any other setting will cause the mail API to be 
used.
* email_to (optional) - if provided, will cause email to be sent to the recipients.  This value must be a JSON list.
* email_from (optional) - this setting is only required if not using `osmail`  Indicates the user for the email.
* email_server (optional) - this setting is only required if not using `osmail`  Indicates the server for email.
* email_port (optional) - this setting is only required if not using `osmail`  Indicates the port for email.
* email_password (optional) -  this setting is only required if not using `osmail`  Indicates the password for email.
* move_files (optional) - if this flag is set to true (default) files are moved to the archive.  If not set or set to
false, files are copied to the archive, but not moved out of the data directory.  This setting is useful for testing.
* filename_extension (required) - indicates the extension on data files to be loaded.
* tsload._xxx_ (required/optional) - these flags are the flags to pass to tsload.  Each _xxx_ is the name of a valid
tsload flag and the value is what will be passed to tsload.  For true|false flags are either passed or not passed. 

### Process

The intended overall process for loading data using load_files.py is to automatically extract delimited 
files from the source system.  Then a semaphore file (optiona) is written to the staging area that 
indicates all of the data has been staged for upload _*OR*_ the script is called manually.  

If using a semaphore approach, the load_files script is run via cron or other scheduling tool on regular intervals.  If the semaphore file exists 
then the script will load all of the data and move the files to a location for recovery.  After 
the files have been loaded the results are emailed to an admin.

**_WARNING:  Whatever process you implement, you must ensure that files are completely written before `tsload`
runs.  Failure to do so may result in partial data loads._**

### Deploy and configure

`load_files.py` assumes a particular file structure.  The first time you run it, it will create the sub-directories needed.
The subdirectories are relative to the `root_directory` defined in the settings.  For example, let's say you have a mounted drive
`/tsmnt` and want to use that for `tsload`.  You might create a `/bin` directory and put `load_files` in that directory.
Then configure `load_files` to have `root_directory` point to `/tsmnt`.  The first time `load_files.py` is run, it will create multiple
subdirectories.


