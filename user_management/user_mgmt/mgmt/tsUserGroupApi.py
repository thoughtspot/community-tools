from __future__ import print_function
import sys
import requests
import logging
import json
import time
import requests.packages.urllib3
from tsUserGroupApiDataModel import User, Group, UsersAndGroups
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

# -------------------------------------------------------------------------------------------------------------------

"""Classes to work with the TS public user and list APIs"""

# Helper functions. ----------------------------------------------------------------------


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


class UGJsonReader(object):
    """
    Reads a user / group structure from JSON and returns a UserGroup object.
    """

    def read_from_file(self, filename):
        """
        Reads the JSON data from a file.
        :param filename: Name of the file to read.
        :type filename: str
        :return: A UsersAndGroups container based on the JSON.
        :rtype: UsersAndGroups
        """
        with open(filename, "r") as json_file:
            json_list = json.load(json_file)
            return self.parse_json(json_list)

    def read_from_string(self, json_string):
        """
        Reads the users and groups from a JSON string.
        :param json_string: String containing the JSON.
        :type json_string: str
        :return: A UsersAndGroups container based on the JSON.
        :rtype: UsersAndGroups
        """
        json_list = json.loads(json_string)
        return self.parse_json(json_list)

    def parse_json(self, json_list):
        """
        Parses a JSON list and creates a UserAndGroup object.
        :param json_list: List of JSON objects that represent users and groups.
        :returns: A user and group container with the users and groups.
        :rtype: UsersAndGroups
        """
        auag = UsersAndGroups()
        for value in json_list:
            if str(value["principalTypeEnum"]).endswith("_USER"):
                user = User(
                    name=value.get("name", None),
                    display_name=value.get("displayName", None),
                    mail=value.get("mail", None),
                    group_names=value.get("groupNames", None),
                    visibility=value.get("visibility", None),
                    created=value.get("created", None),
                    id=value.get("id", None)
                )
                auag.add_user(user)
            else:
                group = Group(
                    name=value.get("name", None),
                    display_name=value.get("displayName", None),
                    description=value.get("description", None),
                    group_names=value.get("groupNames", None),
                    visibility=value.get("visibility", None),
                )
                auag.add_group(group)
        return auag


def api_call(f):
    """
    Makes sure to try to call login if not already logged in.  This only works for classes that extend BaseApiInterface.
    :param f: Function to decorate.
    :return: A new callable method that will try to login first.
    """

    def wrap(self, *args, **kwargs):
        """
        Verifies that the user is logged in and then makes the call.  Assumes something will be returned.
        :param self:  Instance calling a method.
        :param args:  Place arguments.
        :param kwargs: Key word arguments.
        :return: Whatever the wrapped method returns.
        """
        if not self.is_authenticated():
            self.login()
        return f(self, *args, **kwargs)

    return wrap


class BaseApiInterface(object):
    """
    Provides basic support for calling the ThoughtSpot APIs, particularly for logging in.
    """
    SERVER_URL = "{tsurl}/callosum/v1"

    def __init__(self, tsurl, username, password, disable_ssl=False):
        """
        Creates a new sync object and logs into ThoughtSpot
        :param tsurl: Root ThoughtSpot URL, e.g. http://some-company.com/
        :type tsurl: str
        :param username: Name of the admin login to use.
        :type username: str
        :param password: Password for admin login.
        :type password: str
        :param disable_ssl: If true, then disable SSL for calls.
        password for all users.  This can be significantly faster than individual passwords.
        """
        self.tsurl = tsurl
        self.username = username
        self.password = password
        self.cookies = None
        self.session = requests.Session()
        if disable_ssl:
            self.session.verify = False
        self.session.headers = {"X-Requested-By": "ThoughtSpot"}

    def login(self):
        """
        Log into the ThoughtSpot server.
        """
        url = self.format_url(SyncUserAndGroups.LOGIN_URL)
        response = self.session.post(
            url, data={"username": self.username, "password": self.password}
        )

        if response.status_code == 204:
            self.cookies = response.cookies
            logging.info("Successfully logged in as %s" % self.username)
        else:
            logging.error("Failed to log in as %s" % self.username)
            raise requests.ConnectionError(
                "Error logging in to TS (%d)" % response.status_code,
                response.text,
            )

    def is_authenticated(self):
        """
        Returns true if the session is authenticated
        :return: True if the session is authenticated.
        :rtype: bool
        """
        return self.cookies is not None

    def format_url(self, url):
        """
        Returns a URL that has the correct server.
        :param url: The URL template to add the server to.
        :type url: str
        :return: A URL that has the correct server info.
        :rtype: str
        """
        url = BaseApiInterface.SERVER_URL + url
        return url.format(tsurl=self.tsurl)


class SyncUserAndGroups(BaseApiInterface):
    """
    Synchronized with ThoughtSpot and also gets users and groups from ThoughtSpot.
    """

    LOGIN_URL = "/tspublic/v1/session/login"
    GET_ALL_URL = "/tspublic/v1/user/list"
    SYNC_ALL_URL = "/tspublic/v1/user/sync"
    UPDATE_PASSWORD_URL = "/tspublic/v1/user/updatepassword"
    DELETE_USERS_URL = "/session/user/deleteusers"
    DELETE_GROUPS_URL = "/session/group/deletegroups"
    USER_METADATA_URL = "/tspublic/v1/metadata/listobjectheaders?type=USER"
    GROUP_METADATA_URL = "/tspublic/v1/metadata/listobjectheaders?type=USER_GROUP"

    def __init__(
        self,
        tsurl,
        username,
        password,
        disable_ssl=False,
        global_password=False,
    ):
        """
        Creates a new sync object and logs into ThoughtSpot
        :param tsurl: Root ThoughtSpot URL, e.g. http://some-company.com/
        :param username: Name of the admin login to use.
        :param password: Password for admin login.
        :param disable_ssl: If true, then disable SSL for calls.
        :param global_password: If provided, will be passed to the sync call.  This is used to have a single
        password for all users.  This can be significantly faster than individual passwords.
        """
        super(SyncUserAndGroups, self).__init__(
            tsurl=tsurl,
            username=username,
            password=password,
            disable_ssl=disable_ssl,
        )
        self.global_password = global_password

    @api_call
    def get_all_users_and_groups(self):
        """
        Returns all users and groups from the server.
        :return: All users and groups from the server.
        :rtype: UsersAndGroups
        """

        url = self.format_url(SyncUserAndGroups.GET_ALL_URL)
        response = self.session.get(url, cookies=self.cookies)
        if response.status_code == 200:
            logging.info("Successfully got users and groups.")
            json_list = json.loads(response.text)
            reader = UGJsonReader()
            auag = reader.parse_json(json_list=json_list)
            return auag

        else:
            logging.error("Failed to get users and groups.")
            raise requests.ConnectionError(
                "Error getting users and groups (%d)" % response.status_code,
                response.text,
            )

    @api_call
    def get_user_metadata(self):
        """
        Returns a list of User objects based on the metadata.
        :return: A list of user objects.
        :rtype: list of User
        """
        url = self.format_url(SyncUserAndGroups.USER_METADATA_URL)
        response = self.session.get(url, cookies=self.cookies)
        users = []
        if response.status_code == 200:
            logging.info("Successfully got user metadata.")
            json_list = json.loads(response.text)
            for value in json_list:
                user = User(
                    name=value.get("name", None),
                    display_name=value.get("displayName", None),
                    mail=value.get("mail", None),
                    group_names=value.get("groupNames", None),
                    visibility=value.get("visibility", None),
                    created=value.get("created", None),
                    id=value.get("id", None)
                )
                users.append(user)
            return users

        else:
            logging.error("Failed to get user metadata.")
            raise requests.ConnectionError(
                "Error getting user metadata (%d)" % response.status_code,
                response.text,
                )

    @api_call
    def sync_users_and_groups(
        self, users_and_groups, apply_changes=True, remove_deleted=False
    ):
        """
        Syncs users and groups.
        :param users_and_groups: List of users and groups to sync.
        :type users_and_groups: UsersAndGroups
        :param apply_changes: If true, changes will be applied.  If not, then it just says what will happen.
        :type apply_changes: bool
        :param remove_deleted: Flag to removed deleted users.  If true, delete.
        :type remove_deleted: bool
        :returns: The response from the sync.
        """

        is_valid = users_and_groups.is_valid()
        if not is_valid[0]:
            # print("Invalid user and group structure.")
            raise Exception("Invalid users and groups")

        url = self.format_url(SyncUserAndGroups.SYNC_ALL_URL)

        logging.debug("calling %s" % url)
        json_str = users_and_groups.to_json()
        logging.debug("data == %s" % json_str)
        json.loads(json_str)  # do a load to see if it breaks due to bad JSON.

        tmp_file = "/tmp/ug.json.%d" % time.time()
        with open(tmp_file, "w") as out:
            out.write(json_str)

        params = {
            "principals": (tmp_file, open(tmp_file, "rb"), "text/json"),
            "applyChanges": json.dumps(apply_changes),
            "removeDeleted": json.dumps(remove_deleted),
        }

        if self.global_password:
            params["password"] = self.global_password

        response = self.session.post(url, files=params, cookies=self.cookies)

        if response.status_code == 200:
            logging.info("Successfully synced users and groups.")
            print(response.text.encode("utf-8"))
            return response

        else:
            logging.error("Failed synced users and groups.")
            print(response.text.encode("utf-8"))
            with open("ts_users_and_groups.json", "w") as outfile:
                outfile.write(json_str.encode("utf-8"))
            raise requests.ConnectionError(
                "Error syncing users and groups (%d)" % response.status_code,
                response.text,
            )

    @api_call
    def delete_users(self, usernames):
        """
        Deletes a list of users based on their user name.
        :param usernames: List of the names of the users to delete.
        :type usernames: list of str
        """

        # for each username, get the guid and put in a list.  Log errors for users not found, but don't stop.
        url = self.format_url(SyncUserAndGroups.USER_METADATA_URL)
        response = self.session.get(url, cookies=self.cookies)
        users = {}
        if response.status_code == 200:
            logging.info("Successfully got user metadata.")
            json_list = json.loads(response.text)
            for h in json_list:
                name = h["name"]
                id = h["id"]
                users[name] = id

            user_list = []
            for u in usernames:
                id = users.get(u, None)
                if not id:
                    eprint(
                        "WARNING:  user %s not found, not attempting to delete this user."
                        % u
                    )
                else:
                    user_list.append(id)

            if not user_list:
                eprint("No valid users to delete.")
                return

            url = self.format_url(SyncUserAndGroups.DELETE_USERS_URL)
            params = {"ids": json.dumps(user_list)}
            response = self.session.post(
                url, data=params, cookies=self.cookies
            )

            if response.status_code != 204:
                logging.error("Failed to delete %s" % user_list)
                raise requests.ConnectionError(
                    "Error getting users and groups (%d)"
                    % response.status_code,
                    response.text,
                )

        else:
            logging.error("Failed to get users and groups.")
            raise requests.ConnectionError(
                "Error getting users and groups (%d)" % response.status_code,
                response.text,
            )

    def delete_user(self, username):
        """
        Deletes the user with the given username.
        :param username: The name of the user.
        :type username: str
        """
        self.delete_users([username])  # just call the list method.

    @api_call
    def delete_groups(self, groupnames):
        """
        Deletes a list of groups based on their group name.
        :param groupnames: List of the names of the groups to delete.
        :type groupnames: list of str
        """

        # for each groupname, get the guid and put in a list.  Log errors for groups not found, but don't stop.
        url = self.format_url(SyncUserAndGroups.GROUP_METADATA_URL)
        response = self.session.get(url, cookies=self.cookies)
        groups = {}
        if response.status_code == 200:
            logging.info("Successfully got group metadata.")
            json_list = json.loads(response.text)
            # for h in json_list["headers"]:
            for h in json_list:
                name = h["name"]
                id = h["id"]
                groups[name] = id

            group_list = []
            for u in groupnames:
                id = groups.get(u, None)
                if not id:
                    eprint(
                        "WARNING:  group %s not found, not attempting to delete this group."
                        % u
                    )
                else:
                    group_list.append(id)

            if not group_list:
                eprint("No valid groups to delete.")
                return

            url = self.format_url(SyncUserAndGroups.DELETE_GROUPS_URL)
            params = {"ids": json.dumps(group_list)}
            response = self.session.post(
                url, data=params, cookies=self.cookies
            )

            if response.status_code != 204:
                logging.error("Failed to delete %s" % group_list)
                raise requests.ConnectionError(
                    "Error getting groups and groups (%d)"
                    % response.status_code,
                    response.text,
                )

        else:
            logging.error("Failed to get users and groups.")
            raise requests.ConnectionError(
                "Error getting users and groups (%d)" % response.status_code,
                response.text,
            )

    def delete_group(self, groupname):
        """
        Deletes the group with the given groupname.
        :param groupname: The name of the group.
        :type groupname: str
        """
        self.delete_groups([groupname])  # just call the list method.

    @api_call
    def update_user_password(self, userid, currentpassword, password):
        """
        Updates the password for a user.
        :param userid: User id for the user to change the password for.
        :type userid: str
        :param currentpassword: Password for the logged in user with admin privileges.
        :type currentpassword: str
        :param password: New password for the user.
        :type password: str
        """

        url = self.format_url(SyncUserAndGroups.UPDATE_PASSWORD_URL)
        params = {
            "name": userid,
            "currentpassword": currentpassword,
            "password": password,
        }

        response = self.session.post(url, data=params, cookies=self.cookies)

        if response.status_code == 204:
            logging.info("Successfully updated password for %s." % userid)
        else:
            logging.error("Failed to update password for %s." % userid)
            raise requests.ConnectionError(
                "Error (%d) updating user password for %s:  %s"
                % (response.status_code, userid, response.text)
            )


class Privileges(object):
    """
    Contains the various privileges that groups can have.
    """
    IS_ADMINSTRATOR = "ADMINISTRATION"
    CAN_UPLOAD_DATA = "USERDATAUPLOADING"
    CAN_DOWNLOAD_DATA = "DATADOWNLOADING"
    CAN_SHARE_WITH_ALL = "SHAREWITHALL"
    CAN_MANAGE_DATA = "DATAMANAGEMENT"
    CAN_SCHEDULE_PINBOARDS = "JOBSCHEDULING"
    CAN_USE_SPOTIQ = "A3ANALYSIS"
    CAN_ADMINISTER_RLS = "BYPASSRLS"
    CAN_AUTHOR = "AUTHORING"
    CAN_MANAGE_SYSTEM = "SYSTEMMANAGEMENT"


class SetGroupPrivilegesAPI(BaseApiInterface):

    # Note that some of these URLs are not part of the public API and subject to change.
    METADATA_LIST_URL = "/tspublic/v1/metadata/listobjectheaders?type=USER_GROUP"
    METADATA_DETAIL_URL = "/metadata/detail/{guid}?type=USER_GROUP"

    ADD_PRIVILEGE_URL = "/tspublic/v1/group/addprivilege"
    REMOVE_PRIVILEGE_URL = "/tspublic/v1/group/removeprivilege"

    def __init__(self, tsurl, username, password, disable_ssl=False):
        """
        Creates a new sync object and logs into ThoughtSpot
        :param tsurl: Root ThoughtSpot URL, e.g. http://some-company.com/
        :param username: Name of the admin login to use.
        :param password: Password for admin login.
        :param disable_ssl: If true, then disable SSL for calls.
        """
        super(SetGroupPrivilegesAPI, self).__init__(
            tsurl=tsurl,
            username=username,
            password=password,
            disable_ssl=disable_ssl,
        )

    @api_call
    def get_privileges_for_group(self, group_name):
        """
        Gets the current privileges for a given group.
        :param group_name:  Name of the group to get privileges for.
        :returns: A list of privileges.
        :rtype: list of str
        """
        url = self.format_url(
            SetGroupPrivilegesAPI.METADATA_LIST_URL
        ) + "&pattern=" + group_name
        response = self.session.get(url, cookies=self.cookies)
        if response.status_code == 200:  # success
            results = json.loads(response.text)
            try:
                group_id = results[0][
                    "id"
                ]  # should always be present, but might want to add try / catch.
                detail_url = SetGroupPrivilegesAPI.METADATA_DETAIL_URL.format(
                    guid=group_id
                )
                detail_url = self.format_url(detail_url)
                detail_response = self.session.get(
                    detail_url, cookies=self.cookies
                )
                if detail_response.status_code == 200:  # success
                    privileges = json.loads(detail_response.text)["privileges"]
                    return privileges

                else:
                    logging.error(
                        "Failed to get privileges for group %s" % group_name
                    )
                    raise requests.ConnectionError(
                        "Error (%d) setting privileges for group %s.  %s"
                        % (response.status_code, group_name, response.text)
                    )

            except Exception:
                print("Error getting group details.")
                raise

        else:
            logging.error("Failed to get privileges for group %s" % group_name)
            raise requests.ConnectionError(
                "Error (%d) setting privileges for group %s.  %s"
                % (response.status_code, group_name, response.text)
            )

    @api_call
    def add_privilege(self, groups, privilege):
        """
        Adds a privilege to a list of groups.
        :param groups List of groups to add the privilege to.
        :type groups: list of str
        :param privilege: Privilege being set.
        :type privilege: str
        """

        url = self.format_url(SetGroupPrivilegesAPI.ADD_PRIVILEGE_URL)

        params = {"privilege": privilege, "groupNames": json.dumps(groups)}
        response = self.session.post(url, files=params, cookies=self.cookies)

        if response.status_code == 204:
            logging.info(
                "Successfully added privilege %s for groups %s."
                % (privilege, groups)
            )
        else:
            logging.error(
                "Failed to add privilege %s for groups %s."
                % (privilege, groups)
            )
            raise requests.ConnectionError(
                "Error (%d) adding privilege %s for groups %s.  %s"
                % (response.status_code, privilege, groups, response.text)
            )

    @api_call
    def remove_privilege(self, groups, privilege):
        """
        Removes a privilege to a list of groups.
        :param groups List of groups to add the privilege to.
        :type groups: list of str
        :param privilege: Privilege being removed.
        :type privilege: str
        """

        url = self.format_url(SetGroupPrivilegesAPI.REMOVE_PRIVILEGE_URL)

        params = {"privilege": privilege, "groupNames": json.dumps(groups)}
        response = self.session.post(url, files=params, cookies=self.cookies)

        if response.status_code == 204:
            logging.info(
                "Successfully removed privilege %s for groups %s."
                % (privilege, groups)
            )
        else:
            logging.error(
                "Failed to remove privilege %s for groups %s."
                % (privilege, groups)
            )
            raise requests.ConnectionError(
                "Error (%d) removing privilege %s for groups %s.  %s"
                % (response.status_code, privilege, groups, response.text)
            )


class TransferOwnershipApi(BaseApiInterface):

    TRANSFER_OWNERSHIP_URL = "{tsurl}/tspublic/v1/user/transfer/ownership"

    def __init__(self, tsurl, username, password, disable_ssl=False):
        """
        Creates a new sync object and logs into ThoughtSpot
        :param tsurl: Root ThoughtSpot URL, e.g. http://some-company.com/
        :param username: Name of the admin login to use.
        :param password: Password for admin login.
        :param disable_ssl: If true, then disable SSL for calls.
        """
        super(TransferOwnershipApi, self).__init__(
            tsurl=tsurl,
            username=username,
            password=password,
            disable_ssl=disable_ssl,
        )

    @api_call
    def transfer_ownership(self, from_username, to_username):
        """
        Transfer ownersip of all objects from one user to another.
        :param from_username: User name for the user to change the ownership for.
        :type from_username: str
        :param to_username: User name for the user to change the ownership to.
        :type to_username: str
        """

        url = self.format_url(TransferOwnershipApi.TRANSFER_OWNERSHIP_URL)
        url = url + "?fromUserName=" + from_username + "&toUserName=" + to_username
        response = self.session.post(url, cookies=self.cookies)

        if response.status_code == 204:
            logging.info(
                "Successfully transferred ownership to %s." % to_username
            )
        else:
            logging.error("Failed to transfer ownership to %s." % to_username)
            raise requests.ConnectionError(
                "Error (%d) transferring  ownership to %s:  %s"
                % (response.status_code, to_username, response.text)
            )

