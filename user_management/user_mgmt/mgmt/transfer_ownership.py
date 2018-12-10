#!/usr/bin/python

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


class TransferOwnership(object):

    def valid_args(self, args):
        """
        Verifies that the arguments are valid.  Don't quite validate all, so could still fail.
        :param args: List of arguments from the command line and defaults.
        :return:  True if valid.
        :rtype: bool
        """
        is_valid = True
        if args.ts_url is None or args.username is None or args.password is None or args.from_user is None \
                or args.to_user is None:
            eprint("Missing required parameters.")
            is_valid = False

        return is_valid

    def transfer_ownership(self, args):
        """
        Transfers ownership of all content from the from user to the to user.
        :param args: The command line arguments passed in.
        """
        xfer = TransferOwnershipApi(
            tsurl=args.ts_url,
            username=args.username,
            password=args.password,
            disable_ssl=True,
        )
        xfer.transfer_ownership(
            from_username=args.from_user, to_username=args.to_user
        )
