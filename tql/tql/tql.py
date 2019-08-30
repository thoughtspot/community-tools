import logging
import os
import sys
import shlex
import subprocess
import time

from model import DataTable, Row

"""
Copyright 2019 ThoughtSpot
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
This module contains the class for interacting with TQL.
"""


class TQL(object):
    """
    Wraps the TQL interface.  Note that this class expects to run on the ThoughtSpot cluster and have tql in the path.
    """

    COLUMN_SEPARATOR="|"  # TQL uses pipes to separate output columns.
    COMMAND="/usr/local/scaligent/release/bin/tql -query_results_apply_top_row_count=-1"

    # TQL specific queries.
    SHOW_DATABASES="show databases;"

    def __init__(self):
        """
        Creates a new TQL interface.
        """
        pass

    def get_databases(self):
        """
        Returns a list of the databases.
        :return: A list of all the database commands.
        """
        out, err = self._execute_query(query=TQL.SHOW_DATABASES)

        tables = []
        for table in out:
            tables.append(table.strip())

        return tables

    def execute_tql_query(self, query):
        """
        Executes a TQL query and returns the data as a data table.
        :param query: A complete query to send to TQL.
        :type query: str
        :return: A data table with the results.
        :rtype: DataTable
        """
        out, err = self._execute_query(query=query)

        table = DataTable()

        # The header should be in the first row that contains pipes.
        header = None
        for line in err:
            if query in line:
                continue

            # The first line is the command.  The next line is the header.
            splitter = shlex.shlex(line, posix=True)
            splitter.whitespace = TQL.COLUMN_SEPARATOR
            splitter.whitespace_split = True
            splitter.commenters = ''
            splitter.quotes='"'
            header = list(splitter)
            break

        if header:
            table._header = header

        for line in out:
            splitter = shlex.shlex(line, posix=True)
            splitter.whitespace = TQL.COLUMN_SEPARATOR
            splitter.whitespace_split = True
            splitter.commenters = ''
            splitter.quotes='"'
            data = list(splitter)
            table.add_row(row=data)

        return table

    @staticmethod
    def _execute_query(query):
        """
        Executes the query and returns the standard out and standard error received from TQL.
        :param query: The query to execute.
        :type query: str
        :return: The results of the query.
        :rtype list of str,str
        """
        # TODO add more error checking.
        query = query.strip()

        # make sure a semi-colon was included.
        if not query.endswith(';'):
            query += ";"

        tql_file = "/tmp/tql.%s" % time.time()
        with open(tql_file, "w") as cmdfile:
            cmdfile.write(query)

        command = "cat '" + tql_file + "' | " + TQL.COMMAND
        logging.debug(command)

        proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()

        os.remove(tql_file)  # bit of cleanup.

        logging.debug("==================================================================")
        logging.debug(out)
        logging.debug("==================================================================")
        logging.debug(err)
        logging.debug("==================================================================")

        # This isn't perfect if there is an error that doesn't have the text "error=" in it.
        if "error=" in err:
            raise Exception ("Error from TQL: %s", err)

        stdout = out.decode("utf-8", "ignore").split('\n')
        # usually get a blank line that isn't needed.
        try:
            stdout.remove('')
        except ValueError:
            pass  # might not be there.

        stderr = err.decode("utf-8", "ignore").split('\n')
        # usually get a blank line that isn't needed.
        try:
            stderr.remove('')
        except ValueError:
            pass  # might not be there.

        return stdout, stderr


if __name__ == "__main__":
    tql = TQL()
    # send the command.  Wrap in quotes if it has spaces.
    tql._execute_query(sys.argv[1])
