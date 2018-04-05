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
import subprocess
from multiprocessing import Pool


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


def json_dump(j):
    return json.dumps(j, sort_keys=True, indent=4, separators=(",", ": "))


def main():
    """
    Loads files using tsload based on the settings in the settings file.
    """
    args = parse_args()
    if valid_args(args):
        settings = read_settings(args.filename)
        # root_directory, data_directory = get_directory_settings(settings)
        base_cmd = create_base_command(settings)
        load_files(settings, base_cmd)

        # TODO:
        # Write the results to a log file.
        # Send email of results.
        # Move and archive the loaded files.
        # Prune archive if settings say so.


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


def create_base_command(settings):
    """
    Creates the base tsload command based on the settings.
    :param settings:  Dictionary of settings for tsload.
    :type settings: dict
    :return:  A string to use for the command containing two parameters:  {file_path} and {table_name}
    :rtype: str
    """
    cmd = "cat {file_path} | tsload --target_table {table_name}"
    for key in settings:
        if key.startswith("tsload"):
            flag = key.split(".")[
                1
            ]  # get the key after the "tsload." indicator.
            value = str(settings[key])
            if value == "true":
                cmd += " --%s" % flag  # indicates a switch flag.  Hopefully not a valid value for something else.
            elif value == "false":
                pass  # don't add false flags.
            else:
                cmd += ' --%s "%s"' % (flag, value)

    return cmd


def load_files(settings, base_cmd):
    """
    :param settings:  Dictionary of settings for tsload.
    :type settings: dict
    :param base_cmd:  The base command to use for tsload after formatting.
    :type base_cmd: str
    """

    root_directory, data_directory = get_directory_settings(settings)
    file_extension = settings.get(
        "filename_extension", ".csv"
    )  # default to .csv if none provided.

    max_simultaneous_loads = int(
        settings.get("max_simultaneous_loads", 1)
    )  # might throw an exception if not an int.
    pool = Pool(processes=max_simultaneous_loads)

    # TODO turn off indexing:  From Satyam:  You can call `sage_master_tool PauseUpdates`

    # get a list of commands to run in parallel.
    commands = []
    for f in [
        join(data_directory, f)
        for f in listdir(data_directory)
        if isfile(join(data_directory, f)) and f.endswith(file_extension)
    ]:
        commands.append(update_base_cmd_for_file(settings, base_cmd, f))

    # TODO turn on indexing:  From Satyam:  `sage_master_tool ResumeUpdates`

    results = [pool.apply_async(load_a_file, (cmd,)) for cmd in commands]
    for res in results:
        print(res.get())



def get_directory_settings(settings):
    """
    Verifies (as much as possible) that the settings are valid.
    :param settings:  Dictionary of settings for tsload.
    :type settings: dict
    :returns: The root directory and data directory.
    :rtype: (str, str)
    """
    root_directory = settings.get("root_directory", None)
    if not root_directory or not isdir(root_directory):
        raise IOError(
            "The root_directory %s doesn't exist or it not a valid directory."
            % root_directory
        )

    data_directory = settings.get("data_directory", root_directory + "/data")
    if not isdir(data_directory):
        raise IOError(
            "The data_directory %s doesn't exist or it not a valid directory."
            % root_directory
        )

    return root_directory, data_directory


def update_base_cmd_for_file(settings, base_cmd, file_path):
    """
    Updates the base_cmd based on the file name.
    :param settings: Settings from the user.
    :type settings: dict
    :param base_cmd: The base command that will need to be modified for the file.
    :type base_cmd: str
    :param file_path: The path to the file to load.
    :type file_path: str
    :return: The adjusted command tailored for the file.
    :rtype: str
    """

    # always strip the path off the file_path.
    head, tail = ntpath.split(file_path)
    table_name = tail or ntpath.basename(head)

    # table names are the name of the file, minus:
    # - .extension
    # - _incremental or _full
    # - ?? do we somehow allow timestamps?  Easier if not.  Maybe add as a future enhancement.  One option would
    #      be to just to provide a pattern, or maybe a strip flag for _ and -.

    # remove the extension.
    table_name = table_name.split(settings.get("filename_extension", ""))[0]

    # take off . in case it's not included in the extension.  That would be an invalid table name.
    if table_name.endswith("."):
        table_name = table_name[:-1]

    # handle _full and _incremental.  MUST be last thing before the extension.
    empty_target = settings.get("settings.empty_target", "")
    if table_name.endswith("_full"):
        empty_target = "--empty_target"
        table_name = table_name[:-len("_full")]
    elif table_name.endswith("_incremental"):
        empty_target = ""
        table_name = table_name[:-len("_incremental")]

    cmd = base_cmd.format(
        file_path=file_path, table_name=table_name
    )  # TODO add format for file and table names.

    cmd = cmd.replace(
        "--empty_target", empty_target
    )  # simply replace the default if overridden.

    return cmd


def load_a_file(cmd):
    """
    Loads an individual file using tsload.
    :param cmd: The base command to use for tsload.  Gets modified for file and table name.
    :type cmd: str
    :return:  The output as a string.
    :rtype: str
    """

    # fork out to the command and capture the results.
    print(cmd)
    try:
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True
        )
    except subprocess.CalledProcessError as cpe:
        # print ("Status : Fail", cpe.returncode, cpe.output)
        output = cpe.output
    # else:
    #     print("Output: \n{}".format(output))

    return output


if __name__ == "__main__":
    main()
