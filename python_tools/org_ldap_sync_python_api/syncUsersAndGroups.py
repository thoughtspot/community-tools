#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Script to sync users and groups from LDAP System to TS System."""

import argparse
import getpass
import logging
import sys
from itertools import chain

import orgAwareUsersAndGroupsSync
import syncTree


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
        Argument(
            flag="org_mapping",
            help_str="Map users and groups in corresponding orgs",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="org_file_input",
            help_str="file input containing org mappings",
            default=None
        ),
        Argument(
            flag="org_attr",
            help_str="ldap obj have orgs attribute",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="remove_user_orgs",
            help_str="remove users from orgs which "
                     "are not there in present sync",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="remove_group_orgs",
            help_str="remove group from orgs which "
                     "are not there in present sync",
            action="store_true",
            default=False,
        ),
        Argument(
            flag="add_recursive_org_membership",
            help_str="To recursively assign org mapping to member "
                     "objects as that of parent",
            action="store_true",
            default=False,
        )
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

        if non_optional_args["org_mapping"] and (
                non_optional_args["org_file_input"] is None and
                non_optional_args["org_attr"] is False):
            error = "cannot sync orgs without the org_file_input or " \
                    "org_attr flag"
            logging.error(error)
            sys.exit(1)

        if non_optional_args["org_mapping"]:
            orgAwareUsersAndGroupsSync.OrgAwareSyncTree(non_optional_args)
        else:
            syncTree.SyncTree(non_optional_args)
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
