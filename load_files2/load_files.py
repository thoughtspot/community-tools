#!/usr/bin/python

"""
Converts from non-TS DDL to TS DDL.  $ convert_ddl.py --help for more details.

Copyright 2017 ThoughtSpot

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

from __future__ import print_function
import sys
import argparse
from os import listdir
from os.path import isfile, isdir, join
import json
import ntpath


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


def json_dump(j):
    return json.dumps(j, sort_keys=True, indent=4, separators=(",", ": "))


class TSFileLoader(object):
    """
    Loads a file into ThoughtSpot using sub-process calls to tsload.
    """

    def __init__(self, settings):
        """
        Creates a new file loader with the given settings.
        :param settings: A JSON object with the settings to use for loading files.
        :type settings: dict
        """
        self.settings = settings
        self.cmd = self.get_base_tsload_command()  # populate here, so the object can be reused without redoing completely.
        print(self.cmd)

    def get_base_tsload_command(self):
        """
        Calculates the tsload command based on the filename and the flags.
        :return: The base command to execute with the filename and table_name as arguments.
        :rtype: str
        """
        cmd = "cat {filename} | tsload --target_table {table_name}"
        for key in self.settings:
            if key.startswith("tsload"):
                flag = key.split(".")[
                    1
                ]  # get the key after the "tsload." indicator.
                value = str(self.settings[key])
                if value == "true":
                    cmd += " --%s" % flag  # indicates a switch flag.  Hopefully not a valid value for something else.
                elif value == "false":
                    pass  # don't add false flags.
                else:
                    cmd += ' --%s "%s"' % (flag, value)

        print(cmd)
        return cmd

    def load_file(self, filepath):
        """
        Loads an individual file using tsload.
        :param filepath: The path to the file to load.
        :type filepath: str
        :return: Results of the load process as a string.
        :rtype: str
        """
        print("Loading %s...." % filepath)
        # always strip the path off the filepath.
        head, tail = ntpath.split(filepath)
        table_name = tail or ntpath.basename(head)
        # table names are the name of the file, minus:
        # - .extension
        # - _incremental or _full
        # - ?? do we somehow allow timestamps?  Easier if not.  Maybe add as a future enhancement.  One option would
        #      be to just to provide a pattern, or maybe a strip flag for _ and -.
        #   -- solution - add a table name terminator that we will ignore everything after that.

        # TODO add check for empty target flag.  This can override the default.  Support _incremental and _full

        cmd = self.cmd.format(
            filename=filepath, table_name=table_name
        )  # TODO add format for file and table names.
        print(cmd)
        return "success"


class TSLoadManager(object):
    """
    Manages the loading of one or more files into ThoughtSpot using tsload.  The files can be loaded into parallel
    up to the number of parallel loads specified in the settings.
    """

    def __init__(self, settings):
        """
        Creates a load manager to load files using tsload.  An error will be thrown if there are missing mandatory
        parameters.
        :param settings: A JSON object with the settings to use for loading.
        :type settings: dict
        """
        self.settings = settings

        self.root_directory = settings.get("root_directory", None)
        if self.root_directory is None or not isdir(self.root_directory):
            raise Exception(
                "The root_directory %s doesn't exist or it not a valid directory."
                % self.root_directory
            )

        self.data_directory = settings.get(
            "data_directory", self.root_directory + "/data"
        )
        if not isdir(self.data_directory):
            raise Exception(
                "The data_directory %s doesn't exist or it not a valid directory."
                % self.root_directory
            )

        self.max_simultaneous_loads = int(
            settings.get("max_simultaneous_loads", "1")
        )  # might throw an exception.
        pass

    def load_files(self):
        """
        Manages the loading of files.
        """
        for f in [
            join(self.data_directory, f)
            for f in listdir(self.data_directory)
            if isfile(join(self.data_directory, f))
        ]:
            tsloader = TSFileLoader(
                self.settings
            )  # see if I can create a pool and reuse if worth it.
            print(tsloader.load_file(f))


def main():
    """
    Loads files using tsload based on the settings in the settings file.
    """
    args = parse_args()
    if valid_args(args):
        settings = read_settings(args.filename)
        load_manager = TSLoadManager(settings)
        load_manager.load_files()


def parse_args():
    """Parses the arguments from the command line."""
    parser = argparse.ArgumentParser(
        epilog="Example:  python load_files.py my_settings.json"
    )
    parser.add_argument(
        "-f",
        "--filename",
        default="settings.json",
        help="Name of the file with the settings in JSON.",
    )
    args = parser.parse_args()
    return args


def valid_args(args):
    """
    Checks to see if the arguments make sense.
    :param args: The command line arguments.
    :return: True if valid, false otherwise.
    """
    # make sure the settings file exists.
    if not isfile(args.filename):
        eprint("File %s doesn't exist." % args.filename)
        return False

    return True


def read_settings(settings_filename):
    """
    Reads the settings object from a file and returns a JSON object.
    :param settings_filename: Name of the file to read settings from.  Assumed to contain a JSON object.
    :type settings_filename: str
    :return:  A JSON object with the settings.
    """
    print("reading settings from %s" % settings_filename)
    with open(settings_filename, "r") as settings_file:
        settings = json.load(settings_file)
        print(json_dump(settings))

    return settings


if __name__ == "__main__":
    main()
