#!/usr/bin/env python
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)

"""
Unit tests for tsApi.py.

Help command:

>>> python tsApiTest.py --help

Example command:

>>> python tsApiTest.py
    --hostport <hostport>
    --username <username>
    --password <password>
    --admin_user
    --disable_ssl
"""

import argparse
import logging
import sys
import unittest
import time

from globalClasses import Constants
from tsApi import TSApiWrapper, is_valid_uuid

HOSTPORT = None
USERNAME = None
PASSWORD = None
DISABLE_SSL = None
ADMIN_USER = None


class TestTSApi(unittest.TestCase):

    def test_login(self):
        """Tests login into a TS System."""
        ts = TSApiWrapper(DISABLE_SSL)
        self.assertFalse(ts._is_authenticated())
        ts.login(HOSTPORT, USERNAME, PASSWORD)
        self.assertTrue(ts._is_authenticated())

    def test_create_delete_user(self):
        """Tests creation and deletion of user by name 'newxyzuser'."""
        new_user = "newxyzuser"
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        #######################################################################

        # Test for LOCAL_USER create/delete.
        # Assert user doesnt exist in TS.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)
        # Create LOCAL user
        ts.create_user(new_user, new_user)
        # Assert user exists in TS now.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertTrue(flag)
        # Assert by default user type is set to LOCAL_USER.
        for user in ts.list_users().data:
            if user.name == new_user:
                self.assertEqual(TSApiWrapper.LOCAL_USER, user.type)
        # Create user again and check we get USER_ALREADY_EXISTS status.
        status = ts.create_user(new_user, new_user).status
        self.assertEqual(status, Constants.USER_ALREADY_EXISTS)

        # Get user id with name.
        user_id = ts.get_userid_with_name(new_user).data
        # Delete user.
        ts.delete_users([user_id])
        # Assert user no longer exists in TS System.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)

        #######################################################################

        # Test for LDAP_USER create/delete.
        # Assert user doesnt exist in TS.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)
        # Create LDAP user
        ts.create_user(new_user, new_user, TSApiWrapper.LDAP_USER)
        # Assert user exists in TS now.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertTrue(flag)
        # Assert user type is set to LDAP_USER.
        for user in ts.list_users().data:
            if user.name == new_user:
                self.assertEqual(TSApiWrapper.LDAP_USER, user.type)
        # Create user again and check we get USER_ALREADY_EXISTS status.
        status = ts.create_user(
            new_user, new_user, TSApiWrapper.LDAP_USER
        ).status
        self.assertEqual(status, Constants.USER_ALREADY_EXISTS)

        # Get user id with name.
        user_id = ts.get_userid_with_name(new_user).data
        # Delete user.
        ts.delete_users([user_id])
        # Assert user no longer exists in TS System.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)

        #######################################################################

        # Test for SAML_USER create/delete.
        # Assert user doesnt exist in TS.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)
        # Create SAML user
        ts.create_user(new_user, new_user, TSApiWrapper.SAML_USER)
        # Assert user exists in TS now.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertTrue(flag)
        # Assert user type is set to SAML_USER.
        for user in ts.list_users().data:
            if user.name == new_user:
                self.assertEqual(TSApiWrapper.SAML_USER, user.type)
        # Create user again and check we get USER_ALREADY_EXISTS status.
        status = ts.create_user(
            new_user, new_user, TSApiWrapper.SAML_USER
        ).status
        self.assertEqual(status, Constants.USER_ALREADY_EXISTS)

        # Get user id with name.
        user_id = ts.get_userid_with_name(new_user).data
        # Delete user.
        ts.delete_users([user_id])
        # Assert user no longer exists in TS System.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)

    def test_create_user_weak_password(self):
        """Tests user creation with weak password"""
        new_user = "newxyzuser"
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        #######################################################################

        # Test for LDAP_USER create/delete with weak password
        # Assert user doesn't exist in TS.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)
        # Create LDAP user with weak password
        weak_password = "adqadjdf12"
        status = ts.create_user(
            new_user, new_user, TSApiWrapper.LDAP_USER, weak_password).status
        self.assertEqual(status, Constants.OPERATION_FAILURE)
        # Assert user doesn't exist in TS.
        flag = new_user in [user.name for user in ts.list_users().data]
        self.assertFalse(flag)

    def test_create_delete_group(self):
        """Tests creation and deletion of user by name 'newxyzgroup'."""
        new_group = "newxyzgroup"
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        #######################################################################

        # Test for LOCAL_GROUP create/delete.
        # Assert group doesn't exist in TS.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertFalse(flag)
        # Create group.
        ts.create_group(new_group, new_group)
        # Assert group exists in TS now.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertTrue(flag)
        # Assert by default group type is set to LOCL_GROUP
        for group in ts.list_groups().data:
            if group.name == new_group:
                self.assertEqual(TSApiWrapper.LOCAL_GROUP, group.type)
        # Create group again and check we get GROUP_ALREADY_EXISTS status.
        status = ts.create_group(new_group, new_group).status
        self.assertEqual(status, Constants.GROUP_ALREADY_EXISTS)

        # Get group id with name.
        group_id = ts.get_groupid_with_name(new_group).data
        # Delete group.
        ts.delete_groups([group_id])
        # Assert group no longer existe in TS System.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertFalse(flag)

        #######################################################################

        # Test for LDAP_GROUP create/delete.
        # Assert group doesn't exist in TS.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertFalse(flag)
        # Create group.
        ts.create_group(new_group, new_group, TSApiWrapper.LDAP_GROUP)
        # Assert group exists in TS now.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertTrue(flag)
        # Assert group type is set to LDAP_GROUP
        for group in ts.list_groups().data:
            if group.name == new_group:
                self.assertEqual(TSApiWrapper.LDAP_GROUP, group.type)
        # Create group again and check we get GROUP_ALREADY_EXISTS status.
        status = ts.create_group(
            new_group, new_group, TSApiWrapper.LDAP_GROUP
        ).status
        self.assertEqual(status, Constants.GROUP_ALREADY_EXISTS)

        # Get group id with name.
        group_id = ts.get_groupid_with_name(new_group).data
        # Delete group.
        ts.delete_groups([group_id])
        # Assert group no longer existe in TS System.
        flag = new_group in [group.name for group in ts.list_groups().data]
        self.assertFalse(flag)

    def test_add_user_to_group(self):
        """Tests creation of following structure.
           Group: parent_group {
               User: member_user1,
               User: member_user2
           }
        """
        parent_group = "parent_group"
        member_user1 = "member_user1"
        member_user2 = "member_user2"

        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        # Create Parent Group
        ts.create_group(parent_group, parent_group)
        # Create members
        ts.create_user(member_user1, member_user1)
        ts.create_user(member_user2, member_user2)

        # Add member 1 to parent
        parent_gid = ts.get_groupid_with_name(parent_group).data
        member_uid1 = ts.get_userid_with_name(member_user1).data
        member_uid2 = ts.get_userid_with_name(member_user2).data

        # Update parent group with members.
        self.assertEqual(len(ts.list_users_in_group(parent_gid).data), 0)
        ts.add_user_to_group(member_uid1, parent_gid)
        self.assertEqual(len(ts.list_users_in_group(parent_gid).data), 1)
        ts.add_user_to_group(member_uid2, parent_gid)
        self.assertEqual(len(ts.list_users_in_group(parent_gid).data), 2)

        # Cleanup
        ts.delete_groups([parent_gid])
        ts.delete_users([member_uid1, member_uid2])

    def test_add_groups_to_group(self):
        """Tests creation of following structure.
           Group: parent_group {
               Group: member_group1,
               Group: member_group2
           }
        """
        parent_group = "parent_group"
        member_group1 = "member_group1"
        member_group2 = "member_group2"

        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        # Create Parent Group
        ts.create_group(parent_group, parent_group)
        # Create members
        ts.create_group(member_group1, member_group1)
        ts.create_group(member_group2, member_group2)

        # Add member 1 to parent
        parent_gid = ts.get_groupid_with_name(parent_group).data
        member_gid1 = ts.get_groupid_with_name(member_group1).data
        member_gid2 = ts.get_groupid_with_name(member_group2).data

        # Update parent group with members.
        self.assertEqual(len(ts.list_groups_in_group(parent_gid).data), 0)
        ts.add_groups_to_group([member_gid1], parent_gid)
        self.assertEqual(len(ts.list_groups_in_group(parent_gid).data), 1)
        ts.add_groups_to_group([member_gid2], parent_gid)
        self.assertEqual(len(ts.list_groups_in_group(parent_gid).data), 2)

        # Cleanup
        ts.delete_groups([member_gid1, member_gid2, parent_gid])

    def test_update_group(self):
        """Tests creation of following structure.
           Group: parent_group {
               Group: member_group {}
               User: member_user
           }
        """
        parent_group = "parent_group"
        member_group = "member_group"
        member_user = "member_user"

        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        # Create Parent Group
        ts.create_group(parent_group, parent_group)
        # Create members
        ts.create_group(member_group, member_group)
        ts.create_user(member_user, member_user)

        # Update parent group with members.
        parent_gid = ts.get_groupid_with_name(parent_group).data
        member_gid = ts.get_groupid_with_name(member_group).data
        member_uid = ts.get_userid_with_name(member_user).data
        ts.update_groups_to_group([member_gid], parent_gid)
        ts.update_users_to_group([member_uid], parent_gid)

        # Test for membership.
        groups = ts.list_groups_in_group(parent_gid).data
        self.assertEqual(groups[0].id, member_gid)
        users = ts.list_users_in_group(parent_gid).data
        self.assertEqual(users[0].id, member_uid)

        # Cleanup
        ts.delete_groups([member_gid, parent_gid])
        ts.delete_users([member_uid])

    def test_empty_group_relationship(self):
        """Tests creation of following structure.
           Group: parent_group {
               Group: member_group {}
               User: member_user
           }

           Updates parent_group to {}

           Checks for parent_group members to be empty.
        """
        parent_group = "parent_group"
        member_group = "member_group"
        member_user = "member_user"

        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        # Create Parent Group
        ts.create_group(parent_group, parent_group)
        # Create members
        ts.create_group(member_group, member_group)
        ts.create_user(member_user, member_user)

        # Update parent group with members.
        parent_gid = ts.get_groupid_with_name(parent_group).data
        member_gid = ts.get_groupid_with_name(member_group).data
        member_uid = ts.get_userid_with_name(member_user).data
        ts.update_groups_to_group([member_gid], parent_gid)
        ts.update_users_to_group([member_uid], parent_gid)

        # Test for membership.
        groups = ts.list_groups_in_group(parent_gid).data
        self.assertEqual(groups[0].id, member_gid)
        users = ts.list_users_in_group(parent_gid).data
        self.assertEqual(users[0].id, member_uid)

        # Update parent group with no members.
        ts.update_users_to_group([], parent_gid)
        ts.update_groups_to_group([], parent_gid)

        # Test for membership.
        groups = ts.list_groups_in_group(parent_gid).data
        self.assertEqual(groups, [])
        users = ts.list_users_in_group(parent_gid).data
        self.assertEqual(users, [])

        # Cleanup
        ts.delete_groups([member_gid, parent_gid])
        ts.delete_users([member_uid])

    def test_filtering_of_guids(self):
        """Tests filtering of non guids."""
        valid_guid_list = [
            "c56a4180-65aa-42ec-a945-5fd21dec0538",
            "2231647d-86a3-453b-312a-fd01e34a1f1e",
        ]
        invalid_guid_list = [None, "a", 1, "acdf1234-1-1-1-3", ""]
        test_input = valid_guid_list + invalid_guid_list
        test_output = filter(is_valid_uuid, test_input)
        self.assertEqual(len(test_output), 2)
        self.assertEqual(test_output[0], valid_guid_list[0])
        self.assertEqual(test_output[1], valid_guid_list[1])

    def test_invalid_guids_filtering_before_call(self):
        """Tests invalid guids are filtered before making API calls. As making
           API calls with empty guid list is valid these calls should succeed.
        """
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        analyst_group_guid = "c241143a-0e2b-44b6-9cbc-c2b3cff8c57d"
        invalid_guid_list = [None, "a", 1, "acdf1234-1-1-1-3", ""]

        # Validate various calls which accept guid list.
        status = ts.add_groups_to_group(
            invalid_guid_list, analyst_group_guid
        ).status
        self.assertEqual(status, Constants.OPERATION_SUCCESS)

        status = ts.update_users_to_group(
            invalid_guid_list, analyst_group_guid
        ).status
        self.assertEqual(status, Constants.OPERATION_SUCCESS)

        status = ts.update_groups_to_group(
            invalid_guid_list, analyst_group_guid
        ).status
        self.assertEqual(status, Constants.OPERATION_SUCCESS)

        status = ts.delete_users(invalid_guid_list).status
        self.assertEqual(status, Constants.OPERATION_SUCCESS)

        status = ts.delete_groups(invalid_guid_list).status
        self.assertEqual(status, Constants.OPERATION_SUCCESS)

    def test_list_users(self):
        """Tests that we list all users, regardless
           of batchsize requested.
           Note, this test takes some time due to the large number of
           users created to test the default batchsize.
           {
               User: user1,
               User: user2,...
               User: userN
           }
           Tests that list_users(batchsize=-1)
                      == list_users(batchsize=[0, N])
                      == list_users()
        """
        # Login
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        users = ["user" + str(i) for i in range(250)]
        # Create ts user objects
        for u in users:
            res = ts.create_user(u, u)
            sleep_time, create_count = 0.5, 0
            while res.status != Constants.OPERATION_SUCCESS:
                # Check if we have tried creating too many times
                if create_count > 3:
                    break
                # Sleep for @sleep_time seconds, so we do not choke ts instance
                time.sleep(sleep_time)
                res = ts.create_user(u, u)
                sleep_time *= 2
                create_count += 1

        user_ids = set(
            [ts.get_userid_with_name(user_name).data
             for user_name in users]
            ) # - set([None])
        # Check that all users were successfully created
        self.assertEqual(len(users), len(user_ids))

        # List all ts user objects (including default users Ex. 'system')
        for batchsize in [-1, 0, 100, 150, None]:
            users_batched = ts.list_users() if batchsize is None \
                            else ts.list_users(batchsize)
            users_batched = users_batched.data
            # Test if all returned users are unique
            self.assertTrue(len(users_batched) == len(set(users_batched)))
            # Get all user_ids from the returned list
            users_batched_ids = [user_obj.id for user_obj in users_batched]
            # Test if all relevant users are returned
            self.assertTrue(all([uid in users_batched_ids for uid in user_ids]))

        # Cleanup
        ts.delete_users(list(user_ids))

    def test_get_batched_users(self):
        """Tests that we list a batch of users with an offset.
            {
               User: user0,
               User: user1,...
               User: user5
            }
            offset = 3, batch = 2 -> [user3, user4]
        """
        # Login
        ts = TSApiWrapper(DISABLE_SSL)
        ts.login(HOSTPORT, USERNAME, PASSWORD)

        users = ["batched_user" + str(i) for i in range(12)]
        # Create ts user objects
        for u in users:
            ts.create_user(u, u)
        user_ids = set(
            [ts.get_userid_with_name(user_name).data
             for user_name in users]
            )

        # Test batched entities call with offset
        offset = 3
        batchsize = 2
        users_list_ids = [u.id for u in ts.list_users().data]
        users_batched = ts._get_batched_entities(
                            "User", offset, batchsize
                             ).data[0]
        users_batched_ids = [u.id for u in users_batched]
        self.assertEqual(users_batched_ids,
                        users_list_ids[offset:offset+batchsize])

        # Cleanup
        ts.delete_users(list(user_ids))


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hostport",
        help="Hostport in the format http(s)://host:port or http(s)://domain",
        default=None,
    )
    parser.add_argument("--username", help="Username", default=None)
    parser.add_argument("--password", help="Password", default=None)
    parser.add_argument(
        "--disable_ssl", help="Disable SSL authentication", action="store_true"
    )
    parser.add_argument(
        "--admin_user",
        help="Does the user have admin privileges",
        action="store_true",
    )
    arguments = parser.parse_args()
    assert arguments.hostport is not None, "HostPort cannot be None."
    HOSTPORT = arguments.hostport
    assert arguments.username is not None, "Username cannot be None."
    USERNAME = arguments.username
    assert arguments.password is not None, "Password cannot be None."
    PASSWORD = arguments.password
    assert arguments.disable_ssl is not None, "DisableSSL flag cannot be None."
    DISABLE_SSL = arguments.disable_ssl
    assert arguments.admin_user is not None, "Admin User flag cannot be None."
    ADMIN_USER = arguments.admin_user
    # Set sys.argv array to empty as without this unittest.main() too will try
    # to parse the arguments which are already parsed.
    sys.argv[1:] = []

    loader = unittest.loader.defaultTestLoader
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    suite = loader.loadTestsFromModule(sys.modules["__main__"])

    admin_only_test_msg = "User needs to be admin to run this test."
    for testSuite in suite:
        for test in testSuite:
            if not test.id().endswith("login") and ADMIN_USER is False:
                setattr(
                    test,
                    "setUp",
                    lambda tst=test: tst.skipTest(admin_only_test_msg),
                )

    runner.run(suite)
