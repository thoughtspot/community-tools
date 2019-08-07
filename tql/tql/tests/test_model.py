import unittest

from tql.model import Row, DataTable

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


class TestRow(unittest.TestCase):
    """Tests the Row class."""

    def test_create_empty_row(self):
        """Tests creating a row with no data or header."""
        tr = Row()
        self.assertEqual(tr._data, [])
        self.assertEqual(tr._header, [])
        self.assertEqual(0, len(tr))

    def test_create_row_with_header_and_data(self):
        """Tests creating a row with data and a header."""
        tr = Row(data=[1, 2, 3], header=["col1", "col2", "col3"])
        self.assertEqual(3, len(tr))

        # get with index
        self.assertEqual(1, tr.get_column(0))
        self.assertEqual(2, tr.get_column(1))
        self.assertEqual(3, tr.get_column(2))

        with self.assertRaises(ValueError):
            tr.get_column(6)

        # get with header names
        self.assertEqual(1, tr.get_column("col1"))
        self.assertEqual(2, tr.get_column("col2"))
        self.assertEqual(3, tr.get_column("col3"))

        with self.assertRaises(ValueError):
            tr.get_column("colx")

        # get with invalid type
        with self.assertRaises(ValueError):
            tr.get_column(3.14)

    def test_list_indexing(self):
        """Tests getting data with index notation."""
        tr = Row(data=[1, 2, 3], header=["col1", "col2", "col3"])
        self.assertEqual(3, len(tr))

        # get with index
        self.assertEqual(1, tr[0])
        self.assertEqual(2, tr[1])
        self.assertEqual(3, tr[2])

        with self.assertRaises(ValueError):
            print(tr[6])

        # get with header names
        self.assertEqual(1, tr["col1"])
        self.assertEqual(2, tr["col2"])
        self.assertEqual(3, tr["col3"])

        with self.assertRaises(ValueError):
            print(tr["colx"])

    def test_iteration(self):
        """Test iterating over the row."""
        total = 0
        for val in Row([1, 2, 3]):
            total += val

        self.assertEqual(6, total)


class TestDataTable(unittest.TestCase):
    """Tests the DataTable class."""

    def test_create_empty_table(self):
        """Tests creating an empty table."""
        table = DataTable()
        self.assertEqual(0, table.nbr_columns())
        self.assertEqual(0, table.nbr_rows())

    def test_create_table_no_rows(self):
        """Tests creating an empty table with no data."""
        table = DataTable(header=["col1", "col2", "col3"])
        self.assertEqual(3, table.nbr_columns())
        self.assertEqual(0, table.nbr_rows())

    def test_create_table_with_rows(self):
        """Tests creating an empty table with no data."""
        data = [[1, 2, 3], [4, 5, 6]]
        table = DataTable(header=["col1", "col2", "col3"], data=data)
        self.assertEqual(3, table.nbr_columns())
        self.assertEqual(2, table.nbr_rows())

    def test_create_table_add_data(self):
        """Tests creating an empty table and adding data (good and bad)."""
        table = DataTable(header=["col1", "col2", "col3"])
        self.assertEqual(3, table.nbr_columns())
        self.assertEqual(0, table.nbr_rows())

        table.add_row([1, 2, 3])
        self.assertEqual(1, table.nbr_rows())
        table.add_row([4, 5,6])
        self.assertEqual(2, table.nbr_rows())

        with self.assertRaises(AssertionError):
            table.add_row([1, 2])

    def test_table_iteration(self):
        """Tests iterating over the rows of a table."""
        data = [[1, 2, 3], [4, 5, 6]]
        table = DataTable(header=["col1", "col2", "col3"], data=data)

        total = 0
        for row in table:
            for column in row:
                total += column

        self.assertEqual(1+2+3+4+5+6, total)
