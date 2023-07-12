#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2023
# Author: Indresh Gupta (indresh.gupta@thoughtspot.com)
"""Script to sync users, groups and orgs from LDAP System to TS System."""

from collections import defaultdict
from itertools import chain
import json
import logging
import sys
from entityClasses import EntityType
from globalClasses import Constants
import syncUsersAndGroups
import orgAwareUsersAndGroupsSyncUtil

######################### Core Classes/Functions ##############################

# pylint: disable=R0903, R0902, R0912, R0915, R1702, C0302, W0108
class OrgAwareSyncTree(syncUsersAndGroups.SyncTree):
    """Class which encapsulates the logic for fetching entities from LDAP
       system and syncing them with ThoughtSpot system.
    """
    def __init__(self, user_args):
        """@param arguments: Arguments provided by user."""
        self.orgs_to_create = set()
        self.org_mapping = user_args["org_mapping"]
        self.org_file_input = user_args["org_file_input"]
        self.org_attr = user_args["org_attr"]
        self.add_recursive_org_membership = \
            user_args["add_recursive_org_membership"]
        self.remove_user_orgs = user_args["remove_user_orgs"]
        self.remove_group_orgs = user_args["remove_group_orgs"]
        self.org_map = defaultdict(lambda: set())
        self.unmapped_org_obj = []
        self.util = orgAwareUsersAndGroupsSyncUtil
        super().__init__(user_args)

    def add_user_to_create(self, user_dn):
        """Add user with distinguished name to user creation list
           and fill out it's org mapping.
           @param user_dn: User's distinguished name.
        """
        logging.debug(
            "User added to the creation list. User DN: (%s)\n", user_dn
        )
        self.users_to_create.add(user_dn)

    def add_group_to_create(self, group_dn):
        """Add group with distinguished name to group creation list
           and fill out it's org mapping.
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
                if self.add_recursive_org_membership \
                        and group_dn in self.org_map:
                    self.org_map[member_dn].update(self.org_map[group_dn])

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
        group_dns, user_dns = [], []
        for member_dn in result.data:
            dn_type = self.ldap_handle.isOfType(
                member_dn,
                self.ldap_type,
                self.user_identifier,
                self.email_identifier,
                self.user_display_name_identifier,
                self.group_display_name_identifier,
                self.member_str,
                self.authdomain_identifier).data
            logging.debug("member_dn entity type (%s) (%s)", dn_type,
                          member_dn)
            if dn_type == EntityType.USER:
                user_dns.append(member_dn)
            elif dn_type == EntityType.GROUP:
                group_dns.append(member_dn)
            else:
                logging.debug("Unknown entity type (%s)", dn_type)
                continue

        logging.info("Processing org mapping")
        # Fill out org mapping for users and groups
        self.process_org_mapping(group_dns, user_dns)

        logging.info("Running validation on the derived org mapping")
        # Run validation on the derived org mapping
        self.validate_org_assignment(group_dns, user_dns)

        logging.info("Successfully created flat list of "
                     "users, groups and orgs.\n")

    def populate_org_from_file(self):
        """
        Populated org mapping from the given input file
        """
        logging.info("Reading Input from the %s file",
                     self.org_file_input)
        try:
            with open(self.org_file_input) as file:
                parsed_json = json.load(file)
            for json_obj in parsed_json:
                obj_dn = json_obj["dn"]
                org_list = json_obj["orgs"]
                self.orgs_to_create.update(org_list)
                self.org_map[obj_dn].update(org_list)
        except Exception as e:
            reason = str(e)
            msg = "Please check the input org mapping " \
                  "file {}.\n".format(reason)
            logging.error(msg)
            self.error_file.write(msg)
            self.file_handle.write(msg)
            sys.exit(1)

    def populate_org_from_attr(self, obj_dns):
        """
        Populated org mapping from object attribute
        """
        for obj_dn in obj_dns:
            result = self.ldap_handle.dn_to_obj(
                obj_dn,
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
                    "Failed to obtain object for DN (%s)",
                    obj_dn
                )
                continue
            group = result.data
            try:
                if group.orgs is not None:
                    self.orgs_to_create.update(group.orgs)
                    self.org_map[obj_dn].update(group.orgs)
            except Exception as e:
                reason = str(e)
                msg = "Please check Entity's org property at " \
                      "ldap server {}.\n".format(reason)
                logging.error(msg)
                self.error_file.write(msg)
                self.file_handle.write(msg)
                sys.exit(1)


    def process_org_mapping(self, group_dns, user_dns):
        """
        Method that process org mapping provided as input file or
        object attribute and then recursively assigns the orgs to
        object's child members
        """
        if self.org_file_input:
            self.populate_org_from_file()

        if self.org_attr:
            self.populate_org_from_attr(group_dns)
            self.populate_org_from_attr(user_dns)

        for group_dn in group_dns:
            self.add_group_to_create(group_dn)
        for user_dn in user_dns:
            self.add_user_to_create(user_dn)

    def validate_org_assignment(self, group_dns, user_dns):
        """
        Method which runs validation on the derived org mapping
        """
        # logging objects whose org mapping could not be identified
        for member_dn in chain(group_dns, user_dns):
            if member_dn not in self.org_map:
                self.unmapped_org_obj.append(member_dn)
        if len(self.unmapped_org_obj) >= 1:
            self.error_file.write("\nOrg mapping could not be found "
                                  "for the following objects:\n\n")
            self.error_file.writelines("{}\n".format(obj)
                                       for obj in self.unmapped_org_obj)

        org_conflict = 0
        for (child, parent) in self.relationship:
            if child is None:
                continue
            parent_orgs = self.org_map[parent]
            member_orgs = self.org_map[child]
            if len(member_orgs) < 1:
                continue
            for parent_org in parent_orgs:
                if parent_org not in member_orgs:
                    org_conflict = 1
                    reason = "{} child doesn't exists in parent's " \
                             "{} org".format(child, parent_org)
                    msg = ("\nOrg mapping mismatch for child {} "
                    "and parent {} \n.{}\n".format(str(child), str(parent),
                                                   reason))
                    logging.error(msg)
                    self.error_file.write(msg)

        if org_conflict == 1:
            msg = "ERROR: Org mapping conflict found. \n" \
                  "One or more child-parent pair do not belong to same orgs" \
                  "Please check {} file for more info".format(
                self.error_file.name)
            logging.error(msg)
            self.error_file.write(msg)
            self.file_handle.write(msg)
            sys.exit(1)

    def switch_org(self, org_id):
        """
        Method to switch context to given org
        @param org_id: orgId to switch
        """
        result = self.ts_handle.switch_org(int(org_id))
        if result.status != Constants.OPERATION_SUCCESS:
            reason = (
                str(result.data)
                if result.data is not None
                else super().NORSN
            )
            msg = "\nFailed to switch to {} org. {}\n" \
                .format(org_id, reason)
            logging.error(msg)
            self.error_file.write(msg)
            self.file_handle.write(msg)
            sys.exit(1)

    def update_thoughtspot(self):
        """Update users and groups to ThoughtSpot."""

        # Maps to maintain.
        org_name_to_org_id = defaultdict(lambda: None)
        org_id_to_org_name = defaultdict(lambda: None)
        dn_to_obj_ldap_map = defaultdict(lambda: None)
        user_name_to_id_ts_map = defaultdict(lambda: None)
        user_id_to_name_ts_map = defaultdict(lambda: None)
        group_name_to_id_ts_map = defaultdict(lambda: None)
        group_id_to_name_ts_map = defaultdict(lambda: None)
        ts_group_name_to_org = defaultdict(lambda: set())
        ts_user_name_to_org = defaultdict(lambda: set())
        ldap_user_name_to_org = defaultdict(lambda: set())
        ldap_group_name_to_org = defaultdict(lambda: set())

        ldap_user_names, ldap_group_names = [], []
        ts_user_names, ts_group_names = set(), set()
        domain_name = \
            self.ldap_handle.fetch_domain_name_from_dn(self.basedn)

        self.file_handle.write("\n===== Addition Phase =====\n\n")

        # Sync orgs to TS
        org_created, org_already_exist = [0], [0]
        self.util.sync_orgs(
            self,
            org_created,
            org_already_exist
        )

        # Fetch org list from TS and populates:
        # 1. org id to name mapping
        # 2. org name to id mapping
        self.util.fetch_ts_org_list(
            self,
            org_name_to_org_id,
            org_id_to_org_name
        )

        # Create/Sync all users to TS and populates:
        # 1. ldap_user_names
        # 2. orgId list for ldap users
        users_created, users_synced = [0], [0]
        self.util.sync_users(
            self,
            dn_to_obj_ldap_map,
            ldap_user_name_to_org,
            org_name_to_org_id,
            ldap_user_names,
            users_created,
            users_synced)

        # Create/Sync all groups to TS and populates:
        # 1. ldap_group_names
        # 2. ldap_group_name_to_org - orgId list for ldap groups
        # 3. No. of groups created/synced in each org
        groups_created, groups_synced = \
            defaultdict(lambda: 0), defaultdict(lambda: 0)
        self.util.sync_groups(
            self,
            dn_to_obj_ldap_map,
            ldap_group_name_to_org,
            org_name_to_org_id,
            ldap_group_names,
            org_id_to_org_name,
            groups_created,
            groups_synced
        )

        # Fetch user info from TS and populates:
        # 1. user_name_to_id_ts_map
        # 2. user_id_to_name_ts_map
        # 3. ts_user_names
        # 4. ts_user_name_to_org - orgId list for ts users
        self.util.fetch_ts_user_list(
            self,
            domain_name,
            user_name_to_id_ts_map,
            user_id_to_name_ts_map,
            ts_user_names,
            ts_user_name_to_org
        )

        # Fetch group info from TS and populates:
        # 1. group_name_to_id_ts_map
        # 2. group_id_to_name_ts_map
        # 3. ts_group_names
        # 4. ts_group_name_to_org - orgId list for ts groups
        self.util.fetch_ts_group_list(
            self,
            domain_name,
            group_name_to_id_ts_map,
            group_id_to_name_ts_map,
            ts_group_names,
            ts_group_name_to_org
        )

        # Lowercase all the name keys before creating relationships to ensure
        # casing doesn't come into picture during assignment of relations.
        # 1. user_name_to_id_ts_map
        # 2. group_name_to_id_ts_map
        # 3. ldap_user_names, ldap_group_names
        # 4. ts_user_names, ts_group_names
        # 5. ldap_group_name_to_org, ldap_user_name_to_org
        # 6. ts_group_name_to_org, ts_user_name_to_org
        user_name_to_id_ts_map = defaultdict(
            lambda: None,
            [(k.lower(), v) for k, v in user_name_to_id_ts_map.items()],
        )
        group_name_to_id_ts_map = defaultdict(
            lambda: None,
            [(tuple(element.lower() if
                    isinstance(element, str) else element for element in k)
              , v) for k, v in group_name_to_id_ts_map.items()],
        )
        ldap_user_names = [x.lower() for x in ldap_user_names]
        ts_user_names = [x.lower() for x in ts_user_names]
        ts_group_names = [x.lower() for x in ts_group_names]
        ldap_group_name_to_org = defaultdict(
            lambda: set(),
            [(k.lower(), v) for k, v in ldap_group_name_to_org.items()],
        )
        ldap_user_name_to_org = defaultdict(
            lambda: set(),
            [(k.lower(), v) for k, v in ldap_user_name_to_org.items()],
        )
        ts_group_name_to_org = defaultdict(
            lambda: set(),
            [(k.lower(), v) for k, v in ts_group_name_to_org.items()],
        )
        ts_user_name_to_org = defaultdict(
            lambda: set(),
            [(k.lower(), v) for k, v in ts_user_name_to_org.items()],
        )

        # Create relationship map to populate membership.
        parent_id_to_member_user_id_ts_map = defaultdict(lambda: set())
        parent_id_to_member_group_id_ts_map = defaultdict(lambda: set())
        parent_id_to_org_map = defaultdict(lambda: None)
        self.util.populate_rltn_maps(
            self,
            dn_to_obj_ldap_map,
            group_name_to_id_ts_map,
            org_name_to_org_id,
            parent_id_to_member_user_id_ts_map,
            parent_id_to_member_group_id_ts_map,
            ldap_user_name_to_org,
            user_name_to_id_ts_map,
            ldap_group_name_to_org,
            parent_id_to_org_map
        )

        # Create member user relationship in ThoughtSpot system.
        self.util.create_member_user_rltn(
            self,
            parent_id_to_member_user_id_ts_map,
            parent_id_to_org_map,
            group_id_to_name_ts_map
        )

        # Create member group relationship in ThoughtSpot system.
        self.util.create_member_group_rltn(
            self,
            parent_id_to_member_group_id_ts_map,
            parent_id_to_org_map,
            group_id_to_name_ts_map
        )

        # Delete others
        users_deleted, groups_deleted = [0], [0]
        users_org_removed, groups_org_removed = \
            defaultdict(lambda: set()), defaultdict(lambda: set())

        # Group Deletion
        # Deletes groups which are not present in current sync or
        # groups for whom org list is empty
        if self.purge or self.purge_groups:
            self.util.delete_groups(
                self,
                ts_group_names,
                ldap_group_name_to_org,
                ts_group_name_to_org,
                group_name_to_id_ts_map,
                org_id_to_org_name,
                group_id_to_name_ts_map,
                groups_deleted
            )

        # Group Org Removal
        if self.remove_group_orgs:
            self.util.remove_groups_from_orgs(
                self,
                ts_group_names,
                ldap_group_name_to_org,
                ts_group_name_to_org,
                group_name_to_id_ts_map,
                org_id_to_org_name,
                groups_org_removed
            )


        # User deletion
        # Deletes users which are not present in current sync or
        # users for whom org list is empty
        if self.purge_users or self.purge:
            self.util.delete_users(
                self,
                ts_user_names,
                ldap_user_name_to_org,
                user_name_to_id_ts_map,
                users_deleted,
                user_id_to_name_ts_map
            )

        # User Org Removal
        if self.remove_user_orgs:
            self.util.remove_users_from_orgs(
                self,
                ts_user_names,
                ts_user_name_to_org,
                ldap_user_name_to_org,
                org_id_to_org_name,
                users_org_removed
            )

        # Summary Reporting.
        self.file_handle.write("\n========= Summary ========\n\n")
        self.file_handle.write("Orgs created: {}\n".format(
            org_created[0]))
        self.file_handle.write("Orgs Already Exist: {}\n".format(
            org_already_exist[0]))

        self.file_handle.write("Users created: {}\n".format(users_created[0]))
        self.file_handle.write("Users synced: {}\n".format(users_synced[0]))

        for org_name in set(groups_created.keys()).union(groups_synced.keys()):
            if groups_created[org_name] + groups_synced[org_name] == 0:
                self.file_handle.write("No group to sync in {} org.\n"
                                       .format(org_name))
            else:
                self.file_handle.write("{} Groups created in {} org\n".format(
                              groups_created[org_name], org_name))
                self.file_handle.write("{} Groups synced in {} org\n".format(
                    groups_synced[org_name], org_name))

        if self.purge or self.purge_users:
            self.file_handle.write("Users deleted: {}\n".format(
                users_deleted[0]))

        if self.remove_user_orgs:
            for user in list(users_org_removed.keys()):
                self.file_handle.write("Removed {} User from {} Orgs\n".format(
                              user, len(users_org_removed[user])))

        if self.purge or self.purge_groups:
            self.file_handle.write(
                "Groups deleted: {}\n".format(groups_deleted[0])
            )

        if self.remove_group_orgs:
            for group in list(groups_org_removed.keys()):
                if len(groups_org_removed[group]) > 0:
                    self.file_handle.write("Removed {} Group from {} Orgs\n"
                    .format(group, len(groups_org_removed[group])))
        self.file_handle.close()
        self.error_file.close()

        # Summary to debug log
        logging.debug("Orgs created: %s", org_created[0])
        logging.debug("Orgs already exist: %s", org_already_exist[0])
        logging.debug("Users created: %s", users_created[0])
        logging.debug("Users synced: %s", users_synced[0])
        for org_name in set(groups_created.keys()).union(groups_synced.keys()):
            if groups_created[org_name] + groups_synced[org_name] == 0:
                logging.debug("No group to sync in %s org.\n", org_name)
            else:
                logging.debug("Groups created [%d] in %s org\n",
                              groups_created[org_name], org_name)
                logging.debug("Groups synced [%d] in %s org\n",
                              groups_synced[org_name], org_name)

        if self.purge or self.purge_users:
            logging.debug("Users deleted: %s", users_deleted[0])
        if self.remove_user_orgs:
            for user in list(users_org_removed.keys()):
                logging.debug("Removed %s User from %s Orgs\n",
                              user, len(users_org_removed[user]))
        if self.purge or self.purge_groups:
            logging.debug("Groups deleted: %s", groups_deleted[0])
        if self.remove_group_orgs:
            for group in list(groups_org_removed.keys()):
                logging.debug("Removed %s group from %s Orgs\n",
                              group, len(groups_org_removed[group]))

        print("Refer to {} for ldap report and {} for error logs.".format(
            self.file_handle.name, self.error_file.name))
        if len(self.unmapped_org_obj) > 0:
            logging.error("Org mapping of one or more objects could "
                         "not be found.")
            sys.exit(1)

    def dryRun(self):
        """Perform dry run and report the users/groups that
        will be added/synced/deleted to/from TS and individual orgs
        """

        ldap_user_names, ldap_group_names = [], []
        ts_user_names, ts_group_names, ts_org_names = [], set(), []
        ts_user_names_domin, ts_group_names_domin = set(), set()
        org_id_to_org_name = defaultdict(lambda: None)
        org_name_to_org_id = defaultdict(lambda: None)
        ldap_user_name_orgs = defaultdict(lambda: set())
        ts_user_name_orgs = defaultdict(lambda: set())
        ldap_group_name_orgs = defaultdict(lambda: set())
        ts_group_name_orgs = defaultdict(lambda: set())
        unmapped_org_objects = []

        domain_name = \
            self.ldap_handle.fetch_domain_name_from_dn(self.basedn)

        self.file_handle.write("\n===== Dry Run =====\n\n")

        # Orgs to be created/ Orgs already exist
        logging.info("Syncing Orgs in ThoughtSpot system")
        self.switch_org(Constants.ALL_ORG_ID)
        result = self.ts_handle.list_orgs()
        if result.status == Constants.OPERATION_SUCCESS:
            for org in result.data:
                ts_org_names.append(org.name)
                org_id_to_org_name[org.id] = org.name
                org_name_to_org_id[org.name] = org.id
        else:
            reason = (
                str(result.data)
                if result.data is not None
                else super().NORSN
            )
            msg = "\nFailed to fetch orgs from ThoughtSpot system. " \
                  "{}\n".format(reason)
            logging.error(msg)
            self.error_file.write(msg)

        orgs_to_create = list(set(self.orgs_to_create) - set(ts_org_names))
        self.file_handle.write("\nOrgs Created: \n {}\n"
                               .format(orgs_to_create))

        existing_orgs = list(set(self.orgs_to_create) - set(orgs_to_create))
        self.file_handle.write("\nExisting Orgs: \n {}\n\n"
                               .format(existing_orgs))

        # Users to create/ Users to sync
        logging.info("Syncing users to ThoughtSpot system.")
        for user_dn in self.users_to_create:
            result = self.ldap_handle.dn_to_obj(
                user_dn,
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
                    "Failed to obtain user object for user DN (%s)", user_dn
                )
                continue
            user = result.data
            ldap_user_names.append(user.name.lower())
            if len(self.org_map[user_dn]) < 1:
                unmapped_org_objects.append(user)
            ldap_user_name_orgs[user.name.lower()]\
                .update(self.org_map[user_dn])

        self.switch_org(Constants.ALL_ORG_ID)
        result = self.ts_handle.list_users()
        if result.status == Constants.OPERATION_SUCCESS:
            for user in result.data:
                ts_user_names.append(user.name.lower())
                ts_user_name_orgs[user.name.lower()]\
                    .update([org_id_to_org_name[id]
                             for id in user.orgIds])
                if user.name.endswith(domain_name):
                    ts_user_names_domin.add(user.name.lower())
        else:
            logging.error("Failed to fetch users from "
                          "ThoughtSpot system.\n")

        users_to_create = \
            list(set(ldap_user_names) - set(ts_user_names))
        for user_name in users_to_create:
            if len(ldap_user_name_orgs[user_name]) < 1:
                msg = "\nFailed to Create {} User. " \
                      "User doesn't have any specified org\n".format(user_name)
                self.error_file.write(msg)
            else:
                msg = "\n{} User Created in {} Orgs \n"\
                    .format(user_name, list(ldap_user_name_orgs[user_name]))
            self.file_handle.write(msg)

        users_to_sync = list(set(ldap_user_names) - set(users_to_create))
        for user_name in users_to_sync:
            if len(ldap_user_name_orgs[user_name]) < 1:
                msg = "\nFailed to Sync {} User. " \
                      "User doesn't have any specified org\n".format(user_name)
                self.error_file.write(msg)
            else:
                msg = "\n{} User Synced\n".format(user_name)
            self.file_handle.write(msg)

        # Groups to create/ Groups to sync
        logging.info("Syncing groups to ThoughtSpot system.")
        for group_dn in self.groups_to_create:
            result = self.ldap_handle.dn_to_obj(
                group_dn,
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
                    "Failed to obtain group object for group DN (%s)", group_dn
                )
                continue
            group = result.data
            ldap_group_names.append(group.name.lower())
            if len(self.org_map[group_dn]) < 1:
                unmapped_org_objects.append(group)
            ldap_group_name_orgs[group.name.lower()]\
                .update(self.org_map[group_dn])

        self.switch_org(Constants.ALL_ORG_ID)
        result = self.ts_handle.list_groups()

        if result.status == Constants.OPERATION_SUCCESS:
            for group in result.data:
                ts_group_names.add(group.name.lower())
                ts_group_name_orgs[group.name.lower()]\
                    .update([org_id_to_org_name[id]
                             for id in group.orgIds])
                if group.name.endswith(domain_name):
                    ts_group_names_domin.add(group.name.lower())
        else:
            logging.error("Failed to fetch groups from ThoughtSpot system.\n")

        group_to_create = list(set(ldap_group_names) - set(ts_group_names))
        for group_name in group_to_create:
            if len(ldap_group_name_orgs[group_name]) < 1:
                msg = "\nFailed to Create {} Group." \
                " Group doesn't have any specified org\n".format(group_name)
                self.error_file.write(msg)
            else:
                msg = "\n{} Group Created in {} Orgs \n"\
                    .format(group_name,
                            list(ldap_group_name_orgs[group_name]))
            self.file_handle.write(msg)

        groups_to_sync = list(set(ldap_group_names) - set(group_to_create))
        for group_name in groups_to_sync:
            if len(ldap_group_name_orgs[group_name]) < 1:
                msg = "\nFailed to Sync {} Group." \
                " Group doesn't have any specified org\n".format(group_name)
                self.error_file.write(msg)
            else:
                msg = "\n{} Group Synced\n"\
                    .format(group_name)
            self.file_handle.write(msg)

        # Delete Groups not in the present sync or groups whose org list
        # is empty
        if self.purge or self.purge_groups:
            self.file_handle.write("\n===== Group Deletion Phase =====\n\n")
            logging.info("Deleting groups not in current sync path.")
            groups_to_delete = set()
            for group_name in ts_group_names_domin:
                if len(ldap_group_name_orgs[group_name]) < 1:
                    groups_to_delete.add(group_name)
            if len(groups_to_delete) < 1:
                self.file_handle.write("\nNo Groups to be Deleted \n")
            else:
                self.file_handle.write("\nGroup Deleted: {}\n"
                                       .format(list(groups_to_delete)))

        # Remove Groups from orgs which are not there in present sync
        if self.remove_group_orgs:
            group_org_removal = 0
            self.file_handle.write("\n===== Group Org Removal Phase =====\n\n")
            logging.info("Removing groups from Orgs not in current sync path.")
            for group_name in ts_group_names_domin:
                if len(ldap_group_name_orgs[group_name]) < 1:
                    continue
                if ts_group_name_orgs[group_name] \
                    .issubset(ldap_group_name_orgs[group_name]):
                    continue
                group_org_removal = 1
                group_delete_orgs = list(set(ts_group_name_orgs[group_name])
                                    - set(ldap_group_name_orgs[group_name]))
                self.file_handle.write("\n {} Group Removed from {} "
                                       "Orgs: \n".format(group_name,
                                                         group_delete_orgs))
            if group_org_removal == 0:
                self.file_handle.write("\nNo Group to be removed from "
                                       "any org\n")


        # Delete User not in the present sync or users whose org list
        # is empty
        if self.purge or self.purge_users:
            self.file_handle.write("\n===== User Deletion Phase =====\n\n")
            logging.info("Deleting users not in current sync path.")
            users_to_delete = []
            for user_name in ts_user_names_domin:
                if len(ldap_user_name_orgs[user_name]) < 1:
                    users_to_delete.append(user_name)
            if len(users_to_delete) < 1:
                self.file_handle.write("\nNo User to be Deleted \n")
            else:
                self.file_handle.write("\nUser Deleted: {}\n"
                                       .format(users_to_delete))

        # Remove Groups from orgs which are not there in present sync
        if self.remove_user_orgs:
            user_org_removal = 0
            self.file_handle.write("\n===== User Org Removal Phase =====\n\n")
            logging.info("Removing users from Orgs not in current sync path.")
            for user_name in ts_user_names_domin:
                if len(ldap_user_name_orgs[user_name]) < 1:
                    continue
                if ts_user_name_orgs[user_name]\
                        .issubset(ldap_user_name_orgs[user_name]):
                    continue
                user_org_removal = 1
                user_delete_orgs = list(set(ts_user_name_orgs[user_name])
                                        - set(ldap_user_name_orgs[user_name]))
                self.file_handle.write("\n {} User Removed from {} Orgs: \n"
                                       .format(user_name, user_delete_orgs))
            if user_org_removal == 0:
                self.file_handle.write("\nNo User to removed from any org \n")


        print("Refer to {} for ldap report and {} for error logs.".format(
            self.file_handle.name, self.error_file.name))

        if len(unmapped_org_objects) >= 1:
            self.error_file.write("\nOrg mapping could not be found "
                                      "for the following objects:\n\n")
            self.error_file.writelines("{}\n".format(obj)
                                       for obj in self.unmapped_org_obj)
            logging.error("Org mapping of one or more objects could "
                         "not be found.")
            sys.exit(1)
