# Load Files

`load_files` is a bash script that automate the process of loading files using ThoughtSpot's bulk loader
`tsload`.   The benefit of using `load_files` is that it's configurable and manages error handling, 
archiving loaded files as well as logging and reporting status.

`load_files` supports loading local files as well as directly loading from an AWS S3 bucket (as-of TS v5.2).

There are two other utility scripts available in this folder, which are useful for data preparation and validation.

The full documentation can be found here: [load_files and utilities documentation](./documentation/Documentation.md)
