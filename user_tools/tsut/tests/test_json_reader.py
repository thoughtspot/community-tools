import unittest
import os

from tsut.api import UGJsonReader
from tsut.model import UsersAndGroups, User, Group, Visibility

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

    @staticmethod
    def get_test_json():
        """Creates some JSON for testing."""
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
                visibility=Visibility.NON_SHAREABLE,
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
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        return uags.to_json()

    def test_read_from_string(self):
        """Tests reading UaGs from a JSON string."""
        json_data = TestUGJSONReader.get_test_json()
        ugjr = UGJsonReader()
        uags = ugjr.read_from_string(json_data)
        self.verify_uags(uags)

    def test_read_from_file(self):
        """Tests reading UaGs from a JSON string."""
        json_data = TestUGJSONReader.get_test_json()

        # write a temp file for testing.
        filename = "test.json"
        with open(filename, "w") as json_file:
            json_file.write(json_data)

        ugjr = UGJsonReader()
        uags = ugjr.read_from_file(filename=filename)
        self.verify_uags(uags)

        # clean up the temp file
        os.remove(filename)

    def verify_uags(self, uags):
        """Verifies the parsed data.  Same logic for both methods of reading."""
        self.assertEqual(2, uags.number_groups())
        self.assertEqual(2, uags.number_users())

        g = uags.get_group("Group 1")
        self.assertIsNotNone(g)
        self.assertEqual(g.name, "Group 1")
        self.assertEqual(g.displayName, "This is Group 1")
        self.assertEqual(g.description, "A group for testing.")
        self.assertEqual(g.groupNames, [])
        self.assertEqual(g.visibility, Visibility.DEFAULT)

        g = uags.get_group("Group 2")
        self.assertIsNotNone(g)
        self.assertEqual(g.name, "Group 2")
        self.assertEqual(g.displayName, "This is Group 2")
        self.assertEqual(g.description, "Another group for testing.")
        self.assertEqual(g.groupNames, ["Group 1"])
        self.assertEqual(g.visibility, Visibility.NON_SHAREABLE)

        u = uags.get_user("User1")
        self.assertIsNotNone(u)
        self.assertEqual(u.name, "User1")
        self.assertEqual(u.displayName, "User 1")
        self.assertEqual(u.groupNames, ["Group 1"])
        self.assertEqual(u.visibility, Visibility.DEFAULT)

        u = uags.get_user("User2")
        self.assertIsNotNone(u)
        self.assertEqual(u.name, "User2")
        self.assertEqual(u.displayName, "User 2")
        self.assertEqual(sorted(u.groupNames), sorted(["Group 1", "Group 2"]))
        self.assertEqual(u.visibility, Visibility.NON_SHAREABLE)
