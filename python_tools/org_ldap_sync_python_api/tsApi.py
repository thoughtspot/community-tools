#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Classes and Functions to log into and use TS app."""
import http.client
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


# pylint: disable=R0903, R0902, R0912, R0915, R1702, C0302, C0301, W0108
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


def _have_user_properties_changed(name,
                                  display_name,
                                  email=None,
                                  ts_user_data=None):
    """
    Checks if the user properties have changed.

    @param namer: The LDAP name of the user.
    @param ldap_display_name: The LDAP display name of the user.
    @param ldap_email: The LDAP email of the user. Defaults to None.
    @param ts_user_data: The ThoughtSpot user data. Defaults to None.
    @return: True if the user properties have changed, False otherwise.
    """
    new_properties = {
        "name": name,
        "display_name": display_name,
        "email": email
    }

    ts_user_data = ts_user_data or {}
    return any(ts_user_data.get(prop) != value for prop, value in new_properties.items())


def _have_orgs_changed(org_ids, ts_user):
    """
    Checks if the organizations have changed.

    @param org_ids: The list of organization IDs.
    @param ts_user: The ThoughtSpot user data.
    @return: True if the organizations have changed, False otherwise.
    """
    return (ts_user and
            "orgs" in ts_user and
            set(org_ids) != {org['id'] for org in ts_user['orgs']})


def _get_params_for_create_user(name,
                                display_name,
                                usertype=None,
                                password=None,
                                email=None,
                                groups=None,
                                org_ids=None):
    """
    Gets the parameters for creating a user.

    @param name: The name of the user.
    @param display_name: The display name of the user.
    @param usertype: The type of the user. Defaults to None.
    @param password: The password of the user. Defaults to None.
    @param email: The email of the user. Defaults to None.
    @param groups: The groups of the user. Defaults to None.
    @param org_ids: The organization IDs of the user. Defaults to None.
    @return: The parameters for creating a user.
    """
    params = {
        "name": name,
        "displayname": display_name,
        "usertype": usertype,
        # If Password is not passed generate a random string as password.
        # Used in cases where authentication is done by an external agent.
        "password": password_gen() if password is None else password,
        "properties": json.dumps({"mail": email}) if email else None,
        "groups": json.dumps(groups) if groups else None,
        "orgids": json.dumps(org_ids) if org_ids else None
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    return params


def _get_params_for_update_user(user_identifier,
                                name=None,
                                display_name=None,
                                usertype=None,
                                email=None,
                                org_ids=None,
                                all_org_scope=False):
    """
    Gets the parameters for updating a user.

    @param user_identifier: The identifier of the user.
    @param name: The name of the user. Defaults to None.
    @param display_name: The display name of the user. Defaults to None.
    @param usertype: The type of the user. Defaults to None.
    @param email: The email of the user. Defaults to None.
    @param org_ids: The organization IDs of the user. Defaults to None.
    @param all_org_scope: Whether the user has all organization scope. Defaults to False.
    @return: The parameters for updating a user.
    """
    params = {
        "user_identifier": user_identifier,
        "name": name,
        "display_name": display_name,
        "account_type": usertype,
        "email": email,
        "org_identifiers": json.dumps(org_ids) if org_ids else None,
        "org_scope": "ALL" if all_org_scope else None # org override param
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    return params


def _have_group_properties_changed(name, display_name, grouptype, description, privileges, ts_group):
    """
    Checks if the properties of a group have changed.

    @param name (str): The new name of the group.
    @param display_name (str): The new display name of the group.
    @param grouptype (str): The new type of the group.
    @param description (str): The new description of the group.
    @param privileges (str): The new privileges of the group.
    @param ts_group (dict): The current properties of the group in a dictionary format.

    @return: True if any property has changed, False otherwise.
    """
    new_properties = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "type": grouptype,
        "privileges": privileges
    }

    return any(ts_group.get(prop) != value for prop, value in new_properties.items())


def _get_params_for_create_group(name, display_name, grouptype, description, privileges):
    """
    Constructs a dictionary of parameters for creating a group.

    @param name (str): The name of the group.
    @param display_name (str): The display name of the group.
    @param grouptype (str): The type of the group.
    @param description (str): The description of the group.
    @param privileges (list): The privileges of the group.

    @return: dict: A dictionary containing the parameters for creating a group.
    """
    params = {
        "name": name,
        "display_name": display_name,
        "grouptype": grouptype,
        "description": description,
        "privileges": json.dumps(privileges) if privileges else None
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    return params


def _get_params_for_update_group(description, display_name, group_identifier, grouptype,
                                 name, privileges):
    """
    Constructs a dictionary of parameters for updating a group.

    @param description (str): The new description of the group.
    @param display_name (str): The new display name of the group.
    @param group_identifier (str): The identifier of the group to be updated.
    @param grouptype (str): The new type of the group.
    @param name (str): The new name of the group.
    @param privileges (list): The new privileges of the group.

    @return: dict: A dictionary containing the parameters for updating a group.
    """
    params = {
        "group_identifier": group_identifier,
        "name": name,
        "display_name": display_name,
        "type": grouptype,
        "description": description,
        "privileges": json.dumps(privileges) if privileges else None
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    return params


class TSApiWrapper():
    """Wrapper class to log in and execute commands in TS system."""

    # URL end points used for various calls.
    SERVER_URL = "{hostport}/callosum/v1"

    # All org endpoints
    CREATE_USER = SERVER_URL + "/session/user/create"
    DELETE_USERS = SERVER_URL + "/session/user/deleteusers?orgId=-1"
    GET_MEMBERS = SERVER_URL + "/metadata/list"
    CREATE_ORG = SERVER_URL + "/tspublic/v1/org?orgScope=ALL"
    GET_ORGS = SERVER_URL + "/tspublic/v1/org/search?orgScope=ALL"
    SEARCH_USER = SERVER_URL + "/v2/users/search"
    UPDATE_USER = SERVER_URL + "/v2/users/{user_identifier}?operation={op}"

    LOGIN = SERVER_URL + "/session/login"
    INFO = SERVER_URL + "/session/info"
    UPSERT_GROUP = SERVER_URL + "/session/ldap/groups"
    CREATE_GROUP = SERVER_URL + "/session/group/create"
    DELETE_GROUPS = SERVER_URL + "/session/group/deletegroups"
    SWITCH_ORG = SERVER_URL + "/session/orgs"
    UPDATE_USERS_IN_GROUPS = SERVER_URL + "/session/group/updateusersingroup"
    UPDATE_GROUPS_IN_GROUPS = SERVER_URL + "/session/group/updategroupsingroup"
    LIST_USERS_IN_A_GROUP = SERVER_URL + "/session/group/listuser/{groupid}"
    LIST_GROUPS_IN_A_GROUP = SERVER_URL + "/session/group/listgroup/{groupid}"
    ADD_USER_TO_GROUP = SERVER_URL + "/session/group/adduser"
    ADD_GROUPS_TO_GROUP = SERVER_URL + "/session/group/addgroups"
    SEARCH_GROUP = SERVER_URL + "/v2/groups/search"
    UPDATE_GROUP = SERVER_URL + "/v2/users/{group_identifier}?operation={op}"

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
        self.session.headers = {
            "X-Requested-By": "ThoughtSpot",
            "User-Agent": "python/requests"
        }
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
                      "password": password,
                      "rememberme": "true"},
            )
            if response.status_code == http.client.OK:
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
            if response.status_code == http.client.OK:
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
    def search_group(
            self,
            group_identifier
    ):
        """
        Searches group in TS.
        @param group_identifier: group to be searched
        """
        params = {
            "group_identifier": group_identifier,
        }
        try:
            response = self.session.post(
                TSApiWrapper.SEARCH_GROUP.format(
                    hostport=self.hostport),
                data=params,
            )
            response_obj = json.loads(response.text)
            if len(response_obj["data"]) < 1:
                logging.debug("%s group doesn't exist",
                              group_identifier)
                return Result(Constants.OPERATION_FAILURE)
            logging.debug("%s group exists",
                          group_identifier)
            return Result(Constants.OPERATION_SUCCESS, response_obj)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

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
        search_group_result = self.search_group(name)
        is_new_group = search_group_result.status != Constants.OPERATION_SUCCESS

        try:
            if is_new_group:
                result = self.create_ts_group(name, display_name, grouptype, description, privileges)
            else:
                ts_group = search_group_result.data.get("data", [])[
                    0] if search_group_result.data.get(
                    "data") else None

                result = self.sync_existing_group(description, display_name, grouptype, name,
                                                  privileges, ts_group, upsert_group)
        except Exception as e:
            logging.error(e.message)
            result = Result(Constants.OPERATION_FAILURE, e)

        return result

    def create_ts_group(self, name, display_name, grouptype=None, description=None, privileges=None):
        """
        Creates a new group in the ThoughtSpot system.

        Parameters:
        name (str): The name of the new group.
        display_name (str): The display name of the new group.
        grouptype (str, optional): The type of the new group. Defaults to None.
        description (str, optional): The description of the new group. Defaults to None.
        privileges (str, optional): The privileges of the new group. Defaults to None.

        Returns:
        Result: A Result object indicating the success or failure of the operation.
        """
        params = _get_params_for_create_group(name, display_name, grouptype, description, privileges)

        try:
            response = self.session.post(
                TSApiWrapper.CREATE_GROUP.format(hostport=self.hostport),
                data=params,
            )

            if response.status_code == http.client.OK:
                logging.debug("New group %s added.", name)
                return Result(Constants.OPERATION_SUCCESS)

            logging.error("New group %s not added. Response: %s", name, response.text)
            return Result(Constants.OPERATION_FAILURE, {"response_status": response.status_code, "response_text": response.text})

        except requests.RequestException as e:
            logging.error("Request failed due to an error: %s", e)
            return Result(Constants.OPERATION_FAILURE, {"error": str(e)})

    def sync_existing_group(self, description, display_name, grouptype, name, privileges,
                            ts_group, upsert_group):
        """
        Sync existing group in the system. If upsert_group is True and there are changes in the group properties,
        it updates the group.

        :param description: Description of the group.
        :param display_name: Display name of the group.
        :param grouptype: Type of the group.
        :param name: Name of the group.
        :param privileges: Privileges of the group.
        :param ts_group: Existing group data.
        :param upsert_group: Flag to decide whether to update the group or not.
        :return: Result object with operation status and data.
        """
        result = Result(Constants.GROUP_ALREADY_EXISTS)
        should_update_group = _have_group_properties_changed(name, display_name, grouptype,
                                                             description, privileges, ts_group)
        if upsert_group and should_update_group:
            result = self.update_group(
                operation=Constants.Replace,
                group_identifier=name,
                name=name,
                display_name=display_name,
                grouptype=grouptype,
                description=description,
                privileges=privileges
            )
            if result.status == Constants.OPERATION_SUCCESS:
                result = Result(Constants.GROUP_ALREADY_EXISTS)

        return result

    @pre_check
    def update_group(
            self,
            operation,
            group_identifier,
            name=None,
            display_name=None,
            grouptype=None,
            description=None,
            privileges=None
    ):
        """
        Update group in the system.

        :param operation: Operation to be performed.
        :param group_identifier: Identifier of the group.
        :param name: Name of the group.
        :param display_name: Display name of the group.
        :param grouptype: Type of the group.
        :param description: Description of the group.
        :param privileges: Privileges of the group.
        :return: Result object with operation status and data.
        """
        params = _get_params_for_update_group(description, display_name, group_identifier,
                                              grouptype, name, privileges)

        try:
            response = self.session.put(
                TSApiWrapper.UPDATE_GROUP.format(
                    hostport=self.hostport,
                    group_identifier=group_identifier,
                    op=operation),
                data=params,
            )

            if response.status_code == http.client.NO_CONTENT:
                logging.debug("Updated existing group %s.\n"
                              "Updated attributes: %s", name, params)
                result = Result(Constants.OPERATION_SUCCESS)
            else:
                logging.error("Unable to update group %s.\n"
                              "Attributes attempted to be updated : %s.\n"
                              "Response %s", name, params, response.text)
                result = Result(Constants.OPERATION_FAILURE, response)

        except Exception as e:
            logging.error("Exception %s occurred with message: %s", type(e).__name__, e.message)
            result = Result(Constants.OPERATION_FAILURE, e)

        return result

    @pre_check
    def switch_org(self, org_id):
        """Switches org in user session.
           @param org_id: Id of the org to switch to
        """
        params = {"org": org_id}
        success_msg = "Successfully switched to {} org".format(org_id)
        failure_msg = "Failed to switch org."
        try:
            response = self.session.put(
                TSApiWrapper.SWITCH_ORG.format(hostport=self.hostport),
                data=params,
            )
            if response.status_code == http.client.NO_CONTENT:
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS)
            logging.debug(failure_msg)
            return Result(Constants.OPERATION_FAILURE)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def search_user(
            self,
            user_identifier
    ):
        """
        Searches user in TS.
        @param user_identifier: user to be searched
        """
        params = {
            "user_identifier": user_identifier,
            "org_scope": "ALL"
        }
        try:
            response = self.session.post(
                TSApiWrapper.SEARCH_USER.format(
                    hostport=self.hostport),
                data=params,
            )
            response_obj = json.loads(response.text)
            if len(response_obj["data"]) < 1:
                logging.debug("%s user doesn't exists",
                              user_identifier)
                return Result(Constants.OPERATION_FAILURE)
            logging.debug("%s user exists",
                          user_identifier)
            return Result(Constants.OPERATION_SUCCESS, response_obj)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def update_user_org(
            self,
            user_identifier,
            operation,
            org_identifiers=None,
    ):
        """
        Update User org assignment.
        @param user_identifier: user for which org is being updated.
        @param org_identifiers: org ids to be updated.
        @param operation: Operation type.
        """
        return self.update_user(operation=operation, user_identifier=user_identifier,
                                org_identifiers=org_identifiers, all_org_scope=True)

    @pre_check
    def sync_user(
            self,
            name,
            display_name,
            usertype=None,
            password=None,
            email=None,
            groups=None,
            upsert_user=False,
            org_ids=None,
            all_org_scope=False,
    ):
        """Sync user with TS.
           @param name: Name of the new user.
           @param display_name: Name to be displayed in TS system.
           @param usertype: Type of user to create.
           @param password: Password to be set for the user.
           @param email: Email to be set for user.
           @param groups: List of group ids the user belongs to.
           @param upsert_user: Upsert the users if true else only create.
           @param all_org_scope: if the sync call is in all org scope.
           @return: Result object with operation status and data.
        """
        search_user_result = self.search_user(name)
        is_new_user = search_user_result.status != Constants.OPERATION_SUCCESS

        if is_new_user:
            result = self.create_user(name, display_name, usertype, password, email, groups,
                                      org_ids, all_org_scope)
        else:
            ts_user = search_user_result.data.get("data", [])[0] if search_user_result.data.get(
                "data") else None
            update_result = self.sync_existing_user(name, display_name, email, usertype, org_ids,
                                                    all_org_scope, upsert_user, ts_user)
            if update_result.status in [Constants.OPERATION_SUCCESS, Constants.USER_ALREADY_EXISTS]:
                result = Result(Constants.USER_ALREADY_EXISTS)
            else:
                result = Result(Constants.OPERATION_FAILURE, update_result.data)

        return result

    def sync_existing_user(self, name, display_name, email, usertype, org_ids, all_org_scope,
                           upsert_user, ts_user):
        """
        Synchronizes an existing user with the provided properties.

        @param name: The name of the user.
        @param display_name: The display name of the user.
        @param email: The email of the user.
        @param usertype: The type of the user.
        @param org_ids: The organization IDs of the user.
        @param all_org_scope: Whether the user has all organization scope.
        @param upsert_user: Whether to upsert the user.
        @param ts_user: The ThoughtSpot user data.
        @return: The result of the synchronization operation.
        """
        should_update_properties = _have_user_properties_changed(name, display_name, email, ts_user)
        should_update_orgs = _have_orgs_changed(org_ids, ts_user)

        if upsert_user and should_update_properties:
            return self.update_user_properties(name, display_name, usertype, email, org_ids,
                                               all_org_scope)
        if should_update_orgs:
            return self.update_user_org(user_identifier=name,
                                        operation=Constants.Add,
                                        org_identifiers=org_ids)
        logging.debug("User %s already exists. Skipping update.", name)
        return Result(Constants.USER_ALREADY_EXISTS)

    @pre_check
    def update_user_properties(self, name, display_name, usertype, email, org_ids, all_org_scope):
        """
        Updates the properties of a user.

        @param name: The name of the user.
        @param display_name: The display name of the user.
        @param usertype: The type of the user.
        @param email: The email of the user.
        @param org_ids: The organization IDs of the user.
        @param all_org_scope: Whether the user has all organization scope.
        @return: The result of the update operation.
        """
        return self.update_user(operation=Constants.Add, user_identifier=name, name=name,
                                display_name=display_name, user_type=usertype, email=email,
                                org_identifiers=org_ids, all_org_scope=all_org_scope)

    @pre_check
    def create_user(
            self,
            name,
            display_name,
            usertype=None,
            password=None,
            email=None,
            groups=None,
            orgids=None,
            all_org_scope=False
    ):
        """
        Creates a user.
        @param name: Name of the new user.
        @param display_name: Name to be displayed in TS system.
        @param usertype: Type of user to create.
        @param password: Password to be set for the user.
        @param email: Email to be set for user.
        @param groups: List of group ids the user belongs to.
        @param orgids: orgs in which user belongs
        @param all_org_scope: if the call is in all org scope.
        """
        params = _get_params_for_create_user(name,
                                             display_name,
                                             usertype,
                                             password,
                                             email,
                                             groups,
                                             orgids)

        try:
            endpoint_url = (
                TSApiWrapper.CREATE_USER.format(hostport=self.hostport) + "?orgId=-1"
                if all_org_scope
                else TSApiWrapper.CREATE_USER.format(hostport=self.hostport)
            )
            response = self.session.post(
                endpoint_url,
                data=params,
            )
            if response.status_code == http.client.OK:
                logging.debug("New user %s added.", name)
                return Result(Constants.OPERATION_SUCCESS)
            logging.error("New user %s not added. Response %s", name,
                          response.text)
            return Result(Constants.OPERATION_FAILURE, response)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def update_user(
            self,
            operation,
            user_identifier,
            name=None,
            display_name=None,
            user_type=None,
            email=None,
            org_identifiers=None,
            all_org_scope=False,
    ):
        """
        Update orgs and/or properties for a user.
        @param operation: The operation to perform on the user (e.g., 'Add', 'Replace').
        @param user_identifier: The identifier of the user to update.
        @param name: Name of the new user.
        @param display_name: Name to be displayed in TS system.
        @param user_type: Type of user to create.
        @param email: Email to be set for user.
        @param org_identifiers: orgs in which user belongs
        @param all_org_scope: if the call is in all org scope.

        Returns: A Result object indicating the success or failure of the operation.
        """
        params = _get_params_for_update_user(user_identifier,
                                             name,
                                             display_name,
                                             user_type,
                                             email,
                                             org_identifiers,
                                             all_org_scope)
        try:
            response = self.session.put(
                TSApiWrapper.UPDATE_USER.format(
                    hostport=self.hostport,
                    user_identifier=user_identifier,
                    op=operation),
                data=params,
            )

            if response.status_code == http.client.NO_CONTENT:
                logging.debug("Updated existing user %s.\n"
                              "Updated attributes: %s", name, params)
                return Result(Constants.OPERATION_SUCCESS)

            logging.error("Unable to update user %s.\n"
                          "Attributes attempted to be updated : %s.\n"
                          "Response %s", name, params, response.text)
            return Result(Constants.OPERATION_FAILURE, response)

        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    @pre_check
    def create_org(self, name, description):
        """Creates new org and adds it to TS system.
           @param name: Name of the new org.
           @param description: description of the new org
           @return: Result object with operation status and data. Here data is
           set to None.
        """
        payload = {
            "name": name,
            "description": description,
            "orgScope": "All"
        }

        try:
            response = self.session.post(
                TSApiWrapper.CREATE_ORG.format(hostport=self.hostport),
                data=payload,
            )
            if response.status_code == http.client.OK:
                logging.debug("New org %s added.", name)
                return Result(Constants.OPERATION_SUCCESS)
            if response.status_code == http.client.CONFLICT:
                logging.debug("Org %s already exists.", name)
                return Result(Constants.ORG_ALREADY_EXISTS)
            logging.error("New org %s not added. Response %s", name,
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
        entity_list = list(filter(is_valid_uuid, entity_list))

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
            if response.status_code == http.client.NO_CONTENT:
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
    def _get_batched_entities(self, entity, offset, batchsize, allOrgs):
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
        if allOrgs:
            params["orgId"] = -1

        try:
            response = self.session.get(
                end_point.format(hostport=self.hostport), params=params)
            if response.status_code == http.client.OK:
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
                    if "orgIds" in item:
                        ent_property_obj = EntityProperty(
                            item["id"], item["name"], item["type"],
                            item["orgIds"]
                        )
                    else:
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
    def _list_entities(self, entity, batchsize, allOrgs):
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
            result_obj = self._get_batched_entities(entity, offset, batchsize, allOrgs)
            if result_obj.status == Constants.OPERATION_SUCCESS:
                ent_property_obj, is_last_batch = result_obj.data
                entity_list.extend(ent_property_obj)
                batch_count += 1
            else:
                batch_fail_msg = " Failed at batch number: {}".format(
                    batch_count
                    )
                #pylint:disable=logging-not-lazy
                logging.error(failure_msg + batch_fail_msg)
                return result_obj
        logging.debug(success_msg)
        return Result(Constants.OPERATION_SUCCESS, entity_list)

    def list_groups(self, allOrgs, batchsize=200):
        """Lists groups in TS system.
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        return self._list_entities(EntityType.GROUP, batchsize, allOrgs)

    def list_users(self, allOrgs, batchsize=200):
        """Lists users in TS system.
           @return: Result object with operation status and data. Here data is
           a list of (user/group)s in the TS system as EntityProperty objects.
        """
        return self._list_entities(EntityType.USER, batchsize, allOrgs)

    def list_orgs(self):
        """Lists orgs in TS system.
           @return: Result object with operation status and data. Here data is
           a list of orgs in the TS system
        """
        success_msg = "Successfully returning {} list.".format(EntityType.ORG)
        failure_msg = "Failed to procure {} list.".format(EntityType.ORG)
        try:
            response = self.session.post(
                TSApiWrapper.GET_ORGS.format(hostport=self.hostport)
            )
            if response.status_code == http.client.OK:
                response_obj = json.loads(response.text)
                org_list = []
                for item in response_obj:
                    assert "orgId" in item, "id not in item"
                    assert "orgName" in item, ("name not present for {}"
                                            .format(
                                                item["id"]
                                            ))
                    org_list.append(
                        EntityProperty(item["orgId"], item["orgName"]))
                logging.debug(success_msg)
                return Result(Constants.OPERATION_SUCCESS, org_list)
            logging.debug(failure_msg)
            return Result(Constants.OPERATION_FAILURE)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

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
            if response.status_code == http.client.NO_CONTENT:
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
        principalids = list(filter(is_valid_uuid, principalids))

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
            if response.status_code == http.client.NO_CONTENT:
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
        entity_list = list(filter(is_valid_uuid, entity_list))

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
            if response.status_code == http.client.NO_CONTENT:
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
            if response.status_code == http.client.OK:
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
            entity_list = self.list_groups(allOrgs=False)
        elif entity == EntityType.USER:
            entity_list = self.list_users(allOrgs=False)
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
