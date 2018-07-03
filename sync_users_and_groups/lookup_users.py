#!/usr/bin/python

import argparse
from tsUserGroupApi import SyncUserAndGroups, eprint, User

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
This script will look up users based on ID.
"""


def main():
    """Main function for the script."""
    args = parse_args()
    if valid_args(args):
        lookup_users(args)


def parse_args():
    """
    Parses the arguments from the command line.
    :returns: The arguments object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ts_url", help="URL to Thoughtspot, e.g. https://myserver"
    )
    parser.add_argument(
        "--username",
        default="tsadmin",
        help="Name of the user to log in as.",
    )
    parser.add_argument(
        "--password",
        default="admin",
        help="Password for login of the user to log in as.",
    )
    parser.add_argument(
        "--disable_ssl", action="store_true", help="Will ignore SSL errors."
    )
    parser.add_argument(
        "--filename",
        help="File that contains the GUIDs, one per line.",
    )
    parser.add_argument(
        "--guids",
        help="One or more GUIDs separated by commas.",
    )
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

    if not args.guids and not args.filename:
        eprint("Must provide a list of GUIDs or a file containing a list of GUIDs")
        is_valid = False

    return is_valid


def lookup_users(args):
    """
    Look up users based on the requested IDs.
    :param args: The command line arguments.
    """

    guids = read_guids(args)
    user_list = get_all_users(args)

    for user in user_list:
        if user.id in guids:
            print("%s ==> %s" % (user.id, user.name))


def get_all_users(args):
    """
    Gets the users from the server.
    :param args: The command line arguments.
    :return: The list of users and groups from the server.
    :rtype: list of User
    """
    sync = SyncUserAndGroups(
        tsurl=args.ts_url,
        username=args.username,
        password=args.password,
        disable_ssl=args.disable_ssl,
    )
    return sync.get_user_metadata()


def read_guids(args):
    """
    Reads the GUIDs from the command line.
    :param args: The command line arguments.
    :return: The GUIDs from the command line as a list.
    :rtype: list of str
    """
    guids = []
    if args.filename:
        with open(args.filename, "r") as guid_file:
            for line in guid_file:
                guids.append(line.strip().strip('"'))
    else:
        guids.extend([g.strip() for g in args.guids.split(",")])

    return guids


if __name__ == "__main__":
    """
    Run the program if this is the main script.
    """
    main()
