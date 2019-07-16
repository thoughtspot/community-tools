import unittest
import os

from tsut.model import UsersAndGroups, User, Group, Visibility
from tsut.io import UGXLSReader, UGXLSWriter

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


class TestUGJSONReader(unittest.TestCase):
    """Tests the AllUsersAndGroups class."""

    def test_read_ugs_from_excel(self):
        """Writes a test file, then reads from it."""

        uags_out = UsersAndGroups()

        uags_out.add_user(
            User(
                name="user1",
                password="pwd1",
                display_name="User 1",
                mail="user1@company.com",
                group_names=["Group1"],
                visibility=Visibility.DEFAULT,
            )
        )
        uags_out.add_user(
            User(
                name="user2",
                password="pwd2",
                display_name="User 2",
                mail="user2@company.com",
                group_names=["Group1", "Group2"],
                visibility=Visibility.DEFAULT,
            )
        )
        uags_out.add_user(
            User(
                name="user3",
                password="pwd3",
                display_name="User 3",
                mail="user3@company.com",
                group_names=["Group3"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        uags_out.add_group(
            Group(
                name="Group1",
                display_name="Group 1",
                description="Test group 1",
                visibility=Visibility.DEFAULT,
            )
        )
        uags_out.add_group(
            Group(
                name="Group2",
                display_name="Group 2",
                description="Test group 2",
                group_names=["Group1"],
                visibility=Visibility.DEFAULT,
            )
        )
        uags_out.add_group(
            Group(
                name="Group3",
                display_name="Group 3",
                description="Test group 3",
                group_names=["Group1", "Group2"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        excel_filename = "test_read_write.xlsx"
        UGXLSWriter().write(uags_out, excel_filename)

        uags_in = UGXLSReader().read_from_excel(excel_filename)
        os.remove(excel_filename)

        # Verify the users.

        user = uags_in.get_user("user1")
        self.assertIsNotNone(user)
        self.assertEqual("user1", user.name)
        self.assertEqual("pwd1", user.password)
        self.assertEqual("User 1", user.displayName)
        self.assertEqual("user1@company.com", user.mail)
        self.assertEqual(["Group1"], user.groupNames)
        self.assertEqual(Visibility.DEFAULT, user.visibility)

        user = uags_in.get_user("user2")
        self.assertIsNotNone(user)
        self.assertEqual("user2", user.name)
        self.assertEqual("pwd2", user.password)
        self.assertEqual("User 2", user.displayName)
        self.assertEqual("user2@company.com", user.mail)
        self.assertEqual(["Group1", "Group2"], user.groupNames)
        self.assertEqual(Visibility.DEFAULT, user.visibility)

        user = uags_in.get_user("user3")
        self.assertIsNotNone(user)
        self.assertEqual("user3", user.name)
        self.assertEqual("pwd3", user.password)
        self.assertEqual("User 3", user.displayName)
        self.assertEqual("user3@company.com", user.mail)
        self.assertEqual(["Group3"], user.groupNames)
        self.assertEqual(Visibility.NON_SHAREABLE, user.visibility)

        # Verify the groups.

        group = uags_in.get_group("Group1")
        self.assertEqual("Group1", group.name)
        self.assertEqual("Group 1", group.displayName)
        self.assertEqual("Test group 1", group.description)
        self.assertEqual([], group.groupNames)
        self.assertEqual(Visibility.DEFAULT, group.visibility)

        group = uags_in.get_group("Group2")
        self.assertEqual("Group2", group.name)
        self.assertEqual("Group 2", group.displayName)
        self.assertEqual("Test group 2", group.description)
        self.assertEqual(["Group1"], group.groupNames)
        self.assertEqual(Visibility.DEFAULT, group.visibility)

        group = uags_in.get_group("Group3")
        self.assertEqual("Group3", group.name)
        self.assertEqual("Group 3", group.displayName)
        self.assertEqual("Test group 3", group.description)
        self.assertEqual(["Group1", "Group2"], group.groupNames)
        self.assertEqual(Visibility.NON_SHAREABLE, group.visibility)
