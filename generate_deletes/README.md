# Generate Deletes

This script is intended to generate delete commands based on date column values.

## Usage
1.  Modify the script to set your database and schema.
2.  Declare your tables, setting the table name, column name, number of days, and if to delete prior or after.

## Assumptions
* All of the tables are in the same database and schema.
* Only handle day, month, year.
* Only deleting based on a single column's date value.

