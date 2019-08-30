import unittest

from tsut.model import UsersAndGroups, User, Group

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


class TestAllUsersAndGroups(unittest.TestCase):
    """Tests the AllUsersAndGroups class."""

    def test_adding_and_removing_users(self):
        """Tests adding and removing users."""
        auag = UsersAndGroups()

        auag.add_user(User("user1"))
        auag.add_user(User("user2"))

        self.assertTrue(auag.has_user("user1"))
        self.assertFalse(auag.has_user("user6"))
        self.assertEqual(auag.number_users(), 2)

        auag.remove_user("user1")
        self.assertFalse(auag.has_user("user1"))
        self.assertEqual(auag.number_users(), 1)

        self.assertTrue(auag.has_user("user2"))
        u = auag.get_user("user2")
        self.assertTrue(u.name, "user2")

        self.assertIsNone(auag.get_user("noone"))

    def test_duplicate_users(self):
        """Tests adding users with the same name, but duplicate in case."""
        auag = UsersAndGroups()

        auag.add_user(User("user1"))
        with self.assertRaises(Exception):
            auag.add_user(User("user1"))
        with self.assertRaises(Exception):
            auag.add_user(User("User1"))
        self.assertEqual(auag.number_users(), 1)

        self.assertTrue(auag.has_user("user1"))
        self.assertTrue(auag.has_user("User1"))

        auag.remove_user("user1")
        self.assertFalse(auag.has_user("user1"))
        self.assertEqual(auag.number_users(), 0)

    def test_adding_and_removing_groups(self):
        """Tests adding and removing groups."""
        auag = UsersAndGroups()

        auag.add_group(Group("Group1"))
        auag.add_group(Group("Group2"))
        auag.add_group(Group("Group3"))

        self.assertTrue(auag.has_group("Group1"))
        self.assertTrue(auag.has_group("Group2"))
        self.assertTrue(auag.has_group("Group3"))
        self.assertEqual(auag.number_groups(), 3)

        auag.remove_group("Group1")
        self.assertFalse(auag.has_group("Group1"))
        self.assertEqual(auag.number_groups(), 2)

        self.assertTrue(auag.has_group("Group2"))
        u = auag.get_group("Group2")
        self.assertTrue(u.name, "Group2")

        self.assertIsNone(auag.get_group("noone"))

    # noinspection PyUnresolvedReferences

    def test_to_json(self):
        """Tests converting to JSON"""
        auag = UsersAndGroups()

        auag.add_group(Group("group1"))
        auag.add_group(Group("group2", group_names=["group1"]))
        auag.add_user(User("user1", group_names=["group1"]))
        auag.add_user(User("user2", group_names=["group1", "group2"]))

        json_str = auag.to_json()
        self.assertTrue(json_str.startswith("[{ "))
        self.assertTrue(json_str.endswith("}]"))
        self.assertTrue('"name":"user1"' in json_str)
        self.assertTrue('"name":"user2"' in json_str)
        self.assertTrue('"name":"group1"' in json_str)
        self.assertTrue('"name":"group2"' in json_str)

    def test_is_valid(self):
        """Tests validating users and groups."""
        auag = UsersAndGroups()

        auag.add_group(Group("group1"))
        auag.add_group(Group("group2", group_names=["group1"]))
        auag.add_user(User("user1", mail="use2@email.addr", group_names=["group1"]))
        auag.add_user(User("user2", mail="use2@email.addr", group_names=["group1", "group2"]))

        results = auag.is_valid()
        self.assertTupleEqual((results.result, results.issues), (True, []))

        auag.add_user(
            User("user3", group_names=["group3"])
        )  # group3 doesn't exist.

        results = auag.is_valid()
        self.assertFalse(results.result)
