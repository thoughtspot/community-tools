#!/usr/bin/python

import argparse
#from mgmt import delUser
#from mgmt import getUsers
from UserManagement import *
#from delete_ugs import delUser
#from get_users import getUsers
#from tsUserGroupApi import SyncUserAndGroups, eprint

def main():

    args = parse_args()

    print(args)

    if args.command == 'delete':
        deleteUser = delUser()
        if deleteUser.valid_args(args):
            sync = SyncUserAndGroups(tsurl=args.ts_url, username=args.username, password=args.password,
                                     disable_ssl=args.disable_ssl)
            if args.users is not None:
                deleteUser.delete_users(args, sync)
            if args.user_file is not None:
                deleteUser.delete_users_from_file(args, sync)
            if args.groups is not None:
                deleteUser.delete_groups(args, sync)
            if args.group_file is not None:
                deleteUser.delete_groups_from_file(args, sync)

    if args.command == 'get':
        getUsersObj = getUsers()
        if getUsersObj.valid_args(args):
            getUsersObj.dump_users_and_groups(args)


def parse_args():
    """
    Parses the arguments from the command line.
    :returns: The arguments object.
    """
    # parser = argparse.ArgumentParser()
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument("-d", "--delete",help="Delete user, user group", action="store_true")
    # group.add_argument("-g", "--get", help="Delete user, user group", action="store_true")
    # parser.add_argument("-t", "--ts_url",help="URL to ThoughtSpot, e.g. https://myserver")
    # parser.add_argument("-u", "--username",default='tsadmin',help="Name of the user to log in as.")
    # parser.add_argument("-p", "--password",default='admin',help="Password for login of the user to log in as.")
    # parser.add_argument("--disable_ssl", action="store_true",help="Will ignore SSL errors.")
    # parser.add_argument("--users",help="List of comma separated users.  Use quotes if there are spaces.")
    # parser.add_argument("--groups", help="List of comma separated groups.  Use quotes if there are spaces.")
    # parser.add_argument("--user_file",help="File containing list of users to delete.  One user per line, optionally quoted.")
    # parser.add_argument("--group_file",help="File containing list of groups to delete.  One user per line, optionally quoted.")
    # parser.add_argument("-o", "--output_type", default="xls", help="Output type, either xls or json")
    # parser.add_argument("-f", "--filename", default="users_and_groups", help="Either the name of the json file or root of Excel file names.")

    # COMMON INPUTS
    parser = argparse.ArgumentParser(description="TS Comunity Utilities")
    parser.add_argument("-t", "--ts_url", help="URL to ThoughtSpot, e.g. https://myserver")
    parser.add_argument("-u", "--username", default='tsadmin', help="Name of the user to log in as.")
    parser.add_argument("-p", "--password", default='admin', help="Password for login of the user to log in as.")
    parser.add_argument("--disable_ssl", action="store_true", help="Will ignore SSL errors.", default=False)

    subparser = parser.add_subparsers(description='Sub commands', dest='command')

    # HANDLING DELETE OPS AS A SEPARATE COMMAND
    delete_ops = subparser.add_parser('delete', help='Delete user, user group')
    delete_ops.add_argument("--users", help="List of comma separated users.  Use quotes if there are spaces.")
    delete_ops.add_argument("--groups", help="List of comma separated groups.  Use quotes if there are spaces.")
    delete_ops.add_argument("--user_file",
                            help="File containing list of users to delete.  One user per line, optionally quoted.")
    delete_ops.add_argument("--group_file",
                            help="File containing list of groups to delete.  One user per line, optionally quoted.")

    # HANDLING GET OPERATIONS AS A SEPARATE COMMANDS
    get_ops = subparser.add_parser('get', help='Gets User, User groups')
    get_ops.add_argument('-g', '--get', action="store_true", default=False, help='Get details Flag')
    get_ops.add_argument("-o", "--output_type", default="xls", help="Output type, either xls or json")
    get_ops.add_argument("-f", "--filename", default="users_and_groups",
                         help="Either the name of the json file or root of Excel file names.")


    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
