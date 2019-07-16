import unittest

import os
from tsut.model import UsersAndGroups, User, Group
from tsut.io import UGXLSWriter

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


class TestUGXLSWriter(unittest.TestCase):
    """Tests the AllUsersAndGroups class."""

    def test_write_to_xls(self):
        """Tests writing users and groups."""
        uags = UsersAndGroups()

        uags.add_group(
            Group(
                name="Group 1",
                display_name="This is Group 1",
                description="A group for testing.",
                group_names=[],
            )
        )
        uags.add_group(
            Group(
                name="Group 2",
                display_name="This is Group 2",
                description="Another group for testing.",
                group_names=["Group 1"],
            )
        )
        uags.add_group(
            Group(
                name='Group "3"',
                display_name='This is Group "3"',
                description='Another "group" for testing.',
                group_names=["Group 1", "Group 2"],
            )
        )

        uags.add_user(
            User(
                name="User1",
                password="pwd1",
                display_name="User 1",
                mail="User1@company.com",
                group_names=["Group 1"],
            )
        )
        uags.add_user(
            User(
                name="User2",
                password="pwd2",
                display_name="User 2",
                mail="User2@company.com",
                group_names=["Group 1", "Group 2"],
            )
        )
        # Testing for ability to handle embedded quotes.
        uags.add_user(
            User(
                name='User "3"',
                password="pwd2",
                display_name='User "3"',
                mail="User2@company.com",
                group_names=['Group "3"'],
            )
        )

        writer = UGXLSWriter()
        writer.write(uags, "test_uags")
        os.remove("test_uags.xlsx")

