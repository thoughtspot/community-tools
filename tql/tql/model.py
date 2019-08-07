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
This module contains the class for representing TQL data structures.
"""


class Row (object):
    """
    Represents a row of data in a table.  Columns can be iterated over or retrieved by column name.
    """

    def __init__(self, data=None, header=None):
        """
        Creates a new table row.
        :param data: List of data values for the columns.
        :type data: list
        :param header: List of names for the columns.  Can be used to retrieve specific columns.
        :type header: list of str
        """
        self._header = []
        self._data = []

        self.__iter_index = 0

        if data:
            assert isinstance(data, list)  # just to be sure no weird errors happen later.
            self._data = list(data)

        if header:
            assert isinstance(header, list)  # just to be sure no weird errors happen later.
            if len(header) != len(data):
                raise ValueError("Number of columns in header and data row don't match.\n  header:  %s\n  data:  %s",
                                 header, data)
            self._header = header  # WARNING:  Keeping reference to avoid multiple copies of the header in a table.

    def get_data(self):
        """
        Returns the data for the row.
        :return: The data for the row as a mutable list (will not change this row).
        :rtype: list of str
        """
        return list(self._data)

    def get_column(self, column):
        """
        Returns a column value from the row.
        :param column: Either an index (int, zero-based) or column name (str)
        :type column: str or int
        :return: The column or raise an exception.
        :rtype: str
        :raises: ValueError
        """
        index = -1
        if isinstance(column, int):
            index = column
        if isinstance(column, str):
            try:
                index = self._header.index(column)
            except ValueError:
                pass  # handled below

        if index < 0 or index > len(self._data):
            raise ValueError("Invalid column %s for row" % column)

        return self._data[index]

    def __repr__(self):
        """
        Returns a pretty version to show.  Data can be reconstructed via a split.
        :return: A printable representation of the data.
        :rtype: str
        """
        return self.__str__()

    def __str__(self):
        """
        Returns a pretty version to print.
        :return: A printable representation of the data.
        :rtype: str
        """
        return "|".join(self._data)

    def __iter__(self):
        """
        Defines an iterator for this class.
        :return: This object as an interator.
        """
        return self

    def next(self):
        """
        Returns the next column of data.
        :return: The next column of data.
        """
        if self.__iter_index >= len(self._data):
            raise StopIteration()

        self.__iter_index += 1
        return self._data[self.__iter_index - 1]

    def __len__(self):
        """
        Returns the number of columns in the data.
        :return: The number of columns in the data.
        """
        return len(self._data)

    def __getitem__(self, key):
        """
        Provice list like indexing.
        :param key: Column number or name.
        :param key: int or str
        :return: The value for the column.
        :rtype: any
        """
        return self.get_column(key)


class DataTable (object):
    """
    Represents a table of data in TQL.  In contrast to the table with metadata.
    """

    def __init__(self, header=None, data=None):
        """
        Creates a new table for holding data.
        :param header: List of names for the columns.  Can be used to retrieve specific columns.
        :type header: list of str
        :param data: An optional list of lists of the data.  All columns must be present in each row.
        :type data: list of list
        """
        self._header = []  # list of column names
        self._rows = []    # list of Rows

        self.__iter_index = 0

        if header:
            assert isinstance(header, list)  # just to be sure no weird errors happen later.
            self._header = list(header)

        if data:
            assert isinstance(data, list)  # just to be sure no weird errors happen later.
            for row in data:
                self._rows.append(Row(header=self._header, data=row))

    def add_row(self, row):
        """
        Adds a row of data.
        :param row: The row to add.
        :type row: list
        """
        return self._rows.append(Row(header=self._header, data=row))

    def get_row(self, row_number):
        """
        Returns a given row of data.
        :param row_number: The row number.
        :type row_number: int
        :return: The row of data for the given row number.
        :rtype: Row
        :raises: ValueError if the row_number is invalid.
        """
        return self._rows[row_number]

    def get_column(self, column):
        """
        Returns a column value from the row.
        :param column: Either an index (int, zero-based) or column name (str)
        :type column: str or int
        :return: The column of data.
        :rtype: str
        :raises: ValueError
        """
        index = -1
        if isinstance(column, int):
            index = column
        if isinstance(column, str):
            try:
                index = self._header.index(column)
            except ValueError:
                pass  # handled below

        if index < 0 or index > len(self._rows):
            raise ValueError("Invalid column %s for row" % column)

        ret_column = []
        for row in self._rows:
            ret_column.append(row[column])

        return ret_column

    def nbr_columns(self):
        """
        Returns the number of columns.
        :return: The number of columns.
        :rtype int:
        """
        return len(self._header)

    def nbr_rows(self):
        """
        Returns the number of rows.
        :return: The number of rows.
        :rtype int:
        """
        return len(self._rows)

    def __repr__(self):
        """
        Returns a pretty version to show.  Data can be reconstructed via a split.
        :return: A printable representation of the data.
        :rtype: str
        """
        return self.__str__()

    def __str__(self):
        """
        Returns a pretty version to print.
        :return: A printable representation of the data.
        :rtype: str
        """
        result="|".join(self._header)
        result += "\n"
        for row in self._rows:
            result += str(row) + "\n"

        return result

    def __iter__(self):
        """
        Defines an iterator for this class.
        :return: This object as an interator.
        """
        return self

    def next(self):
        """
        Returns the next row of data.
        :return: The next row of data.
        """
        if self.__iter_index >= len(self._rows):
            raise StopIteration()

        self.__iter_index += 1
        return self._rows[self.__iter_index - 1]
