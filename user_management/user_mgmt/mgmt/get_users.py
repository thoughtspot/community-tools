#!/usr/bin/python

from tsUserGroupApi import SyncUserAndGroups, eprint
from tsUserGroupApiIO import UGXLSWriter

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


class GetUsersGroups(object):

    def valid_args(self, args):
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
        if args.output_type not in ["xls", "excel", "json"]:
            eprint("Invalid output_type parameter %s" % args.output_type)
            is_valid = False

        return is_valid

    def dump_users_and_groups(self, args):
        """
        Gets users and groups from the server and dumps them in the correct format.
        :param args: The command line arguments.
        """
        sync = SyncUserAndGroups(
            tsurl=args.ts_url,
            username=args.username,
            password=args.password,
            disable_ssl=args.disable_ssl,
        )
        all_users_and_groups = sync.get_all_users_and_groups()

        if args.output_type == "json":
            print("writing to %s.json" % args.filename)
            with open(args.filename+'.json', "w") as outfile:
                outfile.write(all_users_and_groups.to_json())
        else:
            print("writing to %s.xlsx" % args.filename)
            writer = UGXLSWriter()
            writer.write(
                users_and_groups=all_users_and_groups, filename=args.filename
            )
