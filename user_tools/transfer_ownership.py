#!/usr/bin/python

import argparse
from tsut.api import eprint, TransferOwnershipApi
from tsut.apps import add_cnx_parser_arguments

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


def run_app():
    """Runs to transfer ownership."""
    args = get_args()
    if valid_args(args):
        transfer_ownership(args)


def get_args():

    parser = argparse.ArgumentParser()

    add_cnx_parser_arguments(parser=parser)
    parser.add_argument("--from_user", help="User to transfer ownership from.")
    parser.add_argument("--to_user", help="User to transfer ownership to.")

    return parser.parse_args()


def valid_args(args):
    """
    Verifies that the arguments are valid.  Don't quite validate all, so could still fail.
    :param args: List of arguments from the command line and defaults.
    :return:  True if valid.
    :rtype: bool
    """
    is_valid = True
    if not args.ts_url or not args.username or not args.password or not args.from_user or not args.to_user:
        eprint("Missing required parameters.")
        is_valid = False

    return is_valid


def transfer_ownership(args):
    """
    Transfers ownership of all content from the from user to the to user.
    :param args: The command line arguments passed in.
    """
    xfer = TransferOwnershipApi(
        tsurl=args.ts_url,
        username=args.username,
        password=args.password,
        disable_ssl=args.disable_ssl
    )
    xfer.transfer_ownership(
        from_username=args.from_user, to_username=args.to_user
    )


if __name__ == "__main__":
    run_app()
