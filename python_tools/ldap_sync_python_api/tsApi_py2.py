#!/usr/bin/env python
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Classes and Functions to log into and use TS app."""
import httplib
import json
import logging
import string
from functools import wraps
from random import choice
from uuid import UUID

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from entityClasses import EntityProperty, EntityType
from globalClasses import Constants, Result


def password_gen():
    """Generates random string of length 10 characters for password.
       @return: Password with random characters of specified length.
    """
    chars = string.ascii_letters + string.digits + string.punctuation
    passwd = ("".join(choice(chars) for _ in range(7))
            + choice(string.digits)
            + choice(string.ascii_uppercase)
            + choice(string.ascii_lowercase))
    return passwd


def is_valid_uuid(value):
    """Checks if the given input is a valid UUID.
       @param value: Input to be validated as a UUID.
       @return: True if it is a valid UUID else False.
    """
    try:
        # Try to read the valid UUID. A valid UUID can be read without throwing
        # any exception.
        _ = UUID(value, version=4)
        return True
    except:
        return False


def pre_check(function):
    """A decorator to check for user authentication before executing the given
       command.
       @param function: Function to apply the wrapper around.
       @return: An entity where authentication check happens before the
       actual function call.
    """

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        """Wrapper to wrap the function in.
           @param self: The self pointer to class instance.
           @param *args: List of arguments being passed to the fucntion which
           is being wrapped.
           @param **kwargs: Dictionary being passed to the fucntion which is
           being wrapped.
           @return: Returns the original function.
        """
        if not self._is_authenticated():
            logging.error(TSApiWrapper.USER_AUTHENTICATION_FAILURE)
            return Result(Constants.AUTHENTICATION_FAILURE)
        return function(self, *args, **kwargs)

    return wrapper


class TSApiWrapper(object):
    """Wrapper class to log in and execute commands in TS system."""

    # URL end points used for various calls.
    SERVER_URL = "{hostport}/callosum/v1"
    LOGIN = SERVER_URL + "/session/login"
    INFO = SERVER_URL + "/session/info"
    UPSERT_USER = SERVER_URL + "/session/ldap/users"
    UPSERT_GROUP = SERVER_URL + "/session/ldap/groups"
    CREATE_USER = SERVER_URL + "/session/user/create"
    CREATE_GROUP = SERVER_URL + "/session/group/create"
    DELETE_USERS = SERVER_URL + "/session/user/deleteusers"
    DELETE_GROUPS = SERVER_URL + "/session/group/deletegroups"
    GET_MEMBERS = SERVER_URL + "/metadata/list"
    UPDATE_USERS_IN_GROUPS = SERVER_URL + "/session/group/updateusersingroup"
    UPDATE_GROUPS_IN_GROUPS = SERVER_URL + "/session/group/updategroupsingroup"
    LIST_USERS_IN_A_GROUP = SERVER_URL + "/session/group/listuser/{groupid}"
    LIST_GROUPS_IN_A_GROUP = SERVER_URL + "/session/group/listgroup/{groupid}"
    ADD_USER_TO_GROUP = SERVER_URL + "/session/group/adduser"
    ADD_GROUPS_TO_GROUP = SERVER_URL + "/session/group/addgroups"

    # Message constants
    USER_AUTHENTICATION_FAILURE = "User not authenticated."
    USER_AUTHENTICATION_SUCCESS = "User successfully authenticated."
    UNKNOWN_ENTITY_TYPE = "Unknown entity type."
    NO_OPERATION_NEEDED = "Nothing to be done here."

    # Principal type constants
    LOCAL_USER = "LOCAL_USER"
    LDAP_USER = "LDAP_USER"
    SAML_USER = "SAML_USER"
    LOCAL_GROUP = "LOCAL_GROUP"
    LDAP_GROUP = "LDAP_GROUP"

    def __init__(self, disable_ssl=False):
        """@param disable_ssl: Flag to disable SSL verification."""
        self.hostport = None
        self.session = requests.Session()
        if disable_ssl:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            self.session.verify = False
        self.session.headers = {"X-Requested-By": "ThoughtSpot"}
        self.authenticated = False

    # Authentication Functions #

    def login(self, hostport, username, password):
        """Logs the user into the system.
           @param hostport: Complete URL of the TS system to connect to
           http(s)://<host>:<port>
           @param username: Username for the user.
           @param password: Password for the user.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        try:
            self.hostport = hostport
            response = self.session.post(
                TSApiWrapper.LOGIN.format(hostport=self.hostport),
                data={"username": username,
                      "password": password},
            )
            if response.status_code == httplib.OK:
                self.authenticated = True
                logging.debug(TSApiWrapper.USER_AUTHENTICATION_SUCCESS)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error("Login failure.")
            return Result(Constants.OPERATION_FAILURE, response)
        except requests.ConnectionError as e:
            logging.error("Error in network.")
            return Result(Constants.OPERATION_FAILURE, e)
        except requests.HTTPError as e:
            logging.error("Error in HTTP connection.")
            return Result(Constants.OPERATION_FAILURE, e)
        except requests.Timeout as e:
            logging.error("Timeout error.")
            return Result(Constants.OPERATION_FAILURE, e)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def _is_authenticated(self):
        """Tells us if the user is authenticated or not.
           @return: Bool value to signify user logged in status.
        """
        return self.authenticated

    # Create Functions #

    @pre_check
    def info(self):
        """Gets the session info object.
           @return: Returns map of session info object.
        """
        try:
            response = self.session.get(
                TSApiWrapper.INFO.format(hostport=self.hostport)
            )
            if response.status_code == httplib.OK:
                logging.debug("Info object procured.")
                return Result(
                    Constants.OPERATION_SUCCESS, json.loads(response.text)
                )
            logging.error("Unable to obtain Info object.")
            return Result(Constants.OPERATION_FAILURE)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def is_admin(self):
        """Tells if the user logging in has admin privileges.
           @return: True if logged in user has admin privileges else False
        """
        result = self.info()
        if result.status == Constants.OPERATION_SUCCESS:
            privileges = result.data["privileges"]
            return Constants.PRIVILEGE_ADMINSTRATION in privileges
        return False

    @pre_check
    def sync_group(
        self,
        name,
        display_name,
        grouptype=None,
        description=None,
        privileges=None,
        upsert_group=False
    ):
        """Creates new group and adds it to TS system.
           @param name: Name of the new group.
           @param display_name: Display name of the group.
           @param grouptype: Type of group to create.
           @param description: Description of the new group.
           @param privileges: Privileges provided to the group.
           @param upsert_group: Upsert the groups if true else only create.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        params = {"name": name, "display_name": display_name}
        if grouptype is not None:
            params["grouptype"] = grouptype
        if description is not None:
            params["description"] = description
        if privileges is not None:
            params["privileges"] = json.dumps(privileges)

        try:
            if upsert_group:
                response = self.session.post(
                    TSApiWrapper.UPSERT_GROUP.format(hostport=self.hostport),
                    data=params,
                )
            else:
                response = self.session.post(
                    TSApiWrapper.CREATE_GROUP.format(hostport=self.hostport),
                    data=params,
                )
            if response.status_code == httplib.OK:
                logging.debug("New group %s added.", name)
                return Result(Constants.OPERATION_SUCCESS)
            if ((upsert_group and response.status_code == httplib.NO_CONTENT) or
                    ((not upsert_group)
                     and response.status_code == httplib.CONFLICT)):
                logging.debug("Group %s already exists.", name)
                return Result(Constants.GROUP_ALREADY_EXISTS)
            logging.error("New group %s not added. Response: %s", name,
                          response.text)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def sync_user(
        self,
        name,
        display_name,
        usertype=None,
        password=None,
        properties=None,
        groups=None,
        upsert_user=False
    ):
        """Creates new user and adds it to TS system.
           @param name: Name of the new user.
           @param display_name: Name to be displayed in TS system.
           @param usertype: Type of user to create.
           @param password: Password to be set for the user.
           @param properties: Extra properties related to the user like
           user email etc.
           @param groups: List of group ids the user belongs to.
           @param upsert_user: Upsert the users if true else only create.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        params = {"name": name, "displayname": display_name}
        if usertype is not None:
            params["usertype"] = usertype
        # If Password is not passed generate a random string as password.
        # Used in cases where authentication is done by an external agent.
        if password is None:
            password = password_gen()
        params["password"] = password
        if properties is not None:
            params["properties"] = json.dumps(properties)
        if groups is not None:
            params["groups"] = json.dumps(groups)

        try:
            if upsert_user:
                response = self.session.post(
                    TSApiWrapper.UPSERT_USER.format(hostport=self.hostport),
                    data=params,
                )
            else:
                response = self.session.post(
                    TSApiWrapper.CREATE_USER.format(hostport=self.hostport),
                    data=params,
                )
            if response.status_code == httplib.OK:
                logging.debug("New user %s added.", name)
                return Result(Constants.OPERATION_SUCCESS)
            if ((upsert_user and response.status_code == httplib.NO_CONTENT) or
                    ((not upsert_user)
                     and response.status_code == httplib.CONFLICT)):
                logging.debug("User %s already exists.", name)
                return Result(Constants.USER_ALREADY_EXISTS)
            logging.error("New user %s not added. Response: %s", name,
                          response.text)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    # Delete Functions #

    @pre_check
    def _delete_entities(self, entity, entity_list):
        """Deletes users/groups given the id list.
           @param entity: EntityType that is being deleted.
           @param entity_list: List of entity IDs to delete.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        # Filter irregular input objects from entity_list
        entity_list = filter(is_valid_uuid, entity_list)

        if not entity_list:
            logging.debug(TSApiWrapper.NO_OPERATION_NEEDED)
            return Result(Constants.OPERATION_SUCCESS)

        success_msg = "Successfully deleted {}(s).".format(entity)
        failure_msg = "Failed to delete {}(s).".format(entity)
        if entity == EntityType.GROUP:
            end_point = TSApiWrapper.DELETE_GROUPS
        elif entity == EntityType.USER:
            end_point = TSApiWrapper.DELETE_USERS
        else:
            logging.error(TSApiWrapper.UNKNOWN_ENTITY_TYPE)
            return Result(Constants.OPERATION_FAILURE)

        try:
            response = self.session.post(
                end_point.format(hostport=self.hostport),
                data={"ids": json.dumps(entity_list)},
            )
            if response.status_code == httplib.NO_CONTENT:
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def delete_groups(self, gid_list):
        """Deletes the groups.
           @param gid_list: ID list of groups.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        return self._delete_entities(EntityType.GROUP, gid_list)

    def delete_users(self, uid_list):
        """Deletes the users.
           @param uid_list: ID list of users.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        return self._delete_entities(EntityType.USER, uid_list)

    # List Functions #
    def _get_batched_entities(self, entity, offset, batchsize):
        """Gets entities in TS system.
           @entity: Entity to fetch User/Group
           @batchsize: Number of entities to fetch
           @offset: Batch offset
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        entity_list = []

        success_msg = "Successfully returning {} list.".format(entity)
        failure_msg = "Failed to procure {} list.".format(entity)
        end_point = TSApiWrapper.GET_MEMBERS
        if entity == EntityType.GROUP:
            params = {"type": "USER_GROUP"}
        elif entity == EntityType.USER:
            params = {"type": "USER"}
        else:
            logging.error(TSApiWrapper.UNKNOWN_ENTITY_TYPE)
            return Result(Constants.OPERATION_FAILURE)
        params["batchsize"] = batchsize
        params["offset"] = offset

        try:
            response = self.session.get(
                   end_point.format(hostport=self.hostport), params=params
                   )
            if response.status_code == httplib.OK:
                responseDict = json.loads(response.text)
                for item in responseDict["headers"]:
                    assert "id" in item, "id not in item"
                    assert "name" in item, ("name not present for {}"
                        .format(
                            item["id"]
                        ))
                    assert "type" in item, ("type not present for {} {}"
                        .format(
                            item["id"], item["name"]
                        ))
                    ent_property_obj = EntityProperty(
                        item["id"], item["name"], item["type"]
                    )
                    entity_list.append(ent_property_obj)
                logging.debug(success_msg)
                is_last_batch = responseDict["isLastBatch"]
                return Result(Constants.OPERATION_SUCCESS,
                              (entity_list, is_last_batch))
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def _list_entities(self, entity, batchsize):
        """Lists (user/group)s in TS system.
           @param entity: Entity to fetch User/Group.
           @param batchsize: Batch size for pagination.
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        entity_list = []
        success_msg = "Successfully returning {} list.".format(entity)
        failure_msg = "Failed to procure {} list.".format(entity)
        if batchsize == 0 or batchsize is None:
            batchsize = 200

        is_last_batch = False
        batch_count = 0
        # Paginate the calls to /list
        while not is_last_batch:
            offset = batchsize * batch_count
            result_obj = self._get_batched_entities(entity, offset, batchsize)
            if result_obj.status == Constants.OPERATION_SUCCESS:
                ent_property_obj, is_last_batch = result_obj.data
                entity_list.extend(ent_property_obj)
                batch_count += 1
            else:
                batch_fail_msg = " Failed at batch number: {}".format(
                    batch_count
                    )
                logging.error(failure_msg + batch_fail_msg)
                return result_obj
        logging.debug(success_msg)
        return Result(Constants.OPERATION_SUCCESS, entity_list)

    def list_groups(self, batchsize=200):
        """Lists groups in TS system.
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        return self._list_entities(EntityType.GROUP, batchsize)

    def list_users(self, batchsize=200):
        """Lists users in TS system.
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        return self._list_entities(EntityType.USER, batchsize)

    # Add entities to group functions #

    @pre_check
    def add_user_to_group(self, uid, gid):
        """Method to add user to a group.
           @param uid: User ID.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        if uid is None:
            logging.debug(TSApiWrapper.NO_OPERATION_NEEDED)
            return Result(Constants.OPERATION_SUCCESS)

        success_msg = "Successfully added the user to group."
        failure_msg = "Failed to add user to the group."

        try:
            response = self.session.post(
                TSApiWrapper.ADD_USER_TO_GROUP.format(hostport=self.hostport),
                data={"userid": uid, "groupid": gid},
            )
            if response.status_code == httplib.NO_CONTENT:
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def add_groups_to_group(self, principalids, gid):
        """Method to add user to a group.
           @param principalids: Group ID list.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        # Filter irregular input objects from principalids
        principalids = filter(is_valid_uuid, principalids)

        if not principalids:
            logging.debug(TSApiWrapper.NO_OPERATION_NEEDED)
            return Result(Constants.OPERATION_SUCCESS)

        success_msg = "Successfully added groups to group."
        failure_msg = "Failed to add groups to the group."

        try:
            response = self.session.post(
                TSApiWrapper.ADD_GROUPS_TO_GROUP.format(
                    hostport=self.hostport
                ),
                data={
                    "principalids": json.dumps(principalids),
                    "groupid": gid,
                },
            )
            if response.status_code == httplib.NO_CONTENT:
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    # Group update Functions #

    @pre_check
    def _update_group_membership(self, entity, entity_list, gid,
                                 keep_local_membership):
        """Method used to update a group with member users/groups. Update is
           designed to be of the form delete all and create. So when member
           groups are being updated current member group list is deleted and
           udpated with the new memeber group list being provided. Similar
           steps are taken for member user list update too.
           @param entity: EntityType user/group.
           @param entity_list: Entity ID list to be updated as members of
           the group.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        # Append local object IDs to keep local memberships
        if keep_local_membership:
            if entity == EntityType.GROUP:
                result = self.list_groups_in_group(gid)
                if result.status != Constants.OPERATION_SUCCESS:
                    return Result(result.status)
                current_groups = result.data
                for group in current_groups:
                    if group.type == "LOCAL_GROUP":
                        entity_list.append(group.id)
            else:
                result = self.list_users_in_group(gid)
                if result.status != Constants.OPERATION_SUCCESS:
                    return Result(result.status)
                current_users = result.data
                for user in current_users:
                    if user.type == "LOCAL_USER":
                        entity_list.append(user.id)
        # Filter irregular input objects from entity_list
        entity_list = filter(is_valid_uuid, entity_list)

        if entity == EntityType.GROUP:
            id_list_key = "principalids"
            end_point = TSApiWrapper.UPDATE_GROUPS_IN_GROUPS
        elif entity == EntityType.USER:
            id_list_key = "userids"
            end_point = TSApiWrapper.UPDATE_USERS_IN_GROUPS
        else:
            logging.error(TSApiWrapper.UNKNOWN_ENTITY_TYPE)
            return Result(Constants.OPERATION_FAILURE)

        success_msg = "Successfully updated the group with {}s.".format(entity)
        failure_msg = "Failed to update {}s the group.".format(entity)

        try:
            response = self.session.post(
                end_point.format(hostport=self.hostport),
                data={id_list_key: json.dumps(entity_list), "groupid": gid},
            )
            if response.status_code == httplib.NO_CONTENT:
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def update_groups_to_group(self, group_list, gid,
                               keep_local_membership=False):
        """Method used to update member groups of a group. Current member group
           list is deleted and new group_list is updated as member group list.
           @param group_list: Group ID list to be updated as members of the
           group.
           @param gid: Parent Group ID.
           @param keep_local_membership: Flag indicating whether to keep the
           group membership of local principals during ldap sync, by default
           we loose it.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        return self._update_group_membership(EntityType.GROUP, group_list, gid,
                                             keep_local_membership)

    def update_users_to_group(self, user_list, gid,
                              keep_local_membership=False):
        """Method used to update member users of a group. Current member user
           list is deleted and new user_list is updated as member user list.
           @param user_list: UserID list to be updated as members of the group.
           @param gid: Parent Group ID.
           @param keep_local_membership: Flag indicating whether to keep the
           group membership of local principals during ldap sync, by default
           we loose it.
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        return self._update_group_membership(EntityType.USER, user_list, gid,
                                             keep_local_membership)

    # List entities in group #

    @pre_check
    def _list_entities_in_group(self, entity, gid):
        """Method used to list member users/groups of a group.
           @param entity: EntityType user/group.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           list of EntityProperty objects.
        """
        entity_list = []

        if entity == EntityType.GROUP:
            end_point = TSApiWrapper.LIST_GROUPS_IN_A_GROUP
        elif entity == EntityType.USER:
            end_point = TSApiWrapper.LIST_USERS_IN_A_GROUP
        else:
            logging.error(TSApiWrapper.UNKNOWN_ENTITY_TYPE)
            return Result(Constants.OPERATION_FAILURE)

        success_msg = "Successfully listed the {}s in the group.".format(
            entity
        )
        failure_msg = "Failed to list the {}s the group.".format(entity)

        try:
            response = self.session.get(
                end_point.format(hostport=self.hostport, groupid=gid)
            )
            if response.status_code == httplib.OK:
                for item in json.loads(response.text):
                    ent_property_obj = EntityProperty(
                        item["header"]["id"],
                        item["header"]["name"],
                        item["header"]["type"],
                    )
                    entity_list.append(ent_property_obj)
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS, entity_list)
            logging.error(failure_msg)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def list_groups_in_group(self, gid):
        """Method used to list member groups of a group.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           list of EntityProperty objects.
        """
        return self._list_entities_in_group(EntityType.GROUP, gid)

    def list_users_in_group(self, gid):
        """Method used to list member users of a group.
           @param gid: Group ID.
           @return: Result object with operation status and data. Here data is
           list of EntityProperty objects.
        """
        return self._list_entities_in_group(EntityType.USER, gid)

    # Functions which aren't exposed as API but serve as helpers to fetch data #
    # Specialized getter functions #

    @pre_check
    def _get_entityid_with_name(self, entity, name):
        """Returns user/group id given the unique name of the user/group.
           @param entity: EntityType user/group.
           @param name: Unique name of the user/group.
           @return: Result object with operation status and data. Here data is
           ID if user/group is present in the system else None.
        """
        if entity == EntityType.GROUP:
            entity_list = self.list_groups()
        elif entity == EntityType.USER:
            entity_list = self.list_users()
        else:
            logging.error(TSApiWrapper.UNKNOWN_ENTITY_TYPE)
            return Result(Constants.OPERATION_FAILURE)

        for ent in entity_list.data:
            if ent.name == name:
                return Result(Constants.OPERATION_SUCCESS, ent.id)
        logging.debug("Such an entity doesn't exist.")
        return Result(Constants.OPERATION_FAILURE)

    def get_groupid_with_name(self, name):
        """Returns group id given the unique name of the group.
           @param name: Unique name of the group.
           @return: Result object with operation status and data. Here data is
           ID if user/group is present in the system else None.
        """
        return self._get_entityid_with_name(EntityType.GROUP, name)

    def get_userid_with_name(self, name):
        """Returns user id given the unique name of the user.
           @param name: Unique name of the user.
           @return: Result object with operation status and data. Here data is
           ID if user/group is present in the system else None.
        """
        return self._get_entityid_with_name(EntityType.USER, name)
