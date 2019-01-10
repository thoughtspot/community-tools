import sys
from os.path import abspath, dirname, join
import unittest

sys.path.insert(0, join(abspath(dirname(dirname(__file__))), 'mgmt'))
from tsUserGroupApi import SyncUserAndGroups, Privileges, SetGroupPrivilegesAPI
from tsUserGroupApiDataModel import UsersAndGroups, User, Group, Visibility

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

TS_URL = "https://test_ts"  # test ThoughtSpot server.
TS_USER = "tsadmin"
TS_PASSWORD = "admin"


class TestSyncUsersAndGroups(unittest.TestCase):
    """
    Tests synchronizing with ThoughtSpot.
    """

    def create_common_users_and_groups(self):
        """
        Creates a set of users and groups that can be used in multiple tests.
        """
        auag = UsersAndGroups()

        auag.add_group(
            Group(
                name="Group 1",
                display_name="This is Group 1",
                description="A group for testing.",
                group_names=[],
                visibility=Visibility.DEFAULT,
            )
        )
        auag.add_group(
            Group(
                name="Group 2",
                display_name="This is Group 2",
                description="Another group for testing.",
                group_names=["Group 1"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )
        # Testing for ability to handle embedded quotes.
        auag.add_group(
            Group(
                name='Group "3"',
                display_name='This is Group "3"',
                description='Another "group" for testing.',
                group_names=["Group 1"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        auag.add_user(
            User(
                name="User1",
                password="pwd1",
                display_name="User 1",
                mail="User1@company.com",
                group_names=["Group 1"],
            )
        )
        auag.add_user(
            User(
                name="User2",
                password="pwd2",
                display_name="User 2",
                mail="User2@company.com",
                group_names=["Group 1", "Group 2"],
                visibility=Visibility.NON_SHAREABLE,
            )
        )

        # Testing for ability to handle embedded quotes.
        auag.add_user(
            User(
                name='User "3"',
                password="pwd2",
                display_name='User "3"',
                mail="User2@company.com",
                group_names=['Group "3"'],
            )
        )

        print(auag)

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sync.sync_users_and_groups(auag, remove_deleted=True)

    def test_syncing_user_and_groups(self):
        """
        Tests adding users and groups to ThoughtSpot.
        """

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        auag = sync.get_all_users_and_groups()

        group1 = auag.get_group("Group 1")
        self.assertEqual("Group 1", group1.name)
        self.assertEqual("This is Group 1", group1.displayName)
        self.assertEqual("A group for testing.", group1.description)
        self.assertEqual([], group1.groupNames)
        self.assertEqual(Visibility.DEFAULT, group1.visibility)

        group2 = auag.get_group("Group 2")
        self.assertEqual("Group 2", group2.name)
        self.assertEqual("This is Group 2", group2.displayName)
        self.assertEqual("Another group for testing.", group2.description)
        self.assertEqual(["Group 1"], group2.groupNames)
        self.assertEqual(Visibility.NON_SHAREABLE, group2.visibility)

        user1 = auag.get_user("User1")
        self.assertEqual("User1", user1.name)
        self.assertEqual("User 1", user1.displayName)
        self.assertEqual(["All", "Group 1"], user1.groupNames)
        self.assertEqual(Visibility.DEFAULT, user1.visibility)

        user2 = auag.get_user("User2")
        self.assertEqual("User2", user2.name)
        self.assertEqual("User 2", user2.displayName)
        self.assertEqual(
            sorted(["All", "Group 1", "Group 2"]), sorted(user2.groupNames)
        )
        self.assertEqual(Visibility.NON_SHAREABLE, user2.visibility)

    def test_syncing_user_and_groups_without_password(self):
        """
        Tests adding users and groups to ThoughtSpot.
        """

        auag = UsersAndGroups()

        auag.add_group(
            Group(
                name="Group 1",
                display_name="This is Group 1",
                description="A group for testing.",
                group_names=[],
            )
        )
        auag.add_group(
            Group(
                name="Group 2",
                display_name="This is Group 2",
                description="Another group for testing.",
                group_names=["Group 1"],
            )
        )

        auag.add_user(
            User(
                name="User1",
                password="pwd1",
                display_name="User 1",
                group_names=["Group 1"],
            )
        )
        auag.add_user(
            User(
                name="User2",
                password="pwd2",
                display_name="User 2",
                group_names=["Group 1", "Group 2"],
            )
        )

        # only works on Bill's AWS instance.
        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            global_password="foo",
            disable_ssl=True,
        )
        sync.sync_users_and_groups(auag)

    def test_duplicate_users(self):
        """Tests creating duplicate users with different flags."""

        auag = UsersAndGroups()

        # create a duplicate with default flag to raise an error.
        auag.add_user(User(name="user1"))
        with self.assertRaises(Exception):
            auag.add_user(User(name="user1"))

        # create with overwrite.
        auag.add_user(
            User(name="user2", mail="user2@foo.com", group_names=["group2"]),
            duplicate=UsersAndGroups.OVERWRITE_ON_DUPLICATE,
        )
        u = auag.get_user("user2")
        self.assertEqual(u.name, "user2")
        self.assertEqual(u.mail, "user2@foo.com")
        self.assertEqual(u.groupNames, ["group2"])

        auag.add_user(
            User(name="user2", mail="user2@bar.com", group_names=["group3"]),
            duplicate=UsersAndGroups.OVERWRITE_ON_DUPLICATE,
        )
        u = auag.get_user("user2")
        self.assertEqual(u.name, "user2")
        self.assertEqual(u.mail, "user2@bar.com")
        self.assertEqual(u.groupNames, ["group3"])

        # create with update.
        auag.add_user(
            User(name="user3", mail="user3@foo.com", group_names=["group2"]),
            duplicate=UsersAndGroups.UPDATE_ON_DUPLICATE,
        )
        u = auag.get_user("user3")
        self.assertEqual(u.name, "user3")
        self.assertEqual(u.mail, "user3@foo.com")
        self.assertEqual(u.groupNames, ["group2"])

        auag.add_user(
            User(name="user3", mail="user3@bar.com", group_names=["group3"]),
            duplicate=UsersAndGroups.UPDATE_ON_DUPLICATE,
        )
        u = auag.get_user("user3")
        self.assertEqual(u.mail, "user3@bar.com")
        self.assertEqual(u.groupNames, ["group3", "group2"])

        # create with ignore.
        auag.add_user(
            User(name="user4", mail="user4@foo.com", group_names=["group2"]),
            duplicate=UsersAndGroups.IGNORE_ON_DUPLICATE,
        )
        u = auag.get_user("user4")
        self.assertEqual(u.name, "user4")
        self.assertEqual(u.mail, "user4@foo.com")
        self.assertEqual(u.groupNames, ["group2"])

        auag.add_user(
            User(name="user4", mail="user4@bar.com", group_names=["group3"]),
            duplicate=UsersAndGroups.IGNORE_ON_DUPLICATE,
        )
        u = auag.get_user("user4")
        self.assertEqual(u.name, "user4")
        self.assertEqual(u.mail, "user4@foo.com")
        self.assertEqual(u.groupNames, ["group2"])

    def test_duplicate_groups(self):
        """Tests creating duplicate groups with different flags."""

        auag = UsersAndGroups()

        # create a duplicate with default flag to raise an error.
        auag.add_group(Group(name="group1"))
        with self.assertRaises(Exception):
            auag.add_group(Group(name="group1"))

        # create with overwrite.
        auag.add_group(
            Group(name="group2", group_names=["group2"]),
            duplicate=UsersAndGroups.OVERWRITE_ON_DUPLICATE,
        )
        u = auag.get_group("group2")
        self.assertEqual(u.name, "group2")
        self.assertEqual(u.groupNames, ["group2"])

        auag.add_group(
            Group(name="group2", group_names=["group3"]),
            duplicate=UsersAndGroups.OVERWRITE_ON_DUPLICATE,
        )
        u = auag.get_group("group2")
        self.assertEqual(u.name, "group2")
        self.assertEqual(u.groupNames, ["group3"])

        # create with update.
        auag.add_group(
            Group(name="group3", group_names=["group2"]),
            duplicate=UsersAndGroups.OVERWRITE_ON_DUPLICATE,
        )
        u = auag.get_group("group3")
        self.assertEqual(u.name, "group3")
        self.assertEqual(u.groupNames, ["group2"])

        auag.add_group(
            Group(name="group3", group_names=["group3"]),
            duplicate=UsersAndGroups.UPDATE_ON_DUPLICATE,
        )
        u = auag.get_group("group3")
        self.assertEqual(u.groupNames, ["group2", "group3"])

    def test_update_non_shareable(self):
        """
        Tests updating groups that are non-shareable.
        """
        self.create_common_users_and_groups()
        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        auag = sync.get_all_users_and_groups()

        # Change Group 1 and Group 2 and verify change took.
        group1 = auag.get_group("Group 1")
        group1.visibility = Visibility.NON_SHAREABLE
        group2 = auag.get_group("Group 2")
        group2.visibility = Visibility.DEFAULT

        # sync updates
        sync.sync_users_and_groups(users_and_groups=auag)

        # verify changes
        auag = sync.get_all_users_and_groups()
        self.assertEqual(
            auag.get_group("Group 1").visibility, Visibility.NON_SHAREABLE
        )
        self.assertEqual(
            auag.get_group("Group 2").visibility, Visibility.DEFAULT
        )
        self.assertEqual(
            auag.get_group('Group "3"').visibility, Visibility.NON_SHAREABLE
        )

    def test_getting_all(self):
        """
        Tests getting all users from the server.
        """

        self.create_common_users_and_groups()

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        auag = sync.get_all_users_and_groups()

        # There are four constant users, tsadmin, guest, su, system
        self.assertEqual(auag.number_users(), 7)
        # There are two constant groups, Administrator and System
        self.assertEqual(auag.number_groups(), 6)

    def test_update_password(self):
        """
        Tests updating a user password.
        """

        sync = SyncUserAndGroups(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        auag = UsersAndGroups()
        auag.add_user(
            User(name="userx", display_name="User X", password="password1")
        )
        # sync updates
        sync.sync_users_and_groups(users_and_groups=auag)
        sync.update_user_password(
            userid="userx", currentpassword=TS_PASSWORD, password="password2"
        )

    def test_add_and_remove_privilege(self):
        """
        Tests adding a privilege to a group and then removing it.
        """

        self.create_common_users_and_groups()

        sgp = SetGroupPrivilegesAPI(
            tsurl=TS_URL,
            username=TS_USER,
            password=TS_PASSWORD,
            disable_ssl=True,
        )
        sgp.add_privilege(
            groups=["Group 1", "Group 2"], privilege=Privileges.CAN_USE_SPOTIQ
        )
