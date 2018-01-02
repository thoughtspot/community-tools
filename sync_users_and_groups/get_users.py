#!/usr/bin/python

from __future__ import print_function
import sys
import argparse
from tsUserGroupApi import SyncUserAndGroups, UGXLSWriter

"""
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
"""

"""
This script will retrieve users and groups and write the results to an output file.
"""


def main():
    """Main function for the script."""
    args = parse_args()
    if valid_args(args):
        dump_users_and_groups(args)


def parse_args():
    """
    Parses the arguments from the command line.
    :returns: The arguments object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ts_url",
                        help="URL to Thoughtspot, e.g. https://myserver")
    parser.add_argument("-u", "--username",
                        default='tsadmin',
                        help="Name of the user to log in as.")
    parser.add_argument("-p", "--password",
                        default='admin',
                        help="Password for login of the user to log in as.")
    parser.add_argument("-o", "--output_type",
                        default="xls",
                        help="Output type, either xls or json")
    parser.add_argument("-f", "--filename",
                        default="users_and_groups",
                        help="Either the name of the json file or root of Excel file names.")
    args = parser.parse_args()
    return args


def valid_args(args):
    """
    Verifies that the arguments are valid.
    :param args: List of arguments from the command line and defaults.
    :return:  True if valid.
    :rtype: bool
    """
    is_valid = True
    if args.ts_url is None:
        eprint("Missing TS URL")
        is_valid = False

    # Allow some variation for excel for ease of use.
    if args.output_type not in ["xls", "excel" "json"]:
        eprint("Invalid output_type parameter %s" % args.output_type)
        is_valid = False

    return is_valid


def dump_users_and_groups(args):
    """
    Gets users and groups from the server and dumps them in the correct format.
    :param args: The command line arguments.
    """
    sync = SyncUserAndGroups(tsurl=args.ts_url, username=args.username, password=args.password)
    all_users_and_groups = sync.get_all_users_and_groups()

    print ("writing to %s" % args.filename)

    if args.output_type is "json":
        with open(args.filename, "w") as outfile:
            outfile.write(all_users_and_groups.to_json())
    else:
        writer = UGXLSWriter()
        writer.write(users_and_groups=all_users_and_groups, filename=args.filename)


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


if __name__ == "__main__":
    """
    Run the program if this is the main script.
    """
    main()
