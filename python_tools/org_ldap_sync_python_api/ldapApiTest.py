#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)

"""
Unit tests for ldapApi.py.

Help command:

>>> python ldapApiTest.py --help

Example command:

>>> python ldapApiTest.py
        --hostport <hostport>
        --username <username>
        --password <password>
        --user_dn <userdn>
        --group_dn <groupdn>
"""

import argparse
import logging
import string
import sys
import unittest
import ldap3

from globalClasses import Constants
from ldapApi import LDAPApiWrapper

HOSTPORT = None
USERNAME = None
PASSWORD = None
USER_DN = None
GROUP_DN = None


class TestLDAPApi(unittest.TestCase):

    def test_login(self):
        ldap_handle = LDAPApiWrapper()
        self.assertFalse(ldap_handle._is_authenticated())
        ldap_handle.login(HOSTPORT, USERNAME, PASSWORD)
        self.assertTrue(ldap_handle._is_authenticated())

    def test_list_users(self):
        ldap_handle = LDAPApiWrapper()
        ldap_handle.login(HOSTPORT, USERNAME, PASSWORD)
        result = ldap_handle.list_users(USER_DN, None, "objectGUID", None, None)
        self.assertEqual(result.status, Constants.OPERATION_SUCCESS)

    def test_list_groups(self):
        ldap_handle = LDAPApiWrapper()
        ldap_handle.login(HOSTPORT, USERNAME, PASSWORD)
        result = ldap_handle.list_groups(GROUP_DN, None, None, None, )
        self.assertEqual(result.status, Constants.OPERATION_SUCCESS)

    def test_fetch_components_from_dn(self):
        test_dn = "CN=A,CN=B,OU=engg,DC=ldap,DC=thoughtspot,DC=com"
        ldap_handle = LDAPApiWrapper()
        non_dc, dc = ldap_handle._fetch_components_from_dn(test_dn)
        self.assertEqual(non_dc, ["CN=A", "CN=B", "OU=engg"])
        self.assertEqual(dc, ["DC=ldap", "DC=thoughtspot", "DC=com"])

    def test_fetch_domain_name_from_dn(self):
        test_dn = "CN=A,CN=B,OU=engg,DC=ldap,DC=thoughtspot,DC=com"
        ldap_handle = LDAPApiWrapper()
        domain_name = ldap_handle.fetch_domain_name_from_dn(test_dn)
        self.assertEqual(domain_name, "@ldap.thoughtspot.com")

    def test_filter_handling(self):
        test_dn = "DC=ldap,DC=thoughtspot,DC=com"
        ldap_handle = LDAPApiWrapper()
        ldap_handle.login(HOSTPORT, USERNAME, PASSWORD)

        # Use this to search directly to ensure that when unhandled, an error
        # is thrown for bad filters.
        conn = ldap_handle.connection_pool["default"]

        # Assert ldap_handle search can handle various bad filters
        bad_filters = [r"(cn=\,)", r"(cn=\)", r"(cn=\\)"]
        for bad_filter in bad_filters:
            # Assert that search with unhandled filters raises error.
            with self.assertRaises(
                    ldap3.core.exceptions.LDAPInvalidFilterError):
                conn.search(search_base=test_dn, search_scope=ldap3.SUBTREE,
                            search_filter=bad_filter, attributes=["cn"])
            # Assert that search with our LDAPApiWrapper handles these errors.
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_users(test_dn, None, None, None, None,
                                       ldap3.SUBTREE, bad_filter).status,
            )
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_groups(test_dn, None, None, None,
                                        ldap3.SUBTREE, bad_filter).status,
            )

        good_filters = ["(cn=')", "(cn=')", '(cn="")', '(cn=")', "(cn=,)"]
        for good_filter in good_filters:
            # Assert good filters act the same in both cases.
            conn.search(search_base=test_dn, search_scope=ldap3.SUBTREE,
                        search_filter=good_filter, attributes=["cn"])
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_users(test_dn, None, None, None, None,
                                       ldap3.SUBTREE, good_filter).status,
            )
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_groups(test_dn, None, None, None,
                                        ldap3.SUBTREE, good_filter).status,
            )

        for char in string.punctuation:
            if char in ["(", ")"]:
                # Filter with unbalanced paranthesis means that filter is wrong
                # we shouldn't handle such scenarios.
                continue

            bad_filter = f"(cn=last{char}first)"

            # Assert for bad filters common search raises error.
            if char == "\\":
                with self.assertRaises(
                        ldap3.core.exceptions.LDAPInvalidFilterError):
                    conn.search(search_base=test_dn, search_scope=ldap3.SUBTREE,
                                search_filter=bad_filter, attributes=["cn"])
            else:
                conn.search(search_base=test_dn, search_scope=ldap3.SUBTREE,
                            search_filter=bad_filter, attributes=["cn"])

            # Assert we handle bad filters gracefully.
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_users(test_dn, None, None, None, None,
                                       ldap3.SUBTREE, bad_filter).status,
            )
            self.assertEqual(
                Constants.OPERATION_SUCCESS,
                ldap_handle.list_groups(test_dn, None, None, None,
                                        ldap3.SUBTREE, bad_filter).status,
            )


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hostport",
        help="Hostport in the format ldap(s)://host:port or ldap(s)://host",
        default=None,
    )
    parser.add_argument("--username", help="Username", default=None)
    parser.add_argument("--password", help="Password", default=None)
    parser.add_argument(
        "--user_dn", help="User distinguished name", default=None
    )
    parser.add_argument(
        "--group_dn", help="Group distinguished name", default=None
    )
    arguments = parser.parse_args()
    assert arguments.hostport is not None, "HostPort cannot be None."
    HOSTPORT = arguments.hostport
    assert arguments.username is not None, "Username cannot be None."
    USERNAME = arguments.username
    assert arguments.password is not None, "Password cannot be None."
    PASSWORD = arguments.password
    assert arguments.user_dn is not None, "User DN cannot be None."
    USER_DN = arguments.user_dn
    assert arguments.group_dn is not None, "Group DN cannot be None."
    GROUP_DN = arguments.group_dn
    # Set sys.argv array to empty as without this unittest.main() too will try
    # to parse the arguments which are already parsed.
    sys.argv[1:] = []

    loader = unittest.loader.defaultTestLoader
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    suite = loader.loadTestsFromModule(sys.modules["__main__"])

    runner.run(suite)
