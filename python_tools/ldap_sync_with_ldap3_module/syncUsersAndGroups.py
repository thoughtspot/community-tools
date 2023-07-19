#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Script to sync users and groups from LDAP System to TS System."""

import argparse
import datetime
import getpass
import logging
import sys
import time
from collections import defaultdict
from itertools import chain

import ldapApi
import tsApi
from entityClasses import EntityType
from globalClasses import Constants

######################### Helper Classes/Functions ############################


class Argument():
    """Class used to define argument values for reuse."""

    def __init__(self, flag, help_str, action=None, default=None):
        """@param flag: The command line flag.
           @param help_str: Help text to describe what the flag is for.
           @param action: What the presence of flag stores as value.
           @param default: Default value for the flag.
        """
        self.flag = flag
        self.help_str = help_str
        self.action = action
        self.default = default


class ScriptArguments():
    """Argument values are abstracted as static class constants to ensure code
       re-use is possible.
    """

    non_optional_arguments = [
        Argument(
            flag="ts_hostport",
            help_str="Complete URL of TS server in format"
            + ' "http(s)://<host>:<port>"',
        ),
        Argument(
            flag="disable_ssl",
            help_str="Disable SSL authentication to TS server",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="ts_uname", help_str="Login username for ThoughtSpot system"
        ),
        Argument(
            flag="ts_pass", help_str="Login password for ThoughtSpot system"
        ),
        Argument(
            flag="ldap_hostport",
            help_str="Complete URL of server where LDAP server is"
            + ' running in format "ldap(s)://<host>:<port>"',
        ),
        Argument(flag="ldap_uname", help_str="Login username for LDAP system"),
        Argument(flag="ldap_pass", help_str="Login password for LDAP system"),
        Argument(
            flag="sync",
            help_str="Syncs users and groups between LDAP and TS systems",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="purge",
            help_str="Delete entries in ThoughtSpot system that are not"
            + " currently in LDAP tree being synced",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="purge_users",
            help_str="Delete users entries in ThoughtSpot system that are not"
            + " currently in LDAP tree being synced",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="purge_groups",
            help_str="Delete groups entries in ThoughtSpot system that are not"
            + " currently in LDAP tree being synced",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="dry_run",
            help_str="Dry Run to check which users,groups will be added,"
            + "synced, deleted",
            action="store_true",
            default=False,
        ),
    ]
    sync_arguments = [
        Argument(
            flag="basedn",
            help_str="Distinguished name for the base to start"
            + " searching groups in LDAP System",
        ),
        Argument(
            flag="scope",
            help_str="specifies how broad the search context is:\n"
            + "0: BASE- retrieves attributes of the entry specified "
            + "in the search_base \n"
            + "1: LEVEL- retrieves attributes of the entries contained"
            + "in the search_base and one level down. \n"
            + "2: SUBTREE- retrieves attributes of the entries specified"
            + "in the search_base and all levels downward\n"
        ),
        Argument(
            flag="filter_str", help_str="Filter string to apply the search to"
        ),
        Argument(
            flag="include_nontree_members",
            help_str="Include group members even if they do not belong"
            + "to the current sub tree that is being synced.",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="user_identifier",
            help_str="User name identifier key for user creation or sync",
            default="userPrincipalName",
        ),
        Argument(
            flag="authdomain_identifier",
            help_str="Override domain name to be appended to user identifier"
            + "in user name.",
        ),
        Argument(
            flag="email_identifier",
            help_str="Email identifier key for user creation or sync",
            default="mail",
        ),
        Argument(
            flag="user_display_name_identifier",
            help_str="User display name identifier key "
            + "for user creation or sync",
            default="displayName",
        ),
        Argument(
            flag="group_display_name_identifier",
            help_str="Group display name identifier key "
            + "for group creation or sync",
            default="displayName",
        ),
        Argument(
            flag="ldap_type",
            help_str="Ldap type for identifying AD or OpenLdap",
            default="AD",
        ),
        Argument(
            flag="member_str",
            help_str="Member String for AD or OpenLdap",
            default="member"
        ),
        Argument(
            flag="keep_local_membership",
            help_str="Keep memberships of local users and groups "
            + "intact during AD sync.",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="upsert_group",
            help_str="Upsert groups during sync",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="upsert_user",
            help_str="Upsert users during sync",
            action="store_true",
            default=False,
        ),
    ]


def prompt_string(msg):
    """Prompts the user for a value.
       @param msg: Message to display to user.
       @return: User's input or None.
    """
    return input("\n%s: " % msg).strip(" \n") or None


def yes_no(msg):
    """Prompts the user for a yes/no reply.
       @param msg: Message to be displayed to the user.
       @return: Boolean True or False value based on user choice or None.
    """
    choice = input("\n%s (y/n): " % msg)
    if choice == "y":
        return True
    if choice == "n":
        return False
    return None


def fetch_interactively(args_to_fetch):
    """Used to read values of arguments from the user.
       @param args_to_fetch: List of argument objects.
       @return: Read values from the user as a dictionary.
    """
    args = {}
    for item in args_to_fetch:
        if item.action is not None:
            args[item.flag] = yes_no(item.help_str)
        else:
            if item.flag.endswith("_pass"):
                args[item.flag] = getpass.getpass("\n" + item.help_str + ": ")
            else:
                args[item.flag] = prompt_string(item.help_str)
    return args


######################### Core Classes/Functions ##############################


class SyncTree():
    """Class which encapsulates the logic for fetching entities from LDAP
       system and syncing them with ThoughtSpot system.
    """

    NORSN = "Reason not given."

    def __init__(self, user_args):
        """@param arguments: Arguments provided by user."""
        self.dry_run = user_args["dry_run"]
        # Prerequisites for reporting.

        timestamp = datetime.datetime.fromtimestamp(time.time())
        file_name = (
            "sync_report_" + timestamp.strftime("%Y_%m_%d_%H_%M") + ".txt"
        )
        if self.dry_run:
            file_name = ("dry_run_" + file_name)

        self.file_handle = open(file_name, "w")
        self.file_handle.write(
            "============================================\n"
        )
        self.file_handle.write(
            "========== LDAP to TS Sync Report ==========\n"
        )
        self.file_handle.write(
            "============================================\n"
        )
        self.file_handle.write("Terminology :\n")
        self.file_handle.write("created => New entity created in TS System\n")
        self.file_handle.write(
            "synced => Entity already exists in TS System\n"
        )
        self.file_handle.write(
            "============================================\n"
        )

        # LDAP Login.
        logging.info("Attempting login to LDAP system")
        self.ldap_handle = ldapApi.LDAPApiWrapper()
        result = self.ldap_handle.login(
            user_args["ldap_hostport"],
            user_args["ldap_uname"],
            user_args["ldap_pass"],
        )
        if result.status != Constants.OPERATION_SUCCESS:
            reason = (
                str(result.data) if result.data is not None else SyncTree.NORSN
            )
            msg = "Failed to log in to LDAP system. {}\n".format(reason)
            self.file_handle.write(msg)
            self.file_handle.close()
            logging.error(msg)
            return
        logging.info("Successfully logged in to LDAP system.\n")

        # ThoughtSpot Login.
        logging.info("Attempting login to ThoughtSpot system.")
        self.ts_handle = tsApi.TSApiWrapper(user_args["disable_ssl"])
        result = self.ts_handle.login(
            user_args["ts_hostport"],
            user_args["ts_uname"],
            user_args["ts_pass"],
        )
        if result.status != Constants.OPERATION_SUCCESS:
            reason = (
                str(result.data) if result.data is not None else SyncTree.NORSN
            )
            msg = "Failed to log in to ThoughtSpot System. {}\n".format(reason)
            self.file_handle.write(msg)
            self.file_handle.close()
            logging.error(msg)
            return
        logging.info("Successfully logged in to ThoughtSpot system.\n")

        logging.info("Verifying admin privileges of ThoughtSpot login user.")
        if not self.ts_handle.is_admin():
            msg = (
                "User does not have admin privileges to create"
                + "users/groups.\n"
            )
            self.file_handle.write(msg)
            self.file_handle.close()
            logging.error(msg)
            return
        logging.info("Successfully verified admin privileges of "
                     "ThoughtSpot login user.\n")

        # Other important information
        self.basedn = user_args["basedn"]
        self.scope = user_args["scope"]
        if self.scope == "0":
            self.scope = "BASE"
        elif self.scope == "1":
            self.scope = "LEVEL"
        elif self.scope == "2":
            self.scope = "SUBTREE"

        if self.scope and self.scope not in ("BASE", "LEVEL", "SUBTREE"):
            logging.error("Invalid scope. Please use 0, 1, or 2")
            return
        self.filter_str = user_args["filter_str"]
        self.purge = user_args["purge"]
        self.purge_users = user_args["purge_users"]
        self.purge_groups = user_args["purge_groups"]
        self.include_nontree_members = user_args["include_nontree_members"]
        self.user_identifier = user_args["user_identifier"]
        self.authdomain_identifier = user_args["authdomain_identifier"]
        self.email_identifier = user_args["email_identifier"]

        self.user_display_name_identifier = user_args[
            "user_display_name_identifier"]

        self.group_display_name_identifier = user_args[
            "group_display_name_identifier"]

        self.member_str = user_args["member_str"]
        self.ldap_type = user_args["ldap_type"]
        self.keep_local_membership = user_args["keep_local_membership"]
        self.upsert_group = user_args["upsert_group"]
        self.upsert_user = user_args["upsert_user"]
        self.users_to_create = set()
        self.groups_to_create = set()
        self.relationship = set()

        # Create flat list of users and groups to create along with their
        # relationships.
        self.sync_nodes()

        # Update the fetched users, groups and their relationships to
        # ThoughtSpot.
        if self.dry_run:
            self.dryRun()
        else:
            self.update_thoughtspot()


    def add_user_to_create(self, user_dn):
        """Add user with distinguished name to user creation list.
           @param user_dn: User's distinguished name.
        """
        logging.debug(
            "User added to the creation list. User DN: (%s)\n", user_dn
        )
        self.users_to_create.add(user_dn)

    def add_group_to_create(self, group_dn):
        """Add group with distinguished name to group creation list.
           @param group_dn: Group's distinguished name.
        """

        if group_dn in self.groups_to_create:
            logging.debug(
                "Group already exists in the creation list. Group DN: %s",
                group_dn
            )
            return

        self.groups_to_create.add(group_dn)
        logging.debug(
            "Group added to the creation list. Group DN: %s",
            group_dn
        )

        result = self.ldap_handle.dn_to_obj(
            group_dn,
            self.ldap_type,
            self.user_identifier,
            self.email_identifier,
            self.user_display_name_identifier,
            self.group_display_name_identifier,
            self.authdomain_identifier,
            self.member_str,
            log_entities=True)
        if result.status != Constants.OPERATION_SUCCESS or result.data is None:
            logging.debug(
                "Failed to obtain group object for group DN (%s)", group_dn
            )
            return
        group = result.data

        if not group.members:
            logging.debug("Empty group (%s).\n", group_dn)
            self.relationship.add((None, group_dn))
        else:
            logging.debug("Adding members of the group (%s).", group_dn)
            for member_dn in group.members:
                my_type = self.ldap_handle.isOfType(
                    member_dn,
                    self.ldap_type,
                    self.user_identifier,
                    self.email_identifier,
                    self.user_display_name_identifier,
                    self.group_display_name_identifier,
                    self.member_str,
                    self.authdomain_identifier).data

                if my_type == EntityType.USER:
                    logging.debug(
                        "Adding relationship User(%s) to Group(%s)",
                        member_dn,
                        group_dn,
                    )
                    self.relationship.add((member_dn, group_dn))
                    if self.include_nontree_members:
                        logging.debug(
                            "Including non-tree member user (%s)", member_dn
                        )
                        self.add_user_to_create(member_dn)
                elif my_type == EntityType.GROUP:
                    logging.debug(
                        "Adding relationship Group(%s) to Group(%s)",
                        member_dn,
                        group_dn,
                    )
                    self.relationship.add((member_dn, group_dn))
                    if self.include_nontree_members:
                        logging.debug(
                            "Including non-tree member group (%s)", member_dn
                        )
                        self.add_group_to_create(member_dn)
                else:
                    continue

    def sync_nodes(self):
        """Synchronize the nodes between LDAP and TS System."""
        logging.info("Creating flat list of users and groups for syncing.")
        result = self.ldap_handle.list_member_dns(
            self.basedn, self.scope, self.filter_str
        )

        if result.status != Constants.OPERATION_SUCCESS or result.data is None:
            msg = "Failed to retrieve user/group list.\n"
            self.file_handle.write(msg)
            logging.error(msg)
            if result.status == Constants.OPERATION_FAILURE:
                logging.error(result.data)
            return
        if not result.data:
            msg = "No user or group found for the basedn specified.\n"
            self.file_handle.write(msg)
            logging.debug(msg)
            return

        for member_dn in result.data:

            if (member_dn in self.groups_to_create) \
                    or (member_dn in self.users_to_create):
                logging.debug(
                    "Member already exists in the creation list. Member DN: %s",
                    member_dn
                )
                continue
            my_type = self.ldap_handle.isOfType(
                member_dn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.member_str,
                self.authdomain_identifier).data
            logging.debug("member_dn entity type (%s) (%s)", my_type, member_dn)
            if my_type == EntityType.USER:
                self.add_user_to_create(member_dn)
            elif my_type == EntityType.GROUP:
                self.add_group_to_create(member_dn)
            else:
                logging.debug("Unknown entity type (%s)", my_type)
                continue
        logging.info("Successfully created flat list of users and groups.\n")

    def update_thoughtspot(self):
        """Update users and groups to ThoughtSpot."""

        # Maps to maintain.
        dn_to_obj_ldap_map = defaultdict(lambda: None)
        name_to_id_ts_map = defaultdict(lambda: None)
        id_to_name_ts_map = defaultdict(lambda: None)

        ldap_user_names, ldap_group_names = [], []
        ts_user_names, ts_group_names = [], []

        self.file_handle.write("\n===== Addition Phase =====\n\n")

        # Create/Sync all users to ThoughtSpot system.
        users_created, users_synced = 0, 0
        logging.info("Syncing users to ThoughtSpot system.")
        for userdn in self.users_to_create:
            result = self.ldap_handle.dn_to_obj(
                userdn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.authdomain_identifier,
                self.member_str
            )
            if (result.status != Constants.OPERATION_SUCCESS
                    or result.data is None):
                logging.debug(
                    "Failed to obtain user object for user DN (%s)", userdn
                )
                continue
            user = result.data
            dn_to_obj_ldap_map[user.dn] = user
            ldap_user_names.append(user.name)
            prop = {"mail": user.email} if user.email else None

            result = self.ts_handle.sync_user(
                user.name,
                user.display_name,
                tsApi.TSApiWrapper.LDAP_USER,
                None,  # password
                prop,
                None,  # groups
                self.upsert_user
            )
            if result.status == Constants.OPERATION_SUCCESS:
                msg = "User created: {}\n".format(user.name)
                users_created += 1
            elif result.status == Constants.USER_ALREADY_EXISTS:
                msg = "User exists: {}\n".format(user.name)
                users_synced += 1
            else:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else SyncTree.NORSN
                )
                msg = "Failed to create user {}. {}\n".format(
                    user.name, reason
                )
            self.file_handle.write(msg)
        if users_created + users_synced == 0:
            logging.debug("No users to sync to ThoughtSpot system.\n")
        else:
            logging.debug("Users created [%d]\n", users_created)
            logging.debug("Users synced [%d]\n", users_synced)

        # Create/Sync all groups to ThoughtSpot system.
        groups_created, groups_synced = 0, 0
        logging.info("Syncing groups to ThoughtSpot system.")
        for groupdn in self.groups_to_create:
            result = self.ldap_handle.dn_to_obj(
                groupdn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.authdomain_identifier,
                self.member_str)
            if (result.status != Constants.OPERATION_SUCCESS
                    or result.data is None):
                logging.debug(
                    "Failed to obtain group object for group DN (%s)", groupdn
                )
                continue
            group = result.data
            dn_to_obj_ldap_map[group.dn] = group
            ldap_group_names.append(group.name)

            result = self.ts_handle.sync_group(
                group.name, group.display_name, tsApi.TSApiWrapper.LDAP_GROUP,
                None,  # description
                None,  # privileges
                self.upsert_group
            )
            if result.status == Constants.OPERATION_SUCCESS:
                msg = "Group created: {}\n".format(group.name)
                groups_created += 1
            elif result.status == Constants.GROUP_ALREADY_EXISTS:
                msg = "Group exists: {}\n".format(group.name)
                groups_synced += 1
            else:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else SyncTree.NORSN
                )
                msg = "Failed to create group {}. {}\n".format(
                    group.name, reason
                )
            self.file_handle.write(msg)
        if groups_created + groups_synced == 0:
            logging.debug("No group to sync to ThoughtSpot system.\n")
        else:
            logging.debug("Groups created [%d]", groups_created)
            logging.debug("Groups synced [%d]\n", groups_synced)

        domain_name = self.ldap_handle.fetch_domain_name_from_dn(self.basedn)

        # Fetch user info from ThoughtSpot system.
        logging.debug("Fetching current users from ThoughtSpot system in "
                      "domain (%s) including recently created.", domain_name)
        result = self.ts_handle.list_users()
        if result.status == Constants.OPERATION_SUCCESS:
            for user in result.data:
                name_to_id_ts_map[user.name] = user.id
                id_to_name_ts_map[user.id] = user.name
                if user.name.endswith(domain_name):
                    ts_user_names.append(user.name)
            if not ts_user_names:
                logging.debug(
                    "No users fetched from domain (%s).\n", domain_name
                )
            else:
                logging.debug(
                    "Users fetched [%s]: \n%s\n",
                    len(ts_user_names),
                    ",\n".join(ts_user_names),
                )
        else:
            logging.error("Failed to fetch users from ThoughtSpot system.\n")

        # Fetch group info from ThoughtSpot system.
        logging.debug("Fetching current groups from ThoughtSpot system in "
                      "domain (%s) including recently created.", domain_name)
        result = self.ts_handle.list_groups()
        if result.status == Constants.OPERATION_SUCCESS:
            for group in result.data:
                name_to_id_ts_map[group.name] = group.id
                id_to_name_ts_map[group.id] = group.name
                if group.name.endswith(domain_name):
                    ts_group_names.append(group.name)
            if not ts_group_names:
                logging.debug(
                    "No groups fetched from domain (%s).\n", domain_name
                )
            else:
                logging.debug(
                    "Groups fetched [%s]: \n%s\n",
                    len(ts_group_names),
                    ",\n".join(ts_group_names),
                )
        else:
            logging.error("Failed to fetch groups from ThoughtSpot system.\n")

        # Lowercase all the name keys before creating relationships to ensure
        # casing doesn't come into picture during assignment of relations.
        # 1. name_to_id_ts_map
        # 2. ldap_user_names, ldap_group_names
        # 3. ts_user_names, ts_group_names
        name_to_id_ts_map = defaultdict(
            lambda: None,
            [(k.lower(), v) for k, v in name_to_id_ts_map.items()],
        )
        ldap_user_names = [x.lower() for x in ldap_user_names]
        ldap_group_names = [x.lower() for x in ldap_group_names]
        ts_user_names = [x.lower() for x in ts_user_names]
        ts_group_names = [x.lower() for x in ts_group_names]

        # Create relationship map to populate membership.
        parent_id_to_member_user_id_ts_map = defaultdict(lambda: set())
        parent_id_to_member_group_id_ts_map = defaultdict(lambda: set())
        for (child, parent) in self.relationship:
            if child is not None and parent is not None:
                childObj = dn_to_obj_ldap_map[child]
                parentObj = dn_to_obj_ldap_map[parent]
                if childObj is not None and parentObj is not None:
                    childId = name_to_id_ts_map[childObj.name.lower()]
                    parentId = name_to_id_ts_map[parentObj.name.lower()]

                    if not parent_id_to_member_user_id_ts_map[parentId]:
                        parent_id_to_member_user_id_ts_map[parentId] = set()
                    if not parent_id_to_member_group_id_ts_map[parentId]:
                        parent_id_to_member_group_id_ts_map[parentId] = set()

                    if childObj.type == EntityType.USER:
                        parent_id_to_member_user_id_ts_map[parentId].add(
                            childId
                        )
                    elif childObj.type == EntityType.GROUP:
                        parent_id_to_member_group_id_ts_map[parentId].add(
                            childId
                        )
            elif child is None and parent is not None:
                parentObj = dn_to_obj_ldap_map[parent]
                if parentObj is not None:
                    parentId = name_to_id_ts_map[parentObj.name.lower()]
                    parent_id_to_member_user_id_ts_map[parentId] = set()
                    parent_id_to_member_group_id_ts_map[parentId] = set()

        # Create member user relationship in ThoughtSpot system.
        failed_relationships = 0
        logging.info("Creating member user to group relationships.")
        if not parent_id_to_member_user_id_ts_map:
            logging.debug("No member user to group relationship to create.\n")
        else:
            for parent_id in list(parent_id_to_member_user_id_ts_map.keys()):
                result = self.ts_handle.update_users_to_group(
                    list(parent_id_to_member_user_id_ts_map[parent_id]),
                    parent_id,
                    self.keep_local_membership
                )
                if result.status != Constants.OPERATION_SUCCESS:
                    name = id_to_name_ts_map[parent_id]
                    reason = (
                        str(result.data)
                        if result.data is not None
                        else SyncTree.NORSN
                    )
                    msg = "Failed to update member users to group {} {}\n"
                    msg = msg.format(name, reason)
                    self.file_handle.write(msg)
                    logging.error(msg)
                    failed_relationships += 1
            if failed_relationships == 0:
                logging.debug(
                    "Done creating member users to group relationships.\n"
                )
            else:
                logging.error(
                    "One or more member users to group relationship(s)"
                    " could not be created.\n")

        # Create member group relationship in ThoughtSpot system.
        failed_relationships = 0
        logging.debug("Creating member group to group relationships.")
        if not parent_id_to_member_group_id_ts_map:
            logging.debug("No member group to group relationship to create.\n")
        else:
            for parent_id in list(parent_id_to_member_group_id_ts_map.keys()):
                self.ts_handle.update_groups_to_group(
                    list(parent_id_to_member_group_id_ts_map[parent_id]),
                    parent_id,
                    self.keep_local_membership
                )
                if result.status != Constants.OPERATION_SUCCESS:
                    name = id_to_name_ts_map[parent_id]
                    reason = (
                        str(result.data)
                        if result.data is not None
                        else SyncTree.NORSN
                    )
                    msg = "Failed to update member groups to group {} {}\n"
                    msg = msg.format(name, reason)
                    self.file_handle.write(msg)
                    logging.error(msg)
                    failed_relationships += 1

            if failed_relationships == 0:
                logging.debug(
                    "Done creating member groups to group relationships.\n"
                )
            else:
                logging.error(
                    "One or more member groups to group relationship(s)"
                    " could not be created.\n")

        # Delete others
        if self.purge or self.purge_users:
            self.file_handle.write("\n===== User Deletion Phase =====\n\n")
            logging.info("Deleting users not in current sync path.")
            users_to_delete = []
            for user_name in set(ts_user_names) - set(ldap_user_names):
                if name_to_id_ts_map[user_name]:
                    users_to_delete.append(name_to_id_ts_map[user_name])
                    msg = "Deleting user: {}\n".format(user_name)
                    self.file_handle.write(msg)
            result = self.ts_handle.delete_users(users_to_delete)
            users_deleted = len(users_to_delete)
            if result.status != Constants.OPERATION_SUCCESS:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else SyncTree.NORSN
                )
                msg = "Failed to delete users with ids {} {}\n".format(
                    users_to_delete, reason
                )
                self.file_handle.write(msg)
                logging.debug(msg)
                users_deleted = 0
            elif users_deleted == 0:
                logging.debug("No users to delete.\n")
            else:
                logging.debug(
                    "Users deleted [%s]:\n%s\n",
                    len(users_to_delete),
                    ",\n".join(
                        id_to_name_ts_map[uid] for uid in users_to_delete
                    ),
                )

        if self.purge or self.purge_groups:
            self.file_handle.write("\n===== Group Deletion Phase =====\n\n")
            logging.info("Deleting groups not in current sync path.")
            groups_to_delete = []
            for group_name in set(ts_group_names) - set(ldap_group_names):
                if name_to_id_ts_map[group_name]:
                    groups_to_delete.append(name_to_id_ts_map[group_name])
                    msg = "Deleting group: {}\n".format(group_name)
                    self.file_handle.write(msg)
            result = self.ts_handle.delete_groups(groups_to_delete)
            groups_deleted = len(groups_to_delete)
            if result.status != Constants.OPERATION_SUCCESS:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else SyncTree.NORSN
                )
                msg = "Failed to delete groups with ids {} {}\n".format(
                    groups_to_delete, reason
                )
                self.file_handle.write(msg)
                logging.debug(msg)
                groups_deleted = 0
            elif groups_deleted == 0:
                logging.debug("No groups to delete.\n")
            else:
                logging.debug(
                    "Groups deleted [%s]:\n%s\n",
                    len(groups_to_delete),
                    ",\n".join(
                        id_to_name_ts_map[gid] for gid in groups_to_delete
                    ),
                )

        # Summary Reporting.
        self.file_handle.write("\n========= Summary ========\n\n")
        self.file_handle.write("Users created: {}\n".format(users_created))
        self.file_handle.write("Groups created: {}\n".format(groups_created))
        self.file_handle.write("Users synced: {}\n".format(users_synced))
        self.file_handle.write("Groups synced: {}\n".format(groups_synced))
        if self.purge or self.purge_users:
            self.file_handle.write("Users deleted: {}\n".format(users_deleted))
        elif self.purge or self.purge_groups:
            self.file_handle.write(
                "Groups deleted: {}\n".format(groups_deleted)
            )
        self.file_handle.close()

        # Summary to debug log
        logging.debug("Users created: %s", users_created)
        logging.debug("Groups created: %s", groups_created)
        logging.debug("Users synced: %s", users_synced)
        logging.debug("Groups synced: %s", groups_synced)
        if self.purge or self.purge_users:
            logging.debug("Users deleted: %s", users_deleted)
        elif self.purge or self.purge_groups:
            logging.debug("Groups deleted: %s", groups_deleted)

        print("Refer to {} for details.".format(self.file_handle.name))


    def dryRun(self):
        """Perform dry run and report the users/groups
        that will be added/synced/deleted to/from TS
        """

        ldap_user_names, ldap_group_names = [], []
        ts_user_names, ts_group_names = [], []
        ts_user_names_domin, ts_group_names_domin = [], []

        self.file_handle.write("\n===== Dry Run =====\n\n")

        domain_name = self.ldap_handle.fetch_domain_name_from_dn(self.basedn)

        logging.info("Syncing users to ThoughtSpot system.")
        for userdn in self.users_to_create:
            result = self.ldap_handle.dn_to_obj(
                userdn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.authdomain_identifier,
                self.member_str
            )
            if (result.status != Constants.OPERATION_SUCCESS
                    or result.data is None):
                logging.debug(
                    "Failed to obtain user object for user DN (%s)", userdn
                )
                continue
            user = result.data
            ldap_user_names.append(user.name.lower())

        result = self.ts_handle.list_users()

        if result.status == Constants.OPERATION_SUCCESS:
            for user in result.data:
                ts_user_names.append(user.name.lower())
                if user.name.endswith(domain_name):
                    ts_user_names_domin.append(user.name.lower())
            if not ts_user_names:
                logging.debug(
                    "No users fetched from thoughtspot")
            else:
                logging.debug(
                    "Users fetched [%s]: \n%s\n",
                    len(ts_user_names),
                    ",\n".join(ts_user_names),
                )
        else:
            logging.error("Failed to fetch users from ThoughtSpot system.\n")

        users_to_create = list(set(ldap_user_names) - set(ts_user_names))

        self.file_handle.write("\n\nUsers Created: \n\n\n {}\n"
        .format(users_to_create))

        users_to_sync = list(set(ldap_user_names) - set(users_to_create))

        self.file_handle.write("\n\nUsers Sync: \n\n\n {}\n"
        .format(users_to_sync))

        logging.info("Syncing groups to ThoughtSpot system.")
        for groupdn in self.groups_to_create:
            result = self.ldap_handle.dn_to_obj(
                groupdn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.authdomain_identifier,
                self.member_str)
            if (result.status != Constants.OPERATION_SUCCESS
                    or result.data is None):
                logging.debug(
                    "Failed to obtain group object for group DN (%s)", groupdn
                )
                continue
            group = result.data
            ldap_group_names.append(group.name.lower())

        result = self.ts_handle.list_groups()

        if result.status == Constants.OPERATION_SUCCESS:
            for group in result.data:
                ts_group_names.append(group.name.lower())
                if group.name.endswith(domain_name):
                    ts_group_names_domin.append(group.name.lower())
            if not ts_group_names:
                logging.debug(
                    "No groups fetched from thoughtspot")
            else:
                logging.debug(
                    "Groups fetched [%s]: \n%s\n",
                    len(ts_group_names),
                    ",\n".join(ts_group_names),
                )
        else:
            logging.error("Failed to fetch groups from ThoughtSpot system.\n")

        group_to_create = list(set(ldap_group_names) - set(ts_group_names))

        self.file_handle.write("\n\nGroup Created: \n\n\n {}\n"
        .format(group_to_create))

        groups_to_sync = list(set(ldap_group_names) - set(group_to_create))

        self.file_handle.write("\n\nGroup Sync: \n\n\n {}\n"
        .format(groups_to_sync))

        if self.purge or self.purge_users:
            self.file_handle.write("\n===== User Deletion Phase =====\n\n")
            logging.info("Deleting users not in current sync path.")
            users_to_delete = list(set(ts_user_names_domin)
            .union(set(users_to_create)) - set(ldap_user_names))

            self.file_handle.write("\n\nUsers Deleted: \n\n\n {}\n"
            .format(users_to_delete))

        if self.purge or self.purge_groups:
            self.file_handle.write("\n===== Group Deletion Phase =====\n\n")
            logging.info("Deleting groups not in current sync path.")
            groups_to_delete = list(set(ts_group_names_domin)
            .union(set(group_to_create)) - set(ldap_group_names))

            self.file_handle.write("\n\nGroup Deleted: \n\n\n {}\n"
            .format(groups_to_delete))

        print("Refer to {} for details.".format(self.file_handle.name))

def main(non_optional_args):
    """Function to act as starting point to all other calls needed to sync.
       @param arguments: Arguments provided by the user of the script.
    """
    if non_optional_args["sync"]:
        # If in interactive mode fetch other required arguments from the user.
        if non_optional_args["subparser_name"] == "interactive":
            sync_strs = fetch_interactively(ScriptArguments.sync_arguments)
            non_optional_args.update(sync_strs)

        if non_optional_args["basedn"] is None:
            logging.error("Basedn value cannot be left empty for sync.")
            sys.exit(1)

        if non_optional_args["purge"] and non_optional_args["purge_users"]:
            error = "purge and purge_users flags cannot be set simultaneously"
            logging.error(error)
            sys.exit(1)

        if non_optional_args["purge"] and non_optional_args["purge_groups"]:
            error = "purge and purge_groups flags cannot be set simultaneously"
            logging.error(error)
            sys.exit(1)

        SyncTree(non_optional_args)
    else:
        # If sync flag is unset/false, we do nothing.
        logging.debug("Sync parameter is not set. Exiting.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="subparser_name", help="Modes the script can be run in."
    )
    interactive = subparsers.add_parser(
        "interactive",
        help="Takes user through series of steps to fetch all required values.",
    )
    script = subparsers.add_parser(
        "script", help="Takes all the required values as command line flags."
    )

    for arg in chain(ScriptArguments.non_optional_arguments,
                     ScriptArguments.sync_arguments):
        script.add_argument(
            "--" + arg.flag,
            help=arg.help_str,
            action=arg.action,
            default=arg.default,
        )
    script.add_argument(
        "--debug", action="store_true", default=False, help=argparse.SUPPRESS
    )

    arguments = vars(parser.parse_args())
    if arguments["subparser_name"] == "interactive":
        arg_strs = fetch_interactively(ScriptArguments.non_optional_arguments)
        arguments.update(arg_strs)

    if "debug" in arguments and arguments["debug"]:
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')

    # If any of the non_optional_arguments are left empty we need to quit.
    if None in [arguments[arg.flag] for arg
                in ScriptArguments.non_optional_arguments]:
        logging.error("One or more non-optional parameters are left empty.")
        sys.exit(1)

    main(arguments)
