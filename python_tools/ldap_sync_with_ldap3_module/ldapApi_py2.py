#!/usr/bin/env python
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Classes and Functions to log into and use LDAP System."""

import logging
import re
from functools import wraps

import ldap
from entityClasses import EntityType
from globalClasses import Constants, Result


def pre_check(function):
    """A decorator to check for user authentication before executing the given
    command.

    :param function: Function to apply the wrapper around.
    :return: An entity where authentication check happens before the
    actual function call.
    """

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        """Wrapper to wrap the function in.

        :param self: The self pointer to class instance.
        :param *args: List of arguments being passed to the fucntion which
        is being wrapped.
        :param **kwargs: Dictionary being passed to the fucntion which is
        being wrapped.
        :return: Returns the original function.
        """
        if not self._is_authenticated():
            logging.error(LDAPApiWrapper.USER_AUTHENTICATION_FAILURE)
            return Result(Constants.AUTHENTICATION_FAILURE)
        return function(self, *args, **kwargs)

    return wrapper


class LDAPApiWrapper(object):
    """Wrapper class to connect to and fetch information from LDAP System."""

    class User(object):
        """Entity class to hold most important details of User object."""

        def __init__(self, dn, name, display_name, email=None):
            """Constructor.

            :param dn: Distinguished name.
            :param name: Unique name property of the user.
            :param display_name: Display name for the user.
            :param email: Email of the user.
            """
            self.type = EntityType.USER
            self.dn = dn
            self.name = name
            self.display_name = display_name
            self.email = email



        def __repr__(self):
            prn = "Type: {} DN: {} Name: {} DisplayName: {} email: {}"
            return prn.format(
                self.type, self.dn, self.name, self.display_name, self.email
            )

    class Group(object):
        """Entity class to hold most important details of Group object."""

        def __init__(self, dn, name, display_name, members):
            """Constructor.

            :param dn: Distinguished name.
            :param name: Unique name property of the group.
            :param display_name: Display name property of the group.
            :param members: Distinguished name list of members of the group.
            """
            self.type = EntityType.GROUP
            self.dn = dn
            self.name = name
            self.display_name = display_name
            self.members = members

        def __repr__(self):
            prn = "Type: {} DN: {} Name: {} DisplayName: {} Members: {}"
            return prn.format(
                self.type, self.dn, self.name, self.display_name, self.members
            )

    # LdapType Strings
    OPEN_LDAP = "openldap"
    AD = "AD"

    # Filter Strings
    USER_FILTER_OPEN_LDAP = "(objectClass=inetOrgPerson)"
    GROUP_FILTER_OPEN_LDAP = \
        "(|(objectClass=group)(objectClass=groupOfUniqueNames))"
    USER_FILTER_AD = "(|(objectClass=user)(objectClass=person))"
    GROUP_FILTER_AD = "(|(objectClass=group)(objectClass=container)" \
                      "(objectClass=groupOfUniqueNames))"
    FILTER_ADD = "(&{}{})"
    FILTER_OR = "(|{}{})"
    ATTR_UPN = "userPrincipalName"
    ATTR_NAME = "name"
    ATTR_DISPLAY_NAME = "displayName"
    ATTR_CN = "cn"
    ATTR_EMAIL = "mail"
    ATTR_MEMBER = "member"
    ATTR_CATRECID = "catrecid"
    ATTR_UM = "uniqueMember"
    LIST_MEM_FILTER = "(cn=*)"

    #AD Attribute settings
    AD_ATTR_UID = "sAMAccountName"

    # OPEN_LDAP Attribute settings
    OPEN_LDAP_ATTR_UID = "uid"

    # Error message constants
    USER_AUTHENTICATION_FAILURE = "User not authenticated."
    USER_AUTHENTICATION_SUCCESS = "User successfully authenticated."
    UNKNOWN_ENTITY_TYPE = "Unknown entity type."

    def __init__(self):
        """Constructor."""
        # As we allow both ldap and ldaps, we want to avoid self signed
        # certificates during ldaps authentication.
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        self.connection_pool = {}

    def __del__(self):
        """On destructor call unbind and clear connection pool."""
        for (_, conn) in self.connection_pool.items():
            if conn:
                conn.unbind_s()
        self.connection_pool.clear()

    def bind_to(self, hostport, username, password):
        """Bind.

        :param hostport: HostPort to connect to.
        :param username: Username to use.
        :param password: Password to use.
        """
        conn = ldap.initialize(hostport)
        conn.protocol_version = 3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
        conn.simple_bind_s(username, password)
        return conn

    def get_hostport_from_dn(self, dn):
        """Try deriving the subdomain to connect to by using the DN.

        :param dn: Distinguished name of the ldap object.
        """
        domain = self.fetch_domain_name_from_dn(dn)
        hostport = self.__protocol + domain[1:]
        return hostport.lower()

    def get_connection_to(self, hostport):
        """Get connection to a specific domain/sub-domain from the pool.

        :param hostport: HostPort to connect to.
        """
        if not hostport.startswith("ldap"):
            # Try deriving hostport.
            hostport = self.get_hostport_from_dn(hostport)

        # If connection not in pool create the same in pool.
        if hostport not in self.connection_pool:
            try:
                conn = self.bind_to(hostport, self.__username, self.__password)
                self.connection_pool[hostport] = conn
                logging.debug("Binding to %s", hostport)
            except:
                # Use the default connection if there is an issue connecting to
                # sub-domain.
                self.connection_pool[hostport] = None
                logging.debug("Failed to bind to %s.", hostport)

        # Implementing it this way will ensure we do not try an already failed
        # connection again and hence prevent an unnecessary network call to AD.
        if self.connection_pool[hostport]:
            return self.connection_pool[hostport]
        logging.debug("Returning default connection for %s.", hostport)
        return self.connection_pool["default"]

    def login(self, hostport, username, password):
        """Logs the user into LDAP system.

        :param hostport: Complete URL of the LDAP System to connect to
        ldap(s)://<host>:<port>
        :param username: Username for the user.
        :param password: Password for the user.
        :return: Result object with operation status and data. Here data is
        set to None.
        """
        # Store for future use.
        if hostport.startswith("ldap://"):
            self.__protocol = "ldap://"
        else:
            self.__protocol = "ldaps://"
        self.__username = username
        self.__password = password

        try:
            conn = self.bind_to(hostport, self.__username, self.__password)
            logging.debug(LDAPApiWrapper.USER_AUTHENTICATION_SUCCESS)
            self.connection_pool["default"] = conn
            return Result(Constants.OPERATION_SUCCESS)
        except ldap.INVALID_CREDENTIALS as e:
            logging.error("Invalid credentials provided.")
            return Result(Constants.OPERATION_FAILURE, e)
        except ldap.SERVER_DOWN as e:
            logging.error("Server down.")
            return Result(Constants.OPERATION_FAILURE, e)
        except ldap.LDAPError as e:
            logging.error("LDAP connection error.")
            return Result(Constants.OPERATION_FAILURE, e)
        except Exception as e:
            logging.error(e.message)
            return Result(Constants.OPERATION_FAILURE, e)

    def _is_authenticated(self):
        """Tells us if the user is authenticated or not.

        :return: Bool value to signify user logged in status.
        """
        return len(self.connection_pool) != 0

    # List Functions #

    def _sanitize_filters(self, filter_str):
        """Method to sanitize LDAP filter string.

        :param filter_str: Filter string to sanitize.
        """
        # Remove special characters like backslash
        filter_str = filter_str.replace("\\", "")
        # Properly escape paranthesis.
        filter_str = re.sub(r"\((\w+)\)", r"\(\1\)", filter_str)
        return filter_str

    @pre_check
    def list_users(
        self,
        basedn,
        ldap_type,
        user_identifier,
        email_identifier,
        user_display_name_identifier,
        scope=None,
        filter_str=None,
        log_entities=True,
        authdomain_identifier=None,
        member_str=None
    ):
        """Fetches users present in LDAP System.

        :param basedn: Distinguished name for the base in LDAP System.
        :param scope: Scope to limit the search to (0:base, 1:one, 2:tree).
        :param filter_str: Filter string to apply to search.
        :param log_entities: Flag if entity logging should be done.
        :param user_identifier: Identifier key to be used for user name.
        :param authdomain_identifier: Custom domain name to be appended to
        user identifier key for user name.
        :param email_identifier: Identifier key to be used for user email.
        :param user_display_name_identifier: Identifier key to be used for
        displaying user's name
        :return: Result object with operation status and data. Here data is
        a list of User objects present in LDAP System.
        """
        if LDAPApiWrapper.OPEN_LDAP == ldap_type:
            if user_identifier is None:
                attr_uid = LDAPApiWrapper.OPEN_LDAP_ATTR_UID
            else:
                attr_uid = user_identifier
            user_filter = LDAPApiWrapper.USER_FILTER_OPEN_LDAP
        else:
            attr_uid = LDAPApiWrapper.AD_ATTR_UID
            user_filter = LDAPApiWrapper.USER_FILTER_AD

        attr_list = [
            attr_uid,
            LDAPApiWrapper.ATTR_UPN,
            LDAPApiWrapper.ATTR_NAME,
            LDAPApiWrapper.ATTR_DISPLAY_NAME,
            LDAPApiWrapper.ATTR_CN,
            LDAPApiWrapper.ATTR_EMAIL,
            LDAPApiWrapper.ATTR_CATRECID
        ]

        entity_list = []

        # Add user_identifier to attr_list if not already in retrieval list.
        if user_identifier is not None and user_identifier not in attr_list:
            attr_list.append(user_identifier)
        # Add email_identifier to attr_list if not already in retrieval list.
        if email_identifier is not None and email_identifier not in attr_list:
            attr_list.append(email_identifier)
        # Add display_name_identifier to attr_list if not already
        # in retrieval list.
        if user_display_name_identifier is not None:
            if user_display_name_identifier not in attr_list:
                attr_list.append(user_display_name_identifier)


        if scope is None:
            scope = ldap.SCOPE_SUBTREE

        # If filter string is not specified we use default user filters.
        # If a filter is being provided we need to stitch together the
        # user given filter with default filters to fetch specific users.
        if filter_str is None:
            filter_str = user_filter
        else:
            filter_str = LDAPApiWrapper.FILTER_ADD.format(
                user_filter, filter_str
            )

        filter_str = self._sanitize_filters(filter_str)

        if log_entities:
            logging.debug("Base DN: %s", basedn)
            logging.debug("Filter String: %s", filter_str)

        try:
            item_list = self.get_connection_to(basedn).search_s(
                basedn, int(scope), filter_str, attr_list
            )
        except Exception as e:
            return Result(Constants.OPERATION_FAILURE, e)

        msg = "List of DNs retrieved from LDAP server:\n"
        for dn, entry in item_list:
            # Skip entities which are None
            #
            # NOTE: This becomes necessary because when we get the list of
            # entities back we also have a reference entity describing where
            # it was fetched from which has a None value for dn.
            #
            # This filtering helps us skip these metadata information.
            if dn is None:
                continue
            msg += "==> [{},{}]\n".format(dn, entry)

            name = None

            # Entity specific attributes and handling of unique name attribute
            # if defaults are not present.
            # Default attributes to be used as unique names.
            if user_identifier in entry:
                name = (
                    entry[user_identifier][0].decode('utf-8')
                    + self._get_domain_name(
                        dn,
                        user_identifier,
                        authdomain_identifier
                    )
                )
                msg += (
                    "Using `" + user_identifier + "` for"
                    + " constructing unique name.\n"
                )

            elif LDAPApiWrapper.AD_ATTR_UID in entry:
                # If userPrincipalName not present then use sAMAccountName to
                # construct user name.
                # For sAMAccountName, also append domain name in user name.
                name = (
                    entry[LDAPApiWrapper.AD_ATTR_UID][0]
                    + self._get_domain_name(
                        dn,
                        LDAPApiWrapper.AD_ATTR_UID,
                        authdomain_identifier
                    )
                )
                msg += (
                    "Using `sAMAccountName` for"
                    + " constructing unique name.\n"
                )

            if entry.has_key(user_display_name_identifier):
                display_name = entry[user_display_name_identifier][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_DISPLAY_NAME):
                display_name = entry[LDAPApiWrapper.ATTR_DISPLAY_NAME][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_NAME):
                display_name = entry[LDAPApiWrapper.ATTR_NAME][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_CN):
                display_name = entry[LDAPApiWrapper.ATTR_CN][0]
            else:
                display_name = name

            email = None
            if email_identifier in entry:
                email = entry[email_identifier][0]

            # Unique name is required to login. Hence any user without
            # a userPrincipalName/sAMAccountName would not be created
            # as such a user cannot log into the system.
            # NOTE: Should not be combined with previous if/elif as that
            # would miss the case where one of them is present but is None.
            if name is None:
                msg += "No unique name found for entry\n"
                continue

            entity_list.append(
                LDAPApiWrapper.User(dn, name, display_name, email)
            )

        if log_entities:
            logging.debug(msg)

        return Result(Constants.OPERATION_SUCCESS, entity_list)

    @pre_check
    def list_groups(
        self,
        basedn,
        ldap_type,
        user_identifier,
        group_display_name_identifier,
        scope=None,
        filter_str=None,
        log_entities=True,
        member_str=None
    ):
        """Fetches groups present in LDAP System.

        :param basedn: Distinguished name for the base in LDAP System.
        :param scope: Scope to limit the search to (0:base, 1:one, 2:tree).
        :param filter_str: Filter string to apply to search.
        :param log_entities: Flag if entity logging should be done.
        :param group_display_name_identifier key is to be used for displaying
        group name
        :return: Result object with operation status and data. Here data is
        a list of Group objects present in LDAP System.
        """
        if LDAPApiWrapper.OPEN_LDAP == ldap_type:
            if user_identifier is None:
                attr_uid = LDAPApiWrapper.OPEN_LDAP_ATTR_UID
            else:
                attr_uid = user_identifier
            common_attrs = [
                attr_uid,
                LDAPApiWrapper.ATTR_UPN,
                LDAPApiWrapper.ATTR_NAME,
                LDAPApiWrapper.ATTR_DISPLAY_NAME,
                LDAPApiWrapper.ATTR_CN,
                LDAPApiWrapper.ATTR_MEMBER,
                LDAPApiWrapper.ATTR_UM
            ]
            group_filter = LDAPApiWrapper.GROUP_FILTER_OPEN_LDAP
        else:
            common_attrs = [
                LDAPApiWrapper.AD_ATTR_UID,
                LDAPApiWrapper.ATTR_UPN,
                LDAPApiWrapper.ATTR_NAME,
                LDAPApiWrapper.ATTR_DISPLAY_NAME,
                LDAPApiWrapper.ATTR_CN,
                LDAPApiWrapper.ATTR_MEMBER,
                LDAPApiWrapper.ATTR_UM
            ]
            group_filter = LDAPApiWrapper.GROUP_FILTER_AD
        entity_list = []

        if scope is None:
            scope = ldap.SCOPE_SUBTREE
        if member_str is None:
            member_str = LDAPApiWrapper.ATTR_MEMBER

        # If filter string is not specified we use default group filters.
        # If a filter is being provided we need to stitch together the
        # user given filter with default filters to fetch specific groups.
        if filter_str is None:
            filter_str = group_filter
        else:
            filter_str = LDAPApiWrapper.FILTER_ADD.format(
                group_filter, filter_str
            )

        filter_str = self._sanitize_filters(filter_str)

        if log_entities:
            logging.debug("Base DN: %s", basedn)
            logging.debug("Filter String: %s", filter_str)

        item_list = []
        window = 999
        total_lim = 10000
        for ind in range(0, total_lim, window + 1):
            st, en = ind, ind + window
            memberrange = "member;range={}-{}".format(st, en)
            attr_list = common_attrs + [memberrange]

            if group_display_name_identifier is not None:
                if group_display_name_identifier is not attr_list:
                    attr_list.append(group_display_name_identifier)

            if log_entities:
                logging.debug(
                    "Basedn %s with member range %s filter_str %s.",
                    basedn,
                    memberrange,
                    filter_str,
                )
            try:
                i_list = self.get_connection_to(basedn).search_s(
                    basedn, int(scope), filter_str, attr_list
                )
                if not i_list:
                    if log_entities:
                        logging.debug(
                            "Empty return for "
                            + "basedn %s with member range %s filter_str %s.",
                            basedn,
                            memberrange,
                            filter_str,
                        )
                    break
                item_list.extend(i_list)
            except Exception as e:
                if log_entities:
                    logging.debug(
                        "Threw exception for "
                        + "basedn %s with member range %s filter_str %s.",
                        basedn,
                        memberrange,
                        filter_str,
                    )
                    logging.error(e)
                break

        valid_dn_cnt = 0
        none_dn_cnt = 0
        msg = "List of DNs retrieved from LDAP server:\n"
        for dn, entry in item_list:
            # Skip entities which are None
            #
            # NOTE: This becomes necessary because when we get the list of
            # entities back we also have a reference entity describing where
            # it was fetched from which has a None value for dn.
            #
            # This filtering helps us skip these metadata information.
            if dn is None:
                none_dn_cnt += 1
                continue
            msg += "==> [{},{}]\n".format(dn, entry)
            valid_dn_cnt += 1

            # Entity specific attributes and handling of unique name attribute
            # if defaults are not present.
            name = ".".join(
                self._fetch_components_from_dn(dn)[0]
            ) + self.fetch_domain_name_from_dn(dn)
            # If name follows a consistant rule then we can use patterns
            # to create good looking display names.
            if entry.has_key(group_display_name_identifier):
                display_name = entry[group_display_name_identifier][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_DISPLAY_NAME):
                display_name = entry[LDAPApiWrapper.ATTR_DISPLAY_NAME][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_NAME):
                display_name = entry[LDAPApiWrapper.ATTR_NAME][0]
            elif entry.has_key(LDAPApiWrapper.ATTR_CN):
                display_name = entry[LDAPApiWrapper.ATTR_CN][0]
            else:
                display_name = dn

            # Populate member information.
            member = []
            for member_key in entry:
                if member_key.startswith(member_str):
                    member.extend(entry[member_key])
            if not member:
                logging.debug("Group DN(%s) has no key: %s.", dn, member_str)

            entity_list.append(
                LDAPApiWrapper.Group(dn, name, display_name, member)
            )

        if log_entities:
            logging.debug(
                "valid_dn_cnt %d none_dn_cnt %d procured",
                valid_dn_cnt,
                none_dn_cnt)
            logging.debug(msg)

        # Ensure we send back unique entities with all members and not
        # duplicate entities with members in parts.
        entity_map = {}
        for entity in entity_list:
            if entity.dn in entity_map:
                entity_map[entity.dn].members.extend(entity.members)
            else:
                entity_map[entity.dn] = entity

        return Result(Constants.OPERATION_SUCCESS, entity_map.values())

    # Helper Functions #

    def _get_domain_name(self, dn, user_identifier, authdomain_identifier=None):
        """Fetches domain name for the LDAP entity.

        :param dn: Distinguished Name
        :param user_identifier: Identifier key used for user name.
        :param authdomain_identifier: Override domain name.
        :return: Domain name to be appended for the LDAP entity.
        """
        # Add authdomain_identifier to user name if provided
        # If not utilize inferred domain name, if 'sAMAccountName' is
        # the user identifier
        name = ''
        if authdomain_identifier is not None:
            name += '@' + authdomain_identifier
        elif user_identifier == LDAPApiWrapper.AD_ATTR_UID:
            name += self.fetch_domain_name_from_dn(dn)
        return name

    def _fetch_components_from_dn(self, dn):
        """Fetches components from DN.

        :param dn: Distinguished Name
        :return: DC and non DC components separately.
        """
        components = ldap.dn.explode_dn(dn)
        non_dc, dc = [], []
        for item in components:
            if item.lower().startswith("dc"):
                dc.append(item)
            else:
                non_dc.append(item)
        return non_dc, dc

    def fetch_domain_name_from_dn(self, dn):
        """Fetches domain name for the LDAP entity.

        :param dn: Distinguished name for the entity.
        :return: Domain name for the entity.
        """
        _, domain_components = self._fetch_components_from_dn(dn)
        domain_name = []
        for item in domain_components:
            _, val = item.split("=")
            domain_name.append(val)
        return "@" + ".".join(domain_name)

    @pre_check
    def list_member_dns(self, basedn, scope=None, filter_str=None):
        """Fetches list of DNs of member entities recursively. This includes
        both users and groups.

        :param basedn: Distinguished name for the base in LDAP System.
        :param filter_str: String to filter the Distinguished Names.
        :return: Result object with operation status and data. Here data is
        a list of member DNs.
        """
        entity_list = []
        attr_list = []

        if scope is None:
            scope = ldap.SCOPE_SUBTREE
        # if filter_str is None:
        #     filter_str = "(cn=*)"
        if filter_str is None:
            filter_str = LDAPApiWrapper.LIST_MEM_FILTER

        logging.debug("Base DN: %s", basedn)
        logging.debug("Filter String: %s", filter_str)
        try:
            item_list = self.get_connection_to(basedn).search_s(
                basedn, int(scope), filter_str, attr_list
            )
        except Exception as e:
            return Result(Constants.OPERATION_FAILURE, e)

        msg = "List of DNs in Base DN for input filter:\n"
        for dn, _ in item_list:
            if dn:
                entity_list.append(dn)
                msg += "==> [{}]\n".format(dn)
        logging.debug(msg)
        return Result(Constants.OPERATION_SUCCESS, entity_list)

    def dn_to_obj(
        self,
        basedn,
        ldap_type=None,
        user_identifier=None,
        email_identifier=None,
        user_display_name_identifier=None,
        group_display_name_identifier=None,
        authdomain_identifier=None,
        member_str=None,
        log_entities=True
    ):
        """Fetches if the node represented by basedn is of type user or group.

        :param basedn: Distinguished name for the base in LDAP System.
        :param log_entities: Flag if entity logging should be done.
        :param user_identifier: Identifier key to be used for user name.
        :param authdomain_identifier: Custom domain name to be appended to
        user identifier key for user name.
        :param email_identifier: Identifier key to be used for user email.
        :param user_display_name_identifier: Identifier key to be used for
        displaying user's name
        :param group_display_name_identifier: Identifier key to be used for
        displaying group's name
        :return: Result object with operation status and data. Here data is
        a LDAP user/group object corresponding to the basedn. None for others.
        """
        components = ldap.dn.explode_dn(basedn)
        # LDAP doesn't provide an information object when queried for just the
        # domain component.
        if (
            components == []
            or components[0].startswith("DC")
            or components[0].startswith("dc")
        ):
            return Result(Constants.OPERATION_SUCCESS)

        filter_str = "({})".format(components[0])


        result = self.list_groups(basedn,
                                  ldap_type,
                                  user_identifier,
                                  group_display_name_identifier,
                                  2,
                                  filter_str,
                                  log_entities,
                                  member_str)
        if result.status == Constants.OPERATION_SUCCESS and result.data:
            return Result(Constants.OPERATION_SUCCESS, result.data[0])
        if result.status == Constants.AUTHENTICATION_FAILURE:
            return Result(Constants.AUTHENTICATION_FAILURE)

        result = self.list_users(
                    basedn,
                    ldap_type,
                    user_identifier,
                    email_identifier,
                    user_display_name_identifier,
                    2,
                    filter_str,
                    log_entities,
                    authdomain_identifier,
                    member_str)
        if result.status == Constants.OPERATION_SUCCESS and result.data:
            return Result(Constants.OPERATION_SUCCESS, result.data[0])
        if result.status == Constants.AUTHENTICATION_FAILURE:
            return Result(Constants.AUTHENTICATION_FAILURE)

        return Result(Constants.OPERATION_SUCCESS)

    def isOfType(self,
                 basedn,
                 ldap_type,
                 user_identifier,
                 email_identifier,
                 user_display_name_identifier,
                 group_display_name_identifier,
                 member_str,
                 authdomain_identifier):
        """Fetches if the node represented by basedn is of type user or group.

        :param basedn: Distinguished name for the base in LDAP System.
        :param user_display_name_identifier: Identifier key to be used for
        displaying user's name
        :param group_display_name_identifier: Identifier key to be used for
        displaying group's name
        :return: Result object with operation status and data. Here data is
        EntityType.User for User, EntityType.Group for Group, None for DC
        and others.
        """
        result = self.dn_to_obj(basedn,
                                ldap_type,
                                user_identifier,
                                email_identifier,
                                user_display_name_identifier,
                                group_display_name_identifier,
                                member_str,
                                authdomain_identifier)
        if result.status == Constants.OPERATION_SUCCESS:
            if result.data is not None:
                return Result(Constants.OPERATION_SUCCESS, result.data.type)
            return Result(Constants.OPERATION_SUCCESS)

        if result.status == Constants.AUTHENTICATION_FAILURE:
            return Result(Constants.AUTHENTICATION_FAILURE)

        return Result(Constants.OPERATION_FAILURE)
