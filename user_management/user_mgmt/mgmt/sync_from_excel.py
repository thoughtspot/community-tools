#!/usr/bin/env python

import os
from tsUserGroupApi import eprint
from tsUserGroupApiIO import UGXLSReader

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


class SyncFromExcel(object):

    def get_sheets_and_headers(self):
        header_desc = "Required sheets and columns"

        for sheet_name in UGXLSReader.required_sheets:
            header_desc += "  |  %s:  " % sheet_name
            col_headers = UGXLSReader.required_columns[sheet_name]
            first = True
            for ch in col_headers:
                if not first:
                    header_desc += ", "
                else:
                    first = False
                header_desc += ch

        return header_desc

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

        # Must provide a filename that exists.  This doesn't check that the file is valid.
        if args.filename is None or not os.path.isfile(args.filename):
            eprint("A valid file path must be specified.")
            is_valid = False

        return is_valid
