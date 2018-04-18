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
import os
from os import listdir
from os.path import isfile, isdir, join
import json
import smtplib
import ntpath
import datetime
import time
import tarfile
import shutil
import subprocess
import copy
from multiprocessing import Pool
from email import MIMEMultipart
from email import MIMEText
from email import MIMEBase
from email import encoders

current_datetime = datetime.datetime.now()
date = str(current_datetime.year)+str(current_datetime.month)+str(current_datetime.day)


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


def json_dump(j):
    return json.dumps(j, sort_keys=True, indent=4, separators=(",", ": "))


def load_a_file(cmd):
    """
    Loads an individual file using tsload.
    :param cmd: The command to load the file.  This needs to be a valid tsload command.
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

    return output


class Mailer(object):
    """
    Wraps mail tools to simplify sending email.
    """

    def __init__(self, settings):
        """
        Creates a new mailer.
        :param settings: Contains settings, including the email server.
        :type settings: dict
        """
        self.smtp_server = settings.get("email-server", None)
        self.smtp_port = settings.get("email-port", 25)
        if not self.smtp_server:
            eprint("WARNING:  No email server provided.  Emails will not be sent.")

    def send_email(self, email_to, email_from, subject, body, attachment_path=None):

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_path.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % attachment_path)
            msg.attach(part)

        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.sendmail(email_from, email_to, msg.as_string())
        server.quit()


class ParallelFileLoader(object):
    """
    Manages the loading of multiple data files in parallel using tsload based on settings provided by the user.
    """

    def __init__(self, settings):
        """
        Creates a new parallel file loader based on the settings.
        :param settings: The settings to use for loading the data.
        :type settings: dict
        """

        # get all of the directory settings needed.
        self.root_directory = settings.get("root_directory", None)
        if not self.root_directory or not isdir(self.root_directory):
            raise IOError(
                "The root_directory %s doesn't exist or it not a valid directory."
                % self.root_directory
            )

        self.data_directory = settings.get("data_directory", self.root_directory + "/data")
        if not isdir(self.data_directory):
            raise IOError(
                "The data_directory %s doesn't exist or it not a valid directory."
                % self.data_directory
            )
        self.loaded_directory = self._get_dir("loaded")
        self.archive_directory = self._get_dir("archive")
        self.log_directory = self._get_dir("logs")

        self.settings = copy.copy(settings)  # Assumes shallow copy is sufficient.

    def load_files(self):
        """
        Loads the files based on the settings used when created.
        """

        file_extension = self.settings.get(
            "filename_extension", ".csv"
        )   # default to .csv if none provided.

        max_simultaneous_loads = int(
            self.settings.get("max_simultaneous_loads", 1)
        )  # might throw an exception if not an int.
        pool = Pool(processes=max_simultaneous_loads)

        # get a list of commands to run in parallel.
        files = [f for f in [join(self.data_directory, f)
                             for f in listdir(self.data_directory)
                             if isfile(join(self.data_directory, f)) and f.endswith(file_extension)]]

        base_cmd = self._create_base_command()
        commands = []
        for f in files:
            commands.append(self._update_base_cmd_for_file(base_cmd, f))

        # Turns off indexing.
        subprocess.call("sage_master_tool PauseUpdates", shell=True)

        results = [pool.apply_async(load_a_file, (cmd,)) for cmd in commands]

        # Turns on indexing.
        subprocess.call("sage_master_tool ResumeUpdates", shell=True)

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        log_file_name = "load_results_%s.log" % now
        log_path = self.log_directory + "/" + log_file_name
        with open(log_path, "w") as log_file:
            for res in results:
                print(res.get())
                log_file.write(res.get())

        # copy logfile to old directory.
        to_path = self.loaded_directory + "/" + log_file_name
        shutil.copy(log_path, to_path)

        self.move_loaded_files(files, now)

    def _create_base_command(self):
        """
        Creates the base tsload command based on the settings.
        :return:  A string to use for the command containing two parameters:  {file_path} and {table_name}
        :rtype: str
        """
        cmd = "cat {file_path} | tsload --target_table {table_name}"
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

        return cmd

    def _update_base_cmd_for_file(self, base_cmd, file_path):
        """
        Updates the base_cmd based on the file name.
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
        table_name = table_name.split(self.settings.get("filename_extension", ""))[0]

        # take off . in case it's not included in the extension.  That would be an invalid table name.
        if table_name.endswith("."):
            table_name = table_name[:-1]

        # handle _full and _incremental.  MUST be last thing before the extension.
        empty_target = self.settings.get("settings.empty_target", "")
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
        )  # simply replace the     default if overridden.

        return cmd

    def move_loaded_files(self, files, runtime):
        """
        Zips load files and results and moves them to an archived folder.
        :param files: list of files that were loaded.
        :type files: list of str
        :param runtime: date/time as a string when the run occurred.  Used for the name of the archive.
        :type runtime: str
        """

        for f in files:
            if self.settings.get("move_files", "true") == "true":
                shutil.move(f, self.loaded_directory)
            else:
                shutil.copy(f, self.loaded_directory)

        # Zips the archive into a tarball
        with tarfile.open("%s/load_results_%s.tar.gz" % (self.archive_directory, runtime), "w:gz") as tar:
            tar.add(self.loaded_directory, arcname=os.path.basename(self.loaded_directory))

        # Removes old archive directory contents.
        shutil.rmtree(self.loaded_directory)

    def delete_old_archives(self):
        """
        Deletes archives after a specified number of days
        """

        now = time.time()

        # Lists out all tar archives in old directory.
        # TODO:  update this to work.  Right now it won't find any files.
        for f in os.listdir(self.loaded_directory):
            f = os.path.join(self.loaded_directory, f)
            # Checks if date of archives in old directory are less than number of specified days old (in seconds).
            if os.stat(f).st_mtime < now - int(self.settings.get("max_archive_days", None)) * 86400:
                if os.path.isfile(f):
                    os.remove(f)

    def _get_dir(self, dir_name):
        """
        Returns a path to a directory under the root directory with the given name.  The directory will be created
        if needed.
        :param dir_name: The directory under the root path.
        :type dir_name: str
        :return:  The full path of the directory.
        :rtype: str
        """
        full_dir = self.root_directory + "/" + dir_name
        if not os.path.exists(full_dir):
            os.mkdir(full_dir)
        elif not os.path.isdir(full_dir):
            raise IOError("%s is not a directory." % full_dir)
        return full_dir

    def _send_results_email(self, had_errors):
        """
        Sends an email with the results file attached.
        :param had_errors:  True if the load had errors.
        :type had_errors: bool
        """

        # see if there is anyone to email to.  If not just return and don't do anything.
        email_to = self.settings.get("email_to", None)
        if not email_to:
            print("No email address provided in settings.  To email results add 'email_to' setting.")
            return

        cluster_name = subprocess.check_output("tscli cluster status | grep 'Cluster name' | sed 's/^.*: //'")

        # TODO add some error checking for settings.
        email_from = self.settings.get("email_from", None)
        subject = "%s loading data for cluster %s" % ("Error" if had_errors else "Success", cluster_name)
        body = "Data load for %s appears to have %s.  See attachment for details." % \
               (cluster_name, "failed" if had_errors else "succeeded")

        # TODO: get path to results.
        attachment_path = open("/home/admin/load_files2/testing/load_results.log", "rb")
        mailer = Mailer(settings=self.settings)
        # may need a legit email address.
        mailer.send_email(email_from=email_from, email_to=email_to, subject=subject,
                          body=body, attachment_path=attachment_path)


def main():
    """
    Loads files using tsload based on the settings in the settings file.
    """

    args = parse_args()
    if valid_args(args):

        settings = read_settings(args.filename)

        # See if there is a semaphore setting.  If so, then only run if the semaphore exists.  If not, then run
        # every time, looking for files.

        # exits if semaphore file is not present in data directory
        semaphore_name = settings.get("semaphore_filename", None)
        data_directory = settings.get("data_directory", None)
        if not data_directory:
            eprint("Error:  data directory %s doesn't exist!!" % data_directory)

        # the existance of a semaphore file means that a semaphore is being used.
        if semaphore_name:
            semaphore_path = data_directory + "/" + semaphore_name
            if not os.path.exists(semaphore_path):
                return  # because there is supposed to be a file and it doesn't exist.
            else:
                # Should be OK to remove the semaphore since already know to load.
                os.remove(semaphore_path)

        loader = ParallelFileLoader(settings=settings)
        loader.load_files()


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
