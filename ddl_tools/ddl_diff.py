#!/usr/bin/env python
"""
Compares two different DDL files and outputs the differences or ALTER statements to make the first match the second.

Copyright 2018 ThoughtSpot

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

NOTE:  There are many things that could be more efficient.
The following assumptions are made about the DDL being read:
  CREATE TABLE occur together on a single line, not split across lines.
  CREATE TABLE statements will not occur inside of a comment block.
  Delimiters, such as commas, will not be part of the table or column name.
  Comment characters, such as #, --, or /* */ will not be part of a column name.
  CREATE TABLE will have (....) with no embedded, unbalanced parentheses.
"""
import argparse
import os
from datamodel import eprint
from datamodelio import DDLParser
from datamodeldiff import DDLCompare, TQLAlterWriter
import logging

#logging.basicConfig(level=logging.DEBUG)


def main():
    """Main function for the script."""
    args = parse_args()

    if valid_args(args):
        print(args)

        ddl_parser = DDLParser(database_name=args.database, schema_name=args.schema)
        db_1 = ddl_parser.parse_ddl(args.ddl1)
        ddl_parser = DDLParser(database_name=args.database, schema_name=args.schema)
        db_2 = ddl_parser.parse_ddl(args.ddl2)

        # Returns differences for each database as a tuple.
        database_differences = DDLCompare.compare_databases(db_1, db_2)

        if args.alter1:
            logging.debug("generate alters for first schema to match the second")
            print("-- changes needed for first schema to match the second")
            TQLAlterWriter().write_alters(database_differences[0])

        if args.alter2:
            logging.debug("generate alters for second schema to match the first")
            print("-- changes needed for second schema to match the first")
            TQLAlterWriter().write_alters(database_differences[1])

        if not args.alter1 and not args.alter2:
            print("Database differences for DB 1:")
            for db_diff in database_differences[0]:
                print("\t%s" % db_diff)

            print("Database differences for DB 2:")
            for db_diff in database_differences[1]:
                print("\t%s" % db_diff)


def parse_args():
    """Parses the arguments from the command line."""
    parser = argparse.ArgumentParser("ddl_diff compares two DDL files and "
                                     "can generate changes to make the first match the second")

    parser.add_argument(
        "--ddl1", help="DDL file containing the schema that would be changed."
    )

    parser.add_argument(
        "--ddl2", help="DDL file containing the new schema."
    )

    parser.add_argument(
        "--database", default="MY_DATABASE", help="name of database for generating alter statements"
    )

    parser.add_argument(
        "--schema", default="falcon_default_schema",
        help="name of schema for generating alter statements"
    )

    parser.add_argument(
        "--alter1",
        action="store_true",
        help="Generates drop, create, alter, etc. statements that would be "
             "needed to make the first DDL align with the second."
    )

    parser.add_argument(
        "--alter2",
        action="store_true",
        help="Generates drop, create, alter, etc. statements that would be "
             "needed to make the second DDL align with the first."
    )
    parser.add_argument("--ignore_case",
                        action="store_true",
                        help="Causes case of names to be ignored")

    args = parser.parse_args()
    return args


def valid_args(args):
    """
    Checks to see if the arguments make sense.
    :param args: The command line arguments.
    :return: True if valid, False otherwise.
    """

    ret_value = True

    # make sure there is a to_ flag since data has to come from somewhere unless this is just creating blank Excel.
    if not args.ddl1 or not args.ddl2:
        eprint("--ddl1 and --ddl2 must be provided")
        ret_value = False

    else:
        if not os.path.exists(args.ddl1):
            eprint("file %s doesn't exist" % args.ddl1)
            ret_value = False
        if not os.path.exists(args.ddl2):
            eprint("file %s doesn't exist" % args.ddl2)
            ret_value = False

    return ret_value


if __name__ == "__main__":
    main()
