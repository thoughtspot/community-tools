#!/usr/bin/python

import argparse
from tsut.api import SyncUserAndGroups, eprint
from tsut.apps import add_cnx_parser_arguments

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

"""
This script will retrieve users and groups and write the results to an output file.
"""


def run_app():
    """Runs the application to delete users and groups."""
    args = get_args()
    if valid_args(args=args):
        sync = SyncUserAndGroups(tsurl=args.ts_url,
                                 username=args.username, password=args.password, disable_ssl=args.disable_ssl)

        if args.users:
            delete_users(args, sync)
        if args.groups:
            delete_groups(args, sync)
        if args.user_file:
            delete_users_from_file(args, sync)
        if args.group_file:
            delete_groups_from_file(args, sync)


def get_args():
    """
    Returns the arguments from the command line.
    :return: The arguments from the command line.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser()

    add_cnx_parser_arguments(parser=parser)
    parser.add_argument("--users", help="List of user ids to delete.")
    parser.add_argument("--groups", help="List of group ids to delete.")
    parser.add_argument("--user_file", help="File with list of user ids to delete.")
    parser.add_argument("--group_file", help="File with list of group ids to delete.")

    return parser.parse_args()


def valid_args(args):
    """
    Verifies that the arguments are valid.
    :param args: List of arguments from the command line and defaults.
    :return:  True if valid.
    :rtype: bool
    """
    is_valid = True

    if not args.ts_url:
        eprint("Missing TS URL")
        is_valid = False

    if not args.users and not args.groups and not args.user_file and not args.group_file:
        eprint("Must provide a list of users and/or groups to delete.")
        is_valid = False

    return is_valid


def delete_users(args, sync):
    """
    Deletes the named users.
    :param args: The command line arguments.  Includes the list of users.
    :type args: argparse.Namespace
    :param sync: A sync to use for deleting users.
    :type sync: SyncUserAndGroups
    """
    users = [x.strip() for x in args.users.split(",")]
    sync.delete_users(usernames=users)


def delete_users_from_file(args, sync):
    """
    Deletes users from a file with list of users, one per line.
    :param args: Command line arguments.
    :type args: argparse.Namespace
    :param sync: A sync to use for deleting users.
    :type sync: SyncUserAndGroups
    """
    users = []
    with open(args.user_file, "r") as user_file:
        for row in user_file:
            user = row.strip()
            user = user.strip('"')
            if user != "" and user is not None:
                users.append(user)

    sync.delete_users(usernames=users)


def delete_groups(args, sync):
    """
    Deletes the named groups.
    :param args: The command line arguments.  Includes the list of users.
    :type args: argparse.Namespace
    :param sync: A sync to use for deleting users.
    :type sync: SyncUserAndGroups
    """
    groups = [x.strip() for x in args.groups.split(",")]
    sync.delete_groups(groupnames=groups)


def delete_groups_from_file(args, sync):
    """
    Deletes groups from a file with list of groups, one per line.
    :param args: Command line arguments.
    :type args: argparse.Namespace
    :param sync: A sync to use for deleting groups.
    :type sync: SyncUserAndGroups
    """
    groups = []
    with open(args.group_file, "r") as group_file:
        for row in group_file:
            group = row.strip()
            group = group.strip('"')
            if group != "" and group is not None:
                groups.append(group)

    sync.delete_groups(groupnames=groups)


if __name__ == "__main__":
    run_app()
