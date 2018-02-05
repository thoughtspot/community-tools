#!/usr/bin/python

import sys
import argparse
from tsUserGroupApi import SyncUserAndGroups, eprint

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
        sync = SyncUserAndGroups(tsurl=args.ts_url, username=args.username, password=args.password,
                                 disable_ssl=args.disable_ssl)
        if args.users is not None:
            delete_users(args, sync)
        if args.groups is not None:
            delete_groups(args, sync)


def str2bool(v):
    """
    Allows users to specify a variety of answers for booleans.
    :param v: The arg value passed.
    :type v: str
    :return: True or False
    :rtype: bool
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_args():
    """
    Parses the arguments from the command line.
    :returns: The arguments object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ts_url",
                        help="URL to ThoughtSpot, e.g. https://myserver")
    parser.add_argument("-u", "--username",
                        default='tsadmin',
                        help="Name of the user to log in as.")
    parser.add_argument("-p", "--password",
                        default='admin',
                        help="Password for login of the user to log in as.")
    parser.add_argument("--disable_ssl", action="store_true",
                        help="Will ignore SSL errors.")
    parser.add_argument("--users",
                        help="List of comma separated users.  Use quotes if there are spaces.")
    parser.add_argument("--groups",
                        help="List of comma separated groups.  Use quotes if there are spaces.")
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

    if args.users is None and args.groups is None:
        eprint("Must provide a list of users and/or groups to delete.")
        is_valid = False

    return is_valid


def delete_users(args, sync):
    """
    Deletes the named users.
    :param args: The command line arguments.  Includes the list of users.
    :type args: dict
    :param sync: A sync to use for deleting users.
    :type sync: SyncUserAndGroups
    """
    users = [x.strip() for x in args.users.split(",")]
    sync.delete_users(usernames=users)


def delete_groups(args, sync):
    """
    Deletes the named groups.
    :param args: The command line arguments.  Includes the list of users.
    :type args: dict
    :param sync: A sync to use for deleting users.
    :type sync: SyncUserAndGroups
    """
    groups = [x.strip() for x in args.groups.split(",")]
    sync.delete_groups(groupnames=groups)

if __name__ == "__main__":
    main()
