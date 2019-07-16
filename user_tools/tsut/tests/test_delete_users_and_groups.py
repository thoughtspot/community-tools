import unittest

from tsut.api import SyncUserAndGroups
from tsut.model import UsersAndGroups, Group, User, Visibility

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

TS_URL = "https://tstest"  # Test TS instance.
TS_USER = "tsadmin"
TS_PASSWORD = "admin"


class TestDeleteUsersAndGroups(unittest.TestCase):
    """Tests deleting users and groups."""

    def create_common_users_and_groups(self):
        """
        Creates a set of users and groups that can be used in multiple tests.
        """
        auag = UsersAndGroups()

        auag.add_group(
            Group(
                name="Group1",
                display_name="This is Group 1",
                description="A group for testing.",
                group_names=[],
                visibility=Visibility.DEFAULT,
            )
        )
        auag.add_group(
            Group(
                name="Group2",
                display_name="This is Group 2",
                description="Another group for testing.",
                group_names=["Group1"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )
        # Testing for ability to handle embedded quotes.
        auag.add_group(
            Group(
                name='Group"3"',
                display_name='This is Group "3"',
                description='Another "group" for testing.',
                group_names=["Group1"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        auag.add_user(
            User(
                name="User1",
                password="pwd1",
                display_name="User 1",
                mail="User1@company.com",
                group_names=["Group1"],
            )
        )
        auag.add_user(
            User(
                name="User2",
                password="pwd2",
                display_name="User 2",
                mail="User2@company.com",
                group_names=["Group1", "Group2"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )
        auag.add_user(
            User(
                name='User"3"',
                password="pwd2",
                display_name='User "3"',
                mail="User2@company.com",
                group_names=['Group"3"'],
            )
        )

        print(auag)

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.sync_users_and_groups(auag)

    def test_delete_user_list(self):
        """Tests deleting of a list of users."""

        self.create_common_users_and_groups()

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.delete_users(usernames=["User1", "User2", "UserX"])
        auag = sync.get_all_users_and_groups()
        self.assertFalse(auag.has_user("User1"))
        self.assertFalse(auag.has_user("User2"))
        self.assertTrue(auag.has_user('User"3"'))

    def test_delete_one_user(self):
        """Tests deleting a single users."""

        self.create_common_users_and_groups()

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.delete_user(username="User1")
        auag = sync.get_all_users_and_groups()
        self.assertFalse(auag.has_user("User1"))
        self.assertTrue(auag.has_user("User2"))
        self.assertTrue(auag.has_user('User"3"'))

    def test_delete_group_list(self):
        """Tests deleting of a list of groups."""

        self.create_common_users_and_groups()

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.delete_groups(groupnames=["Group1", "Group2", "GroupX"])
        auag = sync.get_all_users_and_groups()
        self.assertFalse(auag.has_group("Group1"))
        self.assertFalse(auag.has_group("Group2"))
        self.assertTrue(auag.has_group('Group"3"'))

    def test_delete_one_group(self):
        """Tests deleting a single groups."""

        self.create_common_users_and_groups()

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.delete_group(groupname="Group1")
        auag = sync.get_all_users_and_groups()
        self.assertFalse(auag.has_group("Group1"))
        self.assertTrue(auag.has_group("Group2"))
        self.assertTrue(auag.has_group('Group"3"'))
