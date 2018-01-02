#!/usr/bin/python

import argparse
from tsUserGroupApi import eprint, TransferOwnershipApi

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
This script will transfer ownership of all objects from one user to another.
"""


def main():
    """Main function for the script."""
    args = parse_args()
    if valid_args(args):
        transfer_ownership(args)


def parse_args():
    """
    Parses the arguments from the command line.
    :returns: The arguments object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--ts_url",
                        help="URL to Thoughtspot, e.g. https://myserver")
    parser.add_argument("--username",
                        default='tsadmin',
                        help="Name of the user to log in as.")
    parser.add_argument("--password",
                        default='admin',
                        help="Password for login of the user to log in as.")
    parser.add_argument("--from_user",
                        help="Name of the user to transfer content from.")
    parser.add_argument("--to_user",
                        help="Name of the user to transfer content to.")
    args = parser.parse_args()
    return args


def valid_args(args):
    """
    Verifies that the arguments are valid.  Don't quite validate all, so could still fail.
    :param args: List of arguments from the command line and defaults.
    :return:  True if valid.
    :rtype: bool
    """
    is_valid = True
    if args.ts_url is None or args.username is None or args.password is None or \
            args.from_user is None or args.to_user is None:
        eprint("Missing required parameters.")
        is_valid = False

    return is_valid


def transfer_ownership(args):
    """
    Transfers ownership of all content from the from user to the to user.
    :param args: The command line arguments passed in.
    """
    xfer = TransferOwnershipApi(tsurl=args.ts_url, username=args.username, password=args.password, disable_ssl=True)
    xfer.transfer_ownership(from_username=args.from_user, to_username=args.to_user)


if __name__ == "__main__":
    """
    Run the program if this is the main script.
    """
    main()
