# DDL TOOLS

DDL tools was created to make working with DDL and converting from other schemas to ThoughtSpot easier.

Currently, there is only one DDL tool, convert_ddl, but more are planned in the future, along with additional features to be added to convet_ddl
 
## convert_ddl.py

Usage:  convert_ddl.py [flags]

To get a full list of the available flags, run convert_ddl.py --help

### Deploy

To run convert_ddl.py, you will need to put three files into the same directory of your choice:  
* convert_ddl.py
* datamodel.py
* datamodelio.py

You will also need to have Python 2.7 running in your environment.  Python 3 *might* work, but it's not been tested.

Tip:  Put the directory that you put these files into into your PATH and you can run from anywhere.

### Sample of common workflow

The standard workflow that we use with new DDL that we want to connvert uses the following steps:
* Convert from DDL to Excel
* Review and enhance the model in Excel
* Validate the model
* Convert from Excel to TQL DDL

After that, you can go ahead and create the database tables in TQL.

### Sample commands

To convert from some other database DDL to Excel:
```
convert_ddl.py --from_ddl <somefile> --to_excel <somefile> --database <db-name>
```
This will result in a new excel file.  Note that the .xlsx extension is option on the excel file name.

To validate a model from Excel:
```
convert_ddl.py --from_excel <somefile>.xlsx --validate
```
You will either get errors or a message that the model is valid.

To convert from Excel to TQL DDL:
```bazaar
convert_ddl.py --from_excel <somefile>.xlsx --to_tql <somefile> 
```
You will get an output file that contains (hopefully) valid TQL syntax.

### Cleanup in Excel
convert_ddl.py does it's best to parse DDL from a wide variety of sources, but there are some feature gaps and 
occassional things you'll need to clean up.

WARNING:  Do not delete any of the existing columns.  Adding columns is OK.
 
#### Columns tab
The first tab has all of the columns.  You should look for data types of "UNKNOWN".  These are data types
in the original that the parser couldn't decide how to translate.  We are constantly finding new types and adding.

You should also review the columns to see if you like the type chosen.  In particular, we default to BIGINT and DOUBLE
when it's not obvious.  But you may not need these wider types.  Also, some DATE types should be mapped to DATETIME 
instead of DATE.  Finally, don't worry about the actual size in the VARCHAR.  We just ignore this in ThoughtSpot.

#### Tables tab

Most of this tab is automatically generated, but you will want to update three columns:  primary key, shard key, and 
number of shards.  The last two are only needed if you want to shard the table.  The # rows column is optional and 
doesn't impact TQL generation, but it helps with determining shard needs.  

#### Foreign keys tab

The foreign keys tab allows you to enter FK relationships between the tables.  The columns should be obvious.  
Note that ThoughtSpot requires a foreign key to reference a primary key and the number and type of columns
must match.  The validation step will check for these conditions.  

You can use any name you like.  A common practice is FK_fromtable_to_totable.  You can use the following
formula in the first column to generate this formula.  ="FK_"&D2&"_to_"&F2 (in the second row.)  Note that this does 
not work if you have more than one relationship between tables.

#### Relationships tab

The relationships tab lets you enter relationships between tables.  In general, you should try to use foreign keys, but 
sometimes relationships are more appropriate.  The condition must be a valid condition between the tables.  This 
condition is not validated by the validator other than it exists.

## Future features

While there is no timeline for additional features, some of the planned enhancements include:
* Automatically identifying primary keys
* Automatically identifying foreign keys
* Automatically generating tsload commands (started, but not finished)
* Providing a tool to look at the difference between two schemas and generate alter table commands
