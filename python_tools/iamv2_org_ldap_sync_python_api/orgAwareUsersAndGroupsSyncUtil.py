#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2023
# Author: Indresh Gupta (indresh.gupta@thoughtspot.com)
"""Utilities function for orgAwareUsersAndGroupSync"""

# pylint: disable=R0912
import logging
from entityClasses import EntityType
from globalClasses import Constants
import tsApi

# pylint: disable=R0903, R0902, R0912, R0915, R1702, C0302, W0108
def sync_orgs(
        org_sync_tree,
        org_created,
        org_already_exist):
    """
    Method to sync orgs to TS
    """
    logging.info("Syncing Orgs in ThoughtSpot system")
    for org_name in org_sync_tree.orgs_to_create:
        result = org_sync_tree.ts_handle.create_org(
            org_name,
            org_name + "_description")
        if result.status == Constants.OPERATION_SUCCESS:
            msg = "\nOrg created: {}\n".format(org_name)
            org_created[0] += 1
        elif result.status == Constants.ORG_ALREADY_EXISTS:
            msg = "\nOrg exists: {}\n".format(org_name)
            org_already_exist[0] += 1
        else:
            reason = (
                str(result.data)
                if result.data is not None
                else super().NORSN
            )
            msg = "\nFailed to create org {}. {}\n".format(
                org_name, reason
            )
            logging.error(msg)
            org_sync_tree.error_file.write(msg)
        org_sync_tree.file_handle.write(msg)


def fetch_ts_org_list(
        org_sync_tree,
        org_name_to_org_id,
        org_id_to_org_name):
    """
    fetches org list from system and fills out
    org name to id / org id to name mapping
    """
    logging.debug("Fetching current orgs from ThoughtSpot system")
    result = org_sync_tree.ts_handle.list_orgs()
    if result.status == Constants.OPERATION_SUCCESS:
        for org in result.data:
            org_name_to_org_id[org.name] = org.id
            org_id_to_org_name[org.id] = org.name
    else:
        logging.error("Failed to fetch orgs from ThoughtSpot system.\n")
        reason = (
            str(result.data)
            if result.data is not None
            else super().NORSN
        )
        msg = "\nFailed to list all orgs. {}\n".format(
            reason
        )
        org_sync_tree.error_file.write(msg)
        org_sync_tree.file_handle.write(msg)

# todo: introduce new upsert api to handle orgs
def sync_users(
        org_sync_tree,
        dn_to_obj_ldap_map,
        ldap_user_name_to_org,
        org_name_to_org_id,
        ldap_user_names,
        users_created,
        users_synced):
    """
    Method to sync users to TS and populates:
    ldap_user_names
    orgId list for ldap users.
    """
    logging.info("Syncing users to ThoughtSpot system.")
    for user_dn in org_sync_tree.users_to_create:
        result = org_sync_tree.ldap_handle.dn_to_obj(
            user_dn,
            org_sync_tree.ldap_type,
            org_sync_tree.user_identifier,
            org_sync_tree.email_identifier,
            org_sync_tree.user_display_name_identifier,
            org_sync_tree.group_display_name_identifier,
            org_sync_tree.authdomain_identifier,
            org_sync_tree.member_str
        )
        if (result.status != Constants.OPERATION_SUCCESS
                or result.data is None):
            logging.debug(
                "Failed to obtain user object for user DN (%s)",
                user_dn
            )
            continue
        user = result.data
        dn_to_obj_ldap_map[user_dn] = user
        ldap_user_name_to_org[user.name] = [org_name_to_org_id[org_name]
                            for org_name in org_sync_tree.org_map[user_dn]]
        ldap_user_names.append(user.name)
        prop = {"mail": user.email} if user.email else None
        user_org_id = ldap_user_name_to_org[user.name]
        if len(user_org_id) < 1:
            reason = "User doesn't have any specified org"
            msg = "\nFailed to sync/create user {}. {}\n".format(
                user.name, reason
            )
            logging.debug(msg)
            org_sync_tree.error_file.write(msg)
            org_sync_tree.file_handle.write(msg)
            continue
        user_org_ids = '[' + ','.join(str(id) for id in user_org_id) + ']'
        result = org_sync_tree.ts_handle.search_user(
            user.name
        )
        if result.status == Constants.OPERATION_SUCCESS:
            # update user orgs
            result = org_sync_tree.ts_handle.update_user_org(
                user.name,
                Constants.Add,
                user_org_ids
            )
            if result.status == Constants.OPERATION_SUCCESS:
                msg = "\n{} User already exists and synced to {} orgs\n" \
                    .format(user.name, list(org_sync_tree.org_map[user_dn]))
                users_synced[0] += 1
            else:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "\nFailed to add user {} to {} orgs\n.{}".format(
                    user.name, list(org_sync_tree.org_map[user_dn]), reason
                )
                logging.debug(msg)
                org_sync_tree.error_file.write(msg)
            org_sync_tree.file_handle.write(msg)
            # sync other properties of user
            org_sync_tree.ts_handle.sync_user(
                user.name,
                user.display_name,
                tsApi.TSApiWrapper.LDAP_USER,
                None,  # password
                prop,
                None,  # groups
                org_sync_tree.upsert_user,
                True # all org scope
            )
        else:
            # create user in given orgs
            result = org_sync_tree.ts_handle.create_user(
                user.name,
                user.display_name,
                tsApi.TSApiWrapper.LDAP_USER,
                None,  # password
                prop,
                None,  # groups
                user_org_ids,
                True # all org scope
            )
            if result.status == Constants.OPERATION_SUCCESS:
                msg = "\n{} User created in {} orgs\n".format(user.name,
                                  list(org_sync_tree.org_map[user_dn]))
                users_created[0] += 1
            else:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "\nFailed to create user {} to {} orgs\n.{}".format(
                    user.name, list(org_sync_tree.org_map[user_dn]), reason
                )
                logging.debug(msg)
                org_sync_tree.error_file.write(msg)
            org_sync_tree.file_handle.write(msg)


def sync_groups(
        org_sync_tree,
        dn_to_obj_ldap_map,
        ldap_group_name_to_org,
        org_name_to_org_id,
        ldap_group_names,
        org_id_to_org_name,
        groups_created,
        groups_synced):
    """
    Create/Sync all groups to ThoughtSpot system and populates:
    ldap_group_names
    orgId list for ldap groups
    No. of groups created/synced in each org
    """
    logging.info("Syncing groups to ThoughtSpot system.")
    for group_dn in org_sync_tree.groups_to_create:
        result = org_sync_tree.ldap_handle.dn_to_obj(
            group_dn,
            org_sync_tree.ldap_type,
            org_sync_tree.user_identifier,
            org_sync_tree.email_identifier,
            org_sync_tree.user_display_name_identifier,
            org_sync_tree.group_display_name_identifier,
            org_sync_tree.authdomain_identifier,
            org_sync_tree.member_str
        )
        if (result.status != Constants.OPERATION_SUCCESS
                or result.data is None):
            logging.debug(
                "Failed to obtain group object for group DN (%s)",
                group_dn
            )
            continue
        group = result.data
        dn_to_obj_ldap_map[group_dn] = group
        ldap_group_name_to_org[group.name] = [org_name_to_org_id[org_name]
                          for org_name in org_sync_tree.org_map[group_dn]]
        ldap_group_names.append(group.name)

        group_org_id = ldap_group_name_to_org[group.name]
        if len(group_org_id) < 1:
            reason = "Group doesn't have any specified org"
            msg = "\nFailed to sync/create Group {}. {}\n".format(
                group.name, reason
            )
            logging.debug(msg)
            org_sync_tree.error_file.write(msg)
            org_sync_tree.file_handle.write(msg)
            continue
        group_created_orgs, group_exists_orgs = [], []
        for org_id in group_org_id:
            org_sync_tree.switch_org(org_id)
            result = org_sync_tree.ts_handle.sync_group(
                group.name, group.display_name,
                tsApi.TSApiWrapper.LDAP_GROUP,
                None,  # description
                None,  # privileges
                org_sync_tree.upsert_group
            )
            if result.status == Constants.OPERATION_SUCCESS:
                group_created_orgs \
                    .append(org_id_to_org_name[org_id])
                groups_created[org_id_to_org_name[org_id]] += 1
            elif result.status == Constants.GROUP_ALREADY_EXISTS:
                group_exists_orgs \
                    .append(org_id_to_org_name[org_id])
                groups_synced[org_id_to_org_name[org_id]] += 1
            else:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "\nFailed to create group {} in {} Org. {}\n"\
                    .format(
                    group.name, org_id_to_org_name[org_id], reason
                )
                logging.debug(msg)
                org_sync_tree.file_handle.write(msg)

        if len(group_created_orgs) > 0:
            msg = "\n{} Group Created in {} orgs\n".format(
                group.name, group_created_orgs)
            logging.debug(msg)
            org_sync_tree.file_handle.write(msg)
        if len(group_exists_orgs) > 0:
            msg = "\n{} Group already exists in {} orgs\n".format(
                group.name, group_exists_orgs)
            logging.debug(msg)
            org_sync_tree.file_handle.write(msg)

def fetch_ts_user_list(
        org_sync_tree,
        domain_name,
        user_name_to_id_ts_map,
        user_id_to_name_ts_map,
        ts_user_names,
        ts_user_name_to_org):
    """
    Fetch user info from TS and populates:
    user_name_to_id_ts_map
    user_id_to_name_ts_map
    ts_user_names
    ts_user_name_to_org - orgId list for ts users
    """
    logging.debug("Fetching current users from ThoughtSpot "
                  "system in domain (%s) including recently "
                  "created.", domain_name)
    result = org_sync_tree.ts_handle.list_users(allOrgs=True)
    if result.status == Constants.OPERATION_SUCCESS:
        for user in result.data:
            user_name_to_id_ts_map[user.name] = user.id
            user_id_to_name_ts_map[user.id] = user.name
            if user.name.endswith(domain_name):
                ts_user_names.add(user.name)
                ts_user_name_to_org[user.name].update(user.orgIds)
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
        logging.error("Failed to fetch users from "
                      "ThoughtSpot system.\n")


def fetch_ts_group_list(
        org_sync_tree,
        domain_name,
        group_name_to_id_ts_map,
        group_id_to_name_ts_map,
        ts_group_names,
        ts_group_name_to_org):
    """
    Fetch group info from TS and populates:
    group_name_to_id_ts_map
    group_id_to_name_ts_map
    ts_group_names
    ts_group_name_to_org - orgId list for ts groups
    """
    logging.debug("Fetching current groups from ThoughtSpot "
                  "system in domain (%s) including recently "
                  "created.", domain_name)
    result = org_sync_tree.ts_handle.list_groups(allOrgs=True)
    if result.status == Constants.OPERATION_SUCCESS:
        for group in result.data:
            group_name_to_id_ts_map[(group.name,
                                     group.orgIds[0])] = group.id
            group_id_to_name_ts_map[group.id] = group.name
            if group.name.endswith(domain_name):
                ts_group_names.add(group.name)
                ts_group_name_to_org[group.name] \
                    .update(group.orgIds)
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


def populate_rltn_maps(
        org_sync_tree,
        dn_to_obj_ldap_map,
        group_name_to_id_ts_map,
        org_name_to_org_id,
        parent_id_to_member_user_id_ts_map,
        parent_id_to_member_group_id_ts_map,
        ldap_user_name_to_org,
        user_name_to_id_ts_map,
        ldap_group_name_to_org,
        parent_id_to_org_map):
    """
    Create relationship map to populate membership.
    """
    for (child, parent) in org_sync_tree.relationship:
        if child is not None and parent is not None:
            childObj = dn_to_obj_ldap_map[child]
            parentObj = dn_to_obj_ldap_map[parent]
            if childObj is None or parentObj is None:
                continue
            for org in org_sync_tree.org_map[parent]:
                parentId = \
                    group_name_to_id_ts_map[(parentObj.name.lower(),
                                             org_name_to_org_id[org])]
                if not parent_id_to_member_user_id_ts_map[parentId]:
                    parent_id_to_member_user_id_ts_map[parentId] = set()
                if not parent_id_to_member_group_id_ts_map[parentId]:
                    parent_id_to_member_group_id_ts_map[parentId] = \
                        set()
                if childObj.type == EntityType.USER:
                    if len \
                        (ldap_user_name_to_org[childObj.name.lower()]) < 1:
                        continue
                    childId = \
                        user_name_to_id_ts_map[childObj.name.lower()]
                    parent_id_to_member_user_id_ts_map[parentId].add(
                        childId
                    )
                elif childObj.type == EntityType.GROUP:
                    if len \
                        (ldap_group_name_to_org[childObj.name.lower()]) < 1:
                        continue
                    childId = \
                        group_name_to_id_ts_map[(childObj.name.lower(),
                                                 org_name_to_org_id[org])]
                    parent_id_to_member_group_id_ts_map[parentId].add(
                        childId
                    )
                parent_id_to_org_map[parentId] = \
                    org_name_to_org_id[org]
        elif child is None and parent is not None:
            parentObj = dn_to_obj_ldap_map[parent]
            if parentObj is None:
                continue
            for org in org_sync_tree.org_map[parent]:
                parentId = \
                    group_name_to_id_ts_map[(parentObj.name.lower(),
                                             org_name_to_org_id[org])]
                parent_id_to_member_user_id_ts_map[parentId] = set()
                parent_id_to_member_group_id_ts_map[parentId] = set()
                parent_id_to_org_map[parentId] = \
                    org_name_to_org_id[org]


def create_member_user_rltn(
        org_sync_tree,
        parent_id_to_member_user_id_ts_map,
        parent_id_to_org_map,
        group_id_to_name_ts_map):
    """
    Create member user relationship in ThoughtSpot system.
    """
    failed_relationships = 0
    logging.info("Creating member user to group relationships.")
    if not parent_id_to_member_user_id_ts_map:
        msg = "\nNo member user to group relationship to create.\n"
        logging.debug(msg)
        org_sync_tree.file_handle.write(msg)
    else:
        for parent_id in list(parent_id_to_member_user_id_ts_map.keys()):
            orgId = parent_id_to_org_map[parent_id]
            if orgId is None:
                continue # parent doesn't have any orgId
            org_sync_tree.switch_org(orgId)
            result = org_sync_tree.ts_handle.update_users_to_group(
                list(parent_id_to_member_user_id_ts_map[parent_id]),
                parent_id,
                org_sync_tree.keep_local_membership
            )
            if result.status != Constants.OPERATION_SUCCESS:
                name = group_id_to_name_ts_map[parent_id]
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "Failed to update member users to group {} {}\n"
                msg = msg.format(name, reason)
                org_sync_tree.error_file.write(msg)
                logging.error(msg)
                failed_relationships += 1
        if failed_relationships == 0:
            msg = "\nDone creating member users to group relationships.\n"
            logging.debug(msg)
        else:
            msg = "\nOne or more member users to group relationship(s)" \
                  " could not be created.\n"
            logging.error(msg)
        org_sync_tree.file_handle.write(msg)


def create_member_group_rltn(
        org_sync_tree,
        parent_id_to_member_group_id_ts_map,
        parent_id_to_org_map,
        group_id_to_name_ts_map):
    """
    Create member group relationship in ThoughtSpot system.
    """
    failed_relationships = 0
    logging.info("Creating member group to group relationships.")
    if not parent_id_to_member_group_id_ts_map:
        msg = "\nNo member group to group relationship to create.\n"
        logging.debug(msg)
        org_sync_tree.file_handle.write(msg)
    else:
        for parent_id in list(parent_id_to_member_group_id_ts_map.keys()):
            orgId = parent_id_to_org_map[parent_id]
            if orgId is None:
                continue # parent doesn't have a orgId
            org_sync_tree.switch_org(orgId)
            result = org_sync_tree.ts_handle.update_groups_to_group(
                list(parent_id_to_member_group_id_ts_map[parent_id]),
                parent_id,
                org_sync_tree.keep_local_membership
            )
            if result.status != Constants.OPERATION_SUCCESS:
                name = group_id_to_name_ts_map[parent_id]
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "Failed to update member groups to group {} {}\n"
                msg = msg.format(name, reason)
                org_sync_tree.file_handle.write(msg)
                org_sync_tree.error_file.write(msg)
                logging.error(msg)
                failed_relationships += 1

        if failed_relationships == 0:
            msg = "\nDone creating member groups to group relationships.\n"
            logging.debug(msg)
        else:
            msg = "\nOne or more member groups to group relationship(s)" \
                  " could not be created.\n"
            logging.error(msg)
        org_sync_tree.file_handle.write(msg)


def delete_groups(
        org_sync_tree,
        ts_group_names,
        ldap_group_name_to_org,
        ts_group_name_to_org,
        group_name_to_id_ts_map,
        org_id_to_org_name,
        group_id_to_name_ts_map,
        groups_deleted):
    """
    Delete groups which are not there in present sync or
    orgs for which org list is empty
    """
    org_sync_tree.file_handle.write("\n===== Group Deletion Phase =====\n\n")
    logging.info("Deleting groups not in current sync path.")
    for group_name in ts_group_names:
        ldap_group_orgs = ldap_group_name_to_org[group_name]
        ts_group_orgs = ts_group_name_to_org[group_name]
        if len(ldap_group_orgs) >= 1:
            continue
        group_deleted = 1
        for org_id in ts_group_orgs:
            group_id = group_name_to_id_ts_map[(group_name, org_id)]
            org_sync_tree.switch_org(org_id)
            result = org_sync_tree.ts_handle.delete_groups([group_id])
            if result.status != Constants.OPERATION_SUCCESS:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "Failed to delete {} group from {} " \
                      "org. {}\n".format(group_name,
                                         org_id_to_org_name[org_id], reason)
                group_deleted = 0
                org_sync_tree.error_file.write(msg)
                org_sync_tree.file_handle.write(msg)
                logging.debug(msg)
            else:
                logging.debug("Group Deleted: %s",
                              group_id_to_name_ts_map[group_id])
        groups_deleted[0] += group_deleted
        if group_deleted == 1:
            msg = "\n{} Group deleted\n" \
                .format(group_name)
        else:
            msg = "\nFailed to delete {} Group\n" \
                .format(group_name)
        org_sync_tree.file_handle.write(msg)
    if groups_deleted[0] == 0:
        org_sync_tree.file_handle.write("No groups deleted\n")


def remove_groups_from_orgs(
        org_sync_tree,
        ts_group_names,
        ldap_group_name_to_org,
        ts_group_name_to_org,
        group_name_to_id_ts_map,
        org_id_to_org_name,
        groups_org_removed):

    """
    Remove Group from orgs which are not there in present sync
    """
    group_org_removal = 0
    org_sync_tree.file_handle.write("\n===== Group Org Removal Phase =====\n")
    logging.info("Removing groups from Orgs not in current sync path.")
    for group_name in ts_group_names:
        ldap_group_orgs = ldap_group_name_to_org[group_name]
        ts_group_orgs = ts_group_name_to_org[group_name]
        if len(ldap_group_orgs) < 1:
            continue # this will come under purge flag
        for org_id in ts_group_orgs:
            if org_id in ldap_group_orgs:
                continue
            group_org_removal = 1
            group_id = group_name_to_id_ts_map[(group_name, org_id)]
            org_sync_tree.switch_org(org_id)
            result = org_sync_tree.ts_handle.delete_groups([group_id])
            if result.status != Constants.OPERATION_SUCCESS:
                reason = (
                    str(result.data)
                    if result.data is not None
                    else super().NORSN
                )
                msg = "Failed to Remove {} group from {} org\n. {}\n" \
                    .format(
                    group_name, org_id_to_org_name[org_id], reason
                )
                org_sync_tree.error_file.write(msg)
                org_sync_tree.file_handle.write(msg)
                logging.debug(msg)
            else:
                logging.debug("Removed %s Group from %s org\n",
                              group_name, org_id_to_org_name[org_id])
                groups_org_removed[group_name] \
                    .add(org_id_to_org_name[org_id])
        if len(groups_org_removed[group_name]) > 0:
            msg = "\n{} Group Removed from {} orgs\n" \
                .format(group_name,
                        list(groups_org_removed[group_name]))
            org_sync_tree.file_handle.write(msg)

    if group_org_removal == 0:
        org_sync_tree.file_handle.write("\nNo Groups to be removed "
                               "from any orgs\n")

def delete_users(
        org_sync_tree,
        ts_user_names,
        ldap_user_name_to_org,
        user_name_to_id_ts_map,
        users_deleted,
        user_id_to_name_ts_map):
    """
    Deletes users which are not there in present sync or
    whose org list is empty
    """
    users_to_delete = []
    org_sync_tree.file_handle.write("\n===== User Deletion Phase =====\n\n")
    logging.info("Deleting users not in current sync path.")
    for user_name in ts_user_names:
        if len(ldap_user_name_to_org[user_name]) < 1:
            users_to_delete \
                .append(user_name_to_id_ts_map[user_name])

    result = org_sync_tree.ts_handle.delete_users(users_to_delete)
    users_deleted[0] = len(users_to_delete)
    if result.status != Constants.OPERATION_SUCCESS:
        reason = (
            str(result.data)
            if result.data is not None
            else super().NORSN
        )
        user_name_list = [user_id_to_name_ts_map[uid]
                          for uid in users_to_delete]
        msg = "Failed to delete users {} {}\n".format(
            user_name_list, reason
        )
        org_sync_tree.error_file.write(msg)
        logging.error(msg)
        users_deleted[0] = 0
    elif users_deleted[0] == 0:
        msg = "No users to delete\n"
        logging.debug(msg)
    else:
        msg = "Deleted {} users\n".format(
            ",\n".join(
                user_id_to_name_ts_map[uid]
                for uid in users_to_delete
            )
        )
        logging.debug(
            "Users deleted [%s]:\n%s\n",
            len(users_to_delete),
            ",\n".join(
                user_id_to_name_ts_map[uid]
                for uid in users_to_delete
            ),
        )
    org_sync_tree.file_handle.write(msg)


def remove_users_from_orgs(
        org_sync_tree,
        ts_user_names,
        ts_user_name_to_org,
        ldap_user_name_to_org,
        org_id_to_org_name,
        users_org_removed):
    """
    Remove Users from orgs which are not there in present sync
    """
    user_org_removal = 0
    org_sync_tree.file_handle.write("\n===== User Org Removal =====\n\n")
    logging.info("Removing users from orgs not in current "
                 "sync path.")
    for user_name in ts_user_names:
        ts_org_list = ts_user_name_to_org[user_name]
        ldap_org_list = ldap_user_name_to_org[user_name]
        if len(ldap_org_list) < 1:
            continue # since this will come under purge flag
        if ts_org_list.issubset(ldap_org_list):
            continue
        user_org_removal = 1
        result = org_sync_tree.ts_handle.update_user_org(
            user_name,
            Constants.Replace,
            '[' + ','.join(str(id) for id in ldap_org_list) + ']'
        )
        org_list = [org_id_to_org_name[id] for id in
                    ts_org_list if id not in ldap_org_list]
        if result.status == Constants.OPERATION_SUCCESS:
            msg = "Removed {} User from orgs {}\n".format(
                user_name, org_list)
            users_org_removed[user_name] = org_list
        else:
            reason = (
                str(result.data)
                if result.data is not None
                else super().NORSN
            )
            msg = "Failed to remove {} user from {} orgs\n.{}" \
                .format(user_name, org_list, reason)
            logging.error(msg)
            org_sync_tree.error_file.write(msg)
        org_sync_tree.file_handle.write(msg)
    if user_org_removal == 0:
        org_sync_tree.file_handle.write("No user to removed from any org\n")
