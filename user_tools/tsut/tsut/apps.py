import argparse
from abc import abstractmethod
import copy
import json

from tsut.api import SyncUserAndGroups
from tsut.model import UsersAndGroups
from tsut.io import UGXLSWriter, UGXLSReader

"""
Converts from non-TS DDL to TS DDL.  $ convert_ddl.py --help for more details.

Copyright 2017-2018 ThoughtSpot

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

NOTE:  There are many things that could be more efficient.
The following assumptions are made about the DDL being read:
  CREATE TABLE occur together on a single line, not split across lines.
  CREATE TABLE statements will not occur inside of a comment block.
  Delimiters, such as commas, will not be part of the table or column name.
  Comment characters, such as #, --, or /* */ will not be part of a column name.
  CREATE TABLE will have (....) with no embedded, unbalanced parentheses.
"""

"""
This file contains classes for easily creation applications that work with the ThoughtSpot user/group APIs
"""


# Defines the parameters needed for all parsers that will connect to ThoughtSpot.
def add_cnx_parser_arguments(parser):
    """
    Adds common parser arguments needed to connect to ThoughtSpot.
    :param parser: The parser to add the arguments to.
    :type parser: argparse.ArgumentParser
    :return: None
    """
    parser.add_argument("--ts_url", help="URL to ThoughtSpot, e.g. https://myserver")
    parser.add_argument("--username", default='tsadmin', help="Name of the user to log in as.")
    parser.add_argument("--password", default='admin', help="Password for login of the user to log in as.")
    parser.add_argument("--disable_ssl", action="store_true", help="Will ignore SSL errors.", default=True)


class ArgumentUser(object):
    """
    Class that uses arguments.  Used to get the arguments expected and (optionally) validate.
    """
    def __init__(self, required_arguments=None):
        """
        Creates a new ArgumentUser base class.
        :param required_arguments: The arguments required by this class.
        :type required_arguments: list of str
        """
        if not required_arguments:
            self._required_arguments = []
        else:
            self._required_arguments = copy.copy(required_arguments)

    @abstractmethod
    def add_parser_arguments(self, parser):
        """
        Adds the parser arguments to the parser needed for this class.
        """
        pass

    def get_required_arguments(self):
        """
        Returns the list of arguments that are required to be present.
        :return: The list of requried arguments.
        :rtype: list of str
        """
        return self._required_arguments

    def has_valid_arguments(self, args):
        """
        Validates arguments.  By default just checks to see if the required ones are present (not None).
        :param args: Command line arguments.
        :type args: argparse.Namespace
        :return: A tuple of True/False and any issues that might have been found or an empty list.
        :rtype: (bool, list of str)
        """
        issues = []
        dict_args = vars(args)  # convert Namespace to dictionary.
        for req_arg in self._required_arguments:
            valid = (req_arg in dict_args.keys() and dict_args[req_arg])
            if not valid:
                issues.append("Missing %s argument." % req_arg)

        return issues == [], issues


# Readers ------------------------------------------------------------------------------------------------------------

class TSUGReader(ArgumentUser):
    """
    Base class for reading users and groups.
    """
    def __init__(self, required_arguments):
        """
        Creates a new TSUGReader (abstract)
        :param required_arguments: The arguments required by this class.
        :type required_arguments: list of str
        """
        super(TSUGReader, self).__init__(required_arguments=required_arguments)

    @abstractmethod
    def get_users_and_groups(self, args):
        """
        Called by the app to get users and groups.  This method is usually overwritten.
        :param args: Passed in arguments.
        :return: Users and groups that were read.
        :rtype: UsersAndGroups
        """
        pass


class TSUGSyncReader(TSUGReader):
    """
    Reads users and groups from ThoughtSpot using the sync API.
    """

    def __init__(self):
        """
        Creates a new TSUGReader (abstract)
        """
        super(TSUGSyncReader, self).__init__(required_arguments=["ts_url"])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        add_cnx_parser_arguments(parser)

    def get_users_and_groups(self, args):
        """
        Called by the app to get users and groups.  This method is usually overwritten.
        :param args: Passed in arguments.
        :type args: argparse.Namespace
        :return: Users and groups that were read.
        :rtype: UsersAndGroups
        """
        sync = SyncUserAndGroups(tsurl=args.ts_url, username=args.username,
                                 password=args.password, disable_ssl=args.disable_ssl)
        ugs = sync.get_all_users_and_groups()
        print(ugs.to_json())
        return ugs


class TSUGXLSXReader(TSUGReader):
    """
    Reads users and groups from ThoughtSpot using the sync API.
    """

    def __init__(self):
        """
        Creates a new TSUGXLSXReader to read users and groups from Excel.
        """
        super(TSUGXLSXReader, self).__init__(
            required_arguments=["filename"]
        )

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        add_cnx_parser_arguments(parser)
        parser.add_argument("--filename", help="Name of file to write to.")

    def get_users_and_groups(self, args):
        """
        Called by the app to get users and groups.  This method is usually overwritten.
        :param args: Passed in arguments.
        :type args: argparse.Namespace
        :return: Users and groups that were read.
        :rtype: UsersAndGroups
        """
        reader = UGXLSReader()
        ugs = reader.read_from_excel(filepath=args.filename)
        return ugs


# Writers ------------------------------------------------------------------------------------------------------------

class TSUGWriter(ArgumentUser):
    """
    Abstract base class for writing users and groups.
    """

    def __init__(self, required_arguments=None):
        """
        Creates a new TSUGReader (abstract)
        :param required_arguments: The arguments required by this class.
        :type required_arguments: list of str
        """
        super(TSUGWriter, self).__init__(required_arguments=required_arguments)

    @abstractmethod
    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """
        pass


class TSUGXLSWriter(TSUGWriter):
    """
    Writes users and groups to Excel.
    """
    def __init__(self):
        """
        Creates a new TSUGReader (abstract)
        """
        super(TSUGXLSWriter, self).__init__(
            required_arguments=["filename"])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        parser.add_argument("--filename", help="Name of the file to write to.")

    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.  Expects the "filename" argument.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """
        writer = UGXLSWriter()
        writer.write(ugs, args.filename)


class TSUGJsonWriter(TSUGWriter):
    """
    Writes users and groups to a JSON file.
    """
    def __init__(self):
        """
        Creates a new TSUGReader (abstract)
        """
        super(TSUGJsonWriter, self).__init__(
            required_arguments=["filename"])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        parser.add_argument("--filename", help="Name of the file to write to.")

    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.  Expects the "filename" argument.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """
        with open(args.filename, "w") as outfile:
            outfile.write(ugs.to_json())


class TSUGStdOutWriter(TSUGWriter):
    """
    Writes users and groups to standard out as a JSON document.
    """
    def __init__(self):
        """
        Creates a new writer for standard out.
        """
        super(TSUGStdOutWriter, self).__init__(
            required_arguments=[])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        pass

    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.  None expected or used.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """
        # TODO Add pretty print.  Doesn't always work if there are certain, embedded characters.
        # print(json.dumps(json.loads(ugs.to_json()), indent=4, ensure_ascii=False))
        print(ugs.to_json())


class TSUGOutputWriter(TSUGWriter):
    """
    Writer that will write users and groups to a variety of output types (standard out, Excel, or JSON)
    """
    def __init__(self):
        """
        Creates a new writer for standard out.
        """
        super(TSUGOutputWriter, self).__init__(
            required_arguments=["output_type"])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        parser.add_argument("--output_type", help="One of stdout, xls, excel, or json.")
        parser.add_argument("--filename", help="Name of file to write to if not stdout.  Required for Excel and JSON.")

    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.  None expected or used.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """

        if args.output_type in ["json", "excel", "xls"] and not args.filename:
            raise Exception("Output type of %s requires a filename parameter." % args.output_type)

        writer = None
        if args.output_type == "stdout":
            writer = TSUGStdOutWriter()
        elif args.output_type == "json":
            writer = TSUGJsonWriter()
        elif args.output_type == "excel" or args.output_type == "xls":
            writer = TSUGXLSWriter()

        if writer:
            writer.write_user_and_groups(args=args, ugs=ugs)
        else:
            raise Exception("No valid output type specified.  See --help.")


class TSUGSyncWriter(TSUGWriter):
    """
    Writes users and groups to ThoughtSpot using the web services API.
    """
    def __init__(self):
        """
        Creates a new TSUGReader (abstract)
        """
        super(TSUGSyncWriter, self).__init__(
            required_arguments=["ts_url", "username", "password"])

    def add_parser_arguments(self, parser):
        """
        :param parser: The parser to add arguments to.
        :type parser: argparse.ArgumentParser
        """
        add_cnx_parser_arguments(parser)
        parser.add_argument("--remove_deleted", action="store_true",
                            help="Will remove users not in the load.  Cannot be used with batch_size.", default=False)
        parser.add_argument("--apply_changes", action="store_true",
                            help="Will apply changes.  Default is False for testing.", default=False)
        parser.add_argument("--batch_size", default=-1, type=int,
                            help="Loads the users in batches.  Needed to avoid timeouts for large groups of users.")
        parser.add_argument("--merge_groups", default=False, action="store_true",
                            help="Merge new groups with groups in ThoughtSpot.")

    def write_user_and_groups(self, args, ugs):
        """
        Writes the users and groups.
        :param args: Command line arguments for writing.
        :type args: argparse.Namespace
        :param ugs: Users and groups to write.
        :type ugs: UsersAndGroups
        :return:  None
        """
        sync = SyncUserAndGroups(tsurl=args.ts_url, username=args.username,
                                 password=args.password,
                                 disable_ssl=args.disable_ssl)
        sync.sync_users_and_groups(users_and_groups=ugs,
                                   apply_changes=args.apply_changes,
                                   remove_deleted=args.remove_deleted,
                                   batch_size=args.batch_size, merge_groups=args.merge_groups)


class TSUserGroupSyncApp(object):
    """
    Class for applications that use the user/group web services.
    This class allows new sync scripts to created via composition by assigning to/from classes.

    A standard extension will create a sub-class, add arguments to the defaults, call initialize, and then execute.
    """
    def __init__(self, reader, writers):
        """
        :param reader: An object of type TSUGReader that can read users and groups.
        :type reader: TSUGReader
        :param writers: An object of type TSUGWriter that can write users and groups, or list of those objects.
        :type writers: TSUGWriter | list of TSUGWriter
        """

        # Make sure we have all the right types.
        assert (isinstance(reader, TSUGReader))
        self._ug_reader = reader

        self._ug_writers = []
        if isinstance(writers, TSUGWriter):
            self._ug_writers.append(writers)
        else:
            for w in writers:
                assert (isinstance(w, TSUGWriter))
                self._ug_writers.append(w)

        parser = argparse.ArgumentParser(conflict_handler="resolve")
        reader.add_parser_arguments(parser)

        for w in self._ug_writers:
            w.add_parser_arguments(parser)

        self._args = parser.parse_args()


    @staticmethod
    def _get_error_msg(issues):
        """
        Gets a formatted error message for printing.
        :param issues: A list of issues.
        :type issues: list of str
        :return: A formatted string.
        :rtype: str
        """
        err_msg = "Invalid arguments: \n"
        for issue in issues:
            err_msg += "  %s\n" % issue

        return err_msg

    def get_args(self):
        """
        Gets the command line arguments.
        :return: The command line arguments entered by the user.
        :rtype: argparse.Namespace
        """
        return self._args

    def run(self):
        """
        Gets and validates the command line arguments, runs the getter, then runs the setter.
        :return: None
        """
        fail = False
        has_valid_args = self._ug_reader.has_valid_arguments(args=self._args)
        if not has_valid_args[0]:
            fail = True
            print(TSUserGroupSyncApp._get_error_msg(has_valid_args[1]))

        for w in self._ug_writers:
            has_valid_args = w.has_valid_arguments(args=self._args)
            if not has_valid_args[0]:
                fail = True
                print(TSUserGroupSyncApp._get_error_msg(has_valid_args[1]))

        if fail:
            raise AttributeError("Invalid arguments.  Provide all required arguments.")

        ugs = self._ug_reader.get_users_and_groups(args=self._args)
        for w in self._ug_writers:
            w.write_user_and_groups(ugs=ugs, args=self._args)

        print("Success")
