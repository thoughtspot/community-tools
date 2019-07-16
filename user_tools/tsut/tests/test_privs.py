import unittest

from tsut.api import SyncUserAndGroups, Privileges, SetGroupPrivilegesAPI
from tsut.model import UsersAndGroups, User, Group, Visibility

TS_URL = "https://tstest"  # Test ThoughtSpot instance.
TS_USER = "tsadmin"
TS_PASSWORD = "admin"


class TestPrivs(unittest.TestCase):
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
        sync.sync_users_and_groups(auag)

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

        privs1 = sgp.get_privileges_for_group("Group 1")
        self.assertTrue(Privileges.CAN_USE_SPOTIQ in privs1)
        privs2 = sgp.get_privileges_for_group("Group 2")
        self.assertTrue(Privileges.CAN_USE_SPOTIQ in privs2)

        sgp.remove_privilege(
            groups=["Group 1"], privilege=Privileges.CAN_USE_SPOTIQ
        )
        privs1 = sgp.get_privileges_for_group("Group 1")
        self.assertFalse(Privileges.CAN_USE_SPOTIQ in privs1)
        privs2 = sgp.get_privileges_for_group("Group 2")
        self.assertTrue(Privileges.CAN_USE_SPOTIQ in privs2)
