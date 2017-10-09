#!/usr/bin/env python

'''Delete records from tables based on a CSV document.  
   Each line of the description file has the following format:  table_name, col1, col2, etc.
   Each line of the data file has the following format: table_name, val1, val2, etc.
   The delete will be of the format DELETE FROM table_name WHERE col1 = val1 AND col2 = val2, etc.
   
   ASSUMPTIONS:
     * the format of TQL output will not change
     * this script will be run on the appliance and be able to call TQL to execute delete commands.
     * fields do not contain the separator value.
'''

from __future__ import print_function
import sys
import argparse
import csv
import json
import os.path

import subprocess
from subprocess import check_output
from subprocess import call

def main():
  args = parse_args()
  if check_args(args):
    read_descriptions(args)
    generate_deletes(args)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", 
                        help="path to file with records to delete")
    parser.add_argument("-t", "--table", 
                        help="name of the table to delete records from")
    parser.add_argument("-d", "--database",
                        help="database to delete from")
    parser.add_argument("-s", "--schema",
                        default="falcon_default_schema",
                        help="schema to delete from")
    parser.add_argument("-p", "--separator",
                        default="|",
                        help="separator to use in data")
    args = parser.parse_args()
    return args


# description of the tables in the database.  
# { table1 : { column_name : type, ... }, table2 : { column_name : type, ...} }
descriptions={}


def check_args(args):
  args_are_good = True

  if (args.filename is None or os.path.isfile(args.filename) is False):
    eprint("Delete file %s was not found." % args.filename)
    args_are_good = False
    
  if (args.table is None):
    eprint("Table was not specified.")
    args_are_good = False

  if (args.database is None):
    eprint("Database was not specified.")
    args_are_good = False

  return args_are_good
  

def read_descriptions(args):
  '''Reads the table descriptions from the database schema and populates the descriptions.
     WARNING:  This depends on the format of tql output not changing.
  '''

  table_list = check_output ('echo "show tables %s;" | tql' % args.database, shell=True).split("\n")
  for table in table_list:
    table_details = table.split("|")
    if len(table_details) >= 2:
      schema_name = table_details[0].strip()
      table_name = table_details[1].strip()

      schema = descriptions.get(schema_name, None)
      if schema is None:
        schema = {}

      table = schema.get(table_name, None)
      if table is None:
        table = {}

      column_list = check_output ('echo "show table %s.%s.%s;" | tql' % (args.database, schema_name, table_name), shell=True).split("\n")
      for column in column_list:
        column_details = column.split("|")
        if len(column_details) >= 2:
          column_name = column_details[0].strip()
          column_type = column_details[2].strip()
          table[column_name] = column_type

      schema[table_name] = table
      descriptions[schema_name] = schema

  #print (descriptions)


def generate_deletes(args):
  
  # get the column descriptions.
  columns = descriptions.get(args.schema, {}).get(args.table, None)

  if columns is None:
    eprint ("Table %s.%s not found." % (args.schema, args.table))
    return

  with open(args.filename, 'rb') as valuefile:
    filereader = csv.DictReader(valuefile, delimiter='|', quotechar='"')
    for values in filereader:

      delete_stmt = "echo \"DELETE FROM %s.%s.%s WHERE " % (args.database, args.schema, args.table)

      first = True
      for key in values.keys():
        if not first:
          delete_stmt += " AND "
        else:
          first = False

        # TODO see if I need to un-quote non-numeric.  Might need to re-do desc file.
        if "int" in columns[key] or "double" in columns[key]:
          delete_stmt += ("%s = %s" % (key, values[key]))
        else:
          delete_stmt += ("%s = '%s'" % (key, values[key]))

      delete_stmt += ";\" | tql"
      print (delete_stmt)
      subprocess.call(delete_stmt, shell=True)

  valuefile.close()

def eprint (*args, **kwargs):
  '''Prints to standard error'''
  print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
  main()
