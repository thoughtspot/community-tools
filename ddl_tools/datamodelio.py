"""
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

import re
import sys
import xlrd  # reading Excel
# import datetime -- used by TsloadWriter, but commented out for now.
import csv
import os
from openpyxl import Workbook  # writing Excel
from datamodel import Database, Table, Column, ShardKey, DatamodelConstants, eprint


# -------------------------------------------------------------------------------------------------------------------


def list_to_string(a_list, quote=False):
    """
    Converts a list to a set of strings separated by a comma.
    :param a_list: The list to convert.
    :type a_list: list
    :param quote: If true, then surround each item with quotes.
    :type quote: bool
    :return: The string version of the list.  
    """
    if quote:
        string = ", ".join('"{0}"'.format(v) for v in a_list)
    else:
        string = ", ".join('{0}'.format(v) for v in a_list)

    return string


# -------------------------------------------------------------------------------------------------------------------


class DDLParser(object):
    """
    Parses DDL from various formats and creates a DataModel object that can be used for writing data.
    The following assumptions are made about the DDL being read:
    * CREATE TABLE occur together on a single line, not split across lines.
    * CREATE TABLE statements will not occur inside of a comment block.
    * Delimiters, such as commas, will not be part of the table or column name.
    * Comment characters, such as #, --, or /* */ will not be part of a column name.
    * CREATE TABLE will have (....) with no embedded, unbalanced parentheses.
    
    """

    # TODO: capture primary keys, foreign keys, and relationships.

    def __init__(self, database_name, schema_name=DatamodelConstants.DEFAULT_SCHEMA, parse_keys=False):
        """
        Creates a new DDL parser.
        :param database_name: Name of the database to create.
        :type database_name: str
        :param schema_name: Name of the schema if not using the default.
        :param parse_keys: If true, the parser will attempt to parse keys as well. 
        :type parse_keys: bool
        :type schema_name: str
        """
        self.schema_name = schema_name
        self.database = Database(database_name=database_name)
        self.parse_keys = parse_keys

    def parse_ddl(self, stream):
        """
        Parsed DDL from a stream and returns a populated Database.
        :param stream: An input stream to read from.
        :return: A Database object.
        :rtype: Database
        """

        # First read the entire input into memory.  This will allow multiple passes through the data.
        input_ddl = []
        for line in stream:
            input_ddl.append(line)

        self.parse_tables(input_ddl)
        if self.parse_keys:
            self.parse_primary_keys(input_ddl)

        return self.database

    def parse_tables(self, input_ddl):
        """
        Parses the input DDL to convert to a database model.
        :param input_ddl: The DDL to convert.
        :type input_ddl: list of str
        """
        creating = False
        buff = ""
        for line in input_ddl:
            l = self.clean_line(line)

            if not creating:  # looking for CREATE TABLE statement.
                if l.lower().find("create table") >= 0:
                    creating = True
                    buff = l
                    if self.is_complete_create(buff):
                        self.parse_create_table(buff)
                        buff = ""
                        creating = False
            else:  # looking for the end of a create table.
                buff += l
                if self.is_complete_create(buff):
                    # print(buff)
                    self.parse_create_table(buff)
                    buff = ""
                    creating = False

    @staticmethod
    def is_complete_create(buff):
        """
        Returns true if the number of open and close parentheses match.
        :param buff: The buffer being read.
        :return: str
        """
        nbr_open = buff.count('(')
        nbr_close = buff.count(')')
        return nbr_open > 0 and nbr_open == nbr_close

    def parse_create_table(self, buff):
        """
        Parses a create table statement.
        :param buff: The buffer read in.
        :type buff: str
        :return: 
        """
        buff = buff.replace("[", "\"").replace("]", "\"")  # for SQL Server quotes
        table_name = self.get_table_name(buff)
        columns = self.get_columns(buff)

        table = Table(table_name=table_name, schema_name=self.schema_name)
        table.add_columns(columns)
        self.database.add_table(table)

    def get_table_name(self, buff):
        """
        Gets the table name from the buffer.
        :param buff: The line with the create details.
        :type buff: str
        :return: The name of the table.
        :rtype: str
        """
        # The table name (and maybe a schema) are before the opening (
        tn = buff[0:buff.find('(')].rstrip()
        # split on spaces and assume last one is table name (and maybe schema)
        tn = tn.split(' ')[-1]
        tn = tn.split(".")[-1]
        tn = self.strip_quotes(tn)
        return tn

    @staticmethod
    def strip_quotes(line):
        """
        Strips off any quotes in the given line.
        :param line: The line to strip quotes from.
        :type line: str
        :return: The line without quotes.
        :rtype: str
        """
        return line.replace("'", "").replace("`", "").replace("\"", "")

    def get_columns(self, buff):
        """
        Get the columns from the table statement.
        :param buff: The buffer with the create details.
        :type buff: str
        :return: A list of Columns
        :rtype: list
        """
        # The fields will be between the ( ).
        columns = []
        buff = buff[buff.find('(') + 1:buff.rfind(')')].strip()

        # think all DBs use commas for field separators
        # need to find the commas that are not inside of parents.
        field_buff = ""
        open_paren = False
        raw_fields = []

        for c in buff:

            if open_paren:
                field_buff += c
                if c == ')':
                    open_paren = False
            elif c == '(':
                field_buff += c
                open_paren = True
            else:
                if c == ',':
                    raw_fields.append(field_buff)
                    field_buff = ""
                else:
                    field_buff += c

        if field_buff != "":
            raw_fields.append(field_buff)

        for rf in raw_fields:
            rfl = rf.lower()
            # ignore key declarations.
            if "key " in rfl:
                continue

            had_quote = False
            if rfl[0] in "\"'`":  # should be a quote or letter
                had_quote = True
                name = rf[1:rf.find(rf[0], 1)]
            else:
                name = rf[0:rf.find(' ')]

            # The type comes after the name and goes up to the first of a
            #   space, close paren, or comma.  Assuming no space in type.
            start_idx = len(name) + (3 if had_quote else 1)  # extra 1 for space
            if rfl.find(')') > 0:  # type with ()
                data_type = rf[start_idx:rf.find(')') + 1]
            else:
                # either next space or comma.
                space_end_idx = rf.find(' ', start_idx)
                comma_end_idx = rf.find(',', start_idx)
                if space_end_idx == -1:  # not found
                    if comma_end_idx == -1:  # neither found
                        end_idx = len(rf)  # end of line
                    else:
                        end_idx = comma_end_idx
                elif comma_end_idx == -1:
                    end_idx = space_end_idx
                else:
                    end_idx = min(space_end_idx, comma_end_idx)
                data_type = rf[start_idx:end_idx]

            # print ("  adding %s as %s" % (name, data_type))
            columns.append(Column(column_name=name, column_type=self.convert_type(data_type)))

        return columns

    @staticmethod
    def convert_type(data_type):
        """
        Converts data types from other databases to ThoughtSpot types.
        :param data_type:  The datatype to convert.
        :type data_type: str
        :return: A ThoughtSpot data type.
        :rtype: str
        """
        if ')' in data_type:
            t = data_type[0:data_type.find(')') + 1]
        elif " " in data_type:
            t = data_type[0:data_type.find(' ') + 1]
        else:
            t = data_type

        t = t.lower()

        if "int" in t:
            new_t = "BIGINT"
        elif "rowversion" in t:  # MS type
            new_t = "INT"
        elif "uniqueidentifier" in t:  # Oracle type
            new_t = "VARCHAR(0)"
        elif "serial" in t:  # serial index, Oracle and others
            new_t = "INT"
        elif "bit" in t:
            new_t = "BOOL"
        elif "blob" in t or "binary" in t:
            new_t = "UNKNOWN"
        elif "number" in t:  # support for NUMBER(1), NUMBER(1,1)
            if ')' in t:
                numsize = t[t.find('(') + 1:t.find(')')]
                if "," in numsize:
                    first_num, second_num = numsize.split(",")
                    if second_num.strip() == "0":
                        if int(first_num) > 9:
                            new_t = "BIGINT"
                        else:
                            new_t = "INT"
                    else:
                        new_t = "DOUBLE"
                else:
                    new_t = "INT"
            else:
                new_t = "BIGINT"
        elif "decimal" in t or "numeric" in t or \
             "float" in t or "double" in t or "money" in t or "real" in t:
            new_t = "DOUBLE"
        elif "datetime" in t:
            new_t = "DATETIME"
        elif "timestamp" in t:
            new_t = "DATETIME"
        elif "time" in t:
            new_t = "TIME"
        elif "date" in t:
            new_t = "DATE"
        elif "bool" in t:
            new_t = "BOOL"
        elif "text" in t:
            new_t = "VARCHAR(0)"
        elif "char" in t:
            nbytes = 0
            if ')' in t:
                nbytes = t[t.find('(') + 1:t.find(')')]
                nbytes = re.sub("[^0-9]", "", nbytes)
                if nbytes == "":
                    nbytes = 0
            new_t = "VARCHAR(%s)" % nbytes
        else:
            new_t = "UNKNOWN"

        return new_t

    def parse_primary_keys(self, input_ddl):
        """
        Parses primary keys (and shard keys for TQL.
        :param input_ddl: The input DDL to parse from.
        :type input_ddl: list of str
        """
        # read through lines until a CREATE TABLE or ALTER TABLE is found.
        # next look for either a new CREATE TABLE, a PRIMARY KEY, or PARTITION BY HASH
        # add the primary key or partition

        # TODO - get this to work.
        create_or_update = False
        buff = ""
        for line in input_ddl:
            l = self.clean_line(line)

            if not create_or_update:  # looking for CREATE TABLE or UPDATE TABLE statement.
                if l.lower().find("create table") >= 0 or l.lower().find("update table") >= 0:
                    create_or_update = True
                    buff = l
                    if self.is_complete_create(buff):
                        self.parse_create_table(buff)
                        buff = ""
                        create_or_update = False
            else:  # looking for the end of a create table.
                buff += l
                if self.is_complete_create(buff):
                    # print(buff)
                    self.parse_create_table(buff)
                    buff = ""
                    create_or_update = False

        pass

    @staticmethod
    def clean_line(line):
        """
        Removes unwanted characters from the input line.
        :param line:  The line to clean up.
        :type line: str
        :return: The cleaned up line.
        :rtype: str
        """
        l = line.strip()
        l = re.sub(' +', ' ', l)
        l = re.sub('\t+', ' ', l)
        return l


# -------------------------------------------------------------------------------------------------------------------


class TQLWriter:
    """
    Writes TQL from a data model.
    """

    def __init__(self, uppercase=False, lowercase=False, camelcase=False, create_db=False):
        """
        Creates a new TQLWriter to write database models to TQL.
        :param uppercase: Converts all names to uppercase.
        :type uppercase: bool
        :param lowercase: Converts all names to lowercase.  overrides uppercase if set.
        :type lowercase: bool
        :param create_db: Writes create statements for the database.
        :type create_db: bool
        """
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.camelcase = camelcase
        self.create_db = create_db

    def to_case(self, string):
        """
        Converts the string to the proper case based on setting.
        :param string: The string to potentially convert.
        :type string: str
        :return: The string in the appropriate case.
        :rtype: str
        """

        # Exceptions.  Currently on the default schema.
        if string == DatamodelConstants.DEFAULT_SCHEMA:
            return string

        if self.lowercase:
            return string.lower()
        elif self.uppercase:
            return string.upper()
        elif self.camelcase:
            return TQLWriter.to_camel(string)

        return string

    @staticmethod
    def to_camel(val):
        """
        Converts names of the form xxx_yyy to XxxYyy.  
        This is occasionally requested for converting database and table names.
        :param val: The string to convert.
        :type val: str
        :return: The new string in CamelCase.
        :rtype: str
        """
        newval = val.strip("_")
        results = newval[0].upper()
        idx = 1
        while idx < len(newval):
            if newval[idx] != '_':
                results += newval[idx]
                idx += 1
            else:
                idx += 1
                if idx < len(newval):
                    results += newval[idx].upper()
                idx += 1

        return results

    def write_tql(self, database, outfile=None):
        """
        Main function to write the Database to TQL.
        :param database: The database object to convert.
        :type database: Database
        :param outfile: File to write to or STDOUT is not set.  The caller is expected to close the output stream.
        """

        if outfile is None:
            outfile = open(sys.stdout, "w")

        db_name = self.to_case(database.database_name)

        if self.create_db:
            outfile.write('CREATE DATABASE "%s";\n' % db_name)

        # sets to use the database.
        outfile.write('USE "%s";\n' % db_name)

        # create the database if that was an option.
        if self.create_db:
            for schema_name in database.get_schema_names():
                if schema_name != DatamodelConstants.DEFAULT_SCHEMA:
                    outfile.write('CREATE SCHEMA "%s";\n' % schema_name)

        for table in database:
            self.write_create_table_statement(table, outfile)

        for table in database:
            self.write_foreign_keys(table, outfile)

        for table in database:
            self.write_relationships(table, outfile)

    def write_create_table_statement(self, table, outfile):
        """
        Writes a CREATE TABLE statement.
        :param table:  The table to create.
        :type table:  Table
        :param outfile: File stream to write to.
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)

        outfile.write('\n')
        outfile.write('DROP TABLE "%s"."%s";\n' % (schema_name, table_name))
        outfile.write('\n')
        outfile.write('CREATE TABLE "%s"."%s" (\n' % (schema_name, table_name))

        first = True
        for column in table:

            column_name = column.column_name
            if self.lowercase:
                column_name = column_name.lower()
            elif self.uppercase:
                column_name = column_name.upper()

            if first:
                outfile.write('    "%s" %s\n' % (column_name, column.column_type))
                first = False
            else:
                outfile.write('   ,"%s" %s\n' % (column_name, column.column_type))

        if len(table.primary_key) != 0:
            key = list_to_string(table.primary_key, quote=True)
            outfile.write('   ,CONSTRAINT PRIMARY KEY (%s)\n' % key)

        if table.shard_key is not None:
            key = list_to_string(table.shard_key.shard_keys, quote=True)
            outfile.write(') PARTITION BY HASH(%d) KEY(%s);' %
                          (table.shard_key.number_shards, key))
        else:
            outfile.write(');\n')

        outfile.write('\n')

    def write_foreign_keys(self, table, outfile):
        """
        Writes alter table statements for foreign keys.  These should come after table creation.
        :param table: The table with the FK relationships.
        :type table: Table
        :param outfile: The file to write to.
        """
        for fk in table.foreign_keys.values():
            schema_name = self.to_case(table.schema_name)
            from_table = self.to_case(fk.from_table)
            from_key_str = list_to_string(fk.from_keys, quote=True)
            to_table = self.to_case(fk.to_table)
            to_key_str = list_to_string(fk.to_keys, quote=True)

            outfile.write('ALTER TABLE "%s"."%s" ADD CONSTRAINT "%s" FOREIGN KEY (%s) REFERENCES "%s"."%s" (%s);\n' %
                          (schema_name, from_table, fk.name, from_key_str, schema_name, to_table, to_key_str))

    def write_relationships(self, table, outfile):
        """
        Writes alter table statements for relationships.  These should come after table creation.
        :param table: The table with the generic relationships.
        :type table: Table
        :param outfile: The file to write to.
        """
        for rel in table.relationships.values():
            schema_name = self.to_case(table.schema_name)
            from_table = self.to_case(rel.from_table)
            to_table = self.to_case(rel.to_table)

            outfile.write('ALTER TABLE "%s"."%s" ADD RELATIONSHIP "%s" WITH "%s"."%s" AS %s;\n' %
                          (schema_name, from_table, rel.name, schema_name, to_table, rel.conditions))


# -------------------------------------------------------------------------------------------------------------------


class XLSWriter:
    """
    Writes data from a database to Excel.
    """
    EXTENSION = ".xlsx"

    def __init__(self):
        """
        Creates a new writer can write models to an Excel workbook.
        """
        self.workbook = Workbook()

    def write_database(self, database, filename):
        """
        Write the database to an Excel file.
        :param database:  The database object to write to Excel.
        :type database: Database
        :param filename:  Name of the Excel file without extension.
        :type filename: str
        """
        self._write_columns_worksheet(database)
        self._write_tables_worksheet(database)
        self._write_foreign_keys_worksheet(database)
        self._write_relationships_worksheet(database)
        self._write_to_excel(filename)

    def _write_columns_worksheet(self, database):
        """
        Writes the worksheet with the columns for each table.
        :param database: The database to write.
        :type database: Database
        """

        ws = self.workbook.active  # assumes this is the first sheet.
        ws.title = "Columns"

        # Write the header row.
        self._write_header(ws=ws, cols=["Database", "Schema", "Table", "Column", "Name", "Type"])

        # Write the data.
        row_cnt = 1
        for table in database:
            col_idx = 0
            for column in table:
                col_idx += 1
                row_cnt += 1
                self._write_row(ws=ws, row_cnt=row_cnt, cols=[database.database_name, table.schema_name,
                                                              table.table_name, col_idx, column.column_name,
                                                              column.column_type])

    def _write_tables_worksheet(self, database):
        """
        Writes the table(s) details to the table worksheet.
        :param database:  Database with the tables.
        :type database: Database
        """

        ws = self.workbook.create_sheet(title="Tables")
        self._write_header(ws=ws, cols=["Database", "Schema", "Table", "Updated", "Update Type", "# Rows", "# Columns",
                                        "Primary Key", "Shard Key", "# Shards", "RLS Column"])
        # Write the data.
        row_cnt = 1
        for table in database:
            row_cnt += 1
            lookup_formula = "=COUNTIFS(Columns!A:A,Tables!A%d, Columns!B:B,Tables!B%d, Columns!C:C,Tables!C%d)" % (
                row_cnt, row_cnt, row_cnt)

            primary_key = ""
            if table.primary_key is not None:
                primary_key = list_to_string(table.primary_key)

            shard_key = ""
            number_shards = ""
            if table.shard_key is not None:
                shard_key = list_to_string(table.shard_key.shard_keys)
                number_shards = table.shard_key.number_shards

            # TODO add support for update frequency so that it's remembered during development.
            self._write_row(ws, row_cnt, [database.database_name, table.schema_name, table.table_name,
                                          "daily", "partial", "", lookup_formula,
                                          primary_key, shard_key, number_shards, ""])

    def _write_foreign_keys_worksheet(self, database):
        """
        Writes the relationship details (FKs and generic relationships) worksheet.
        :param database: 
        :type database: Database
        """
        ws = self.workbook.create_sheet(title="Foreign Keys")
        # Assuming relationships can only be within a single schema.
        self._write_header(ws, ["Name", "Database", "Schema", "From Table", "From Columns", "To Table", "To Columns"])

        row_cnt = 0
        for table in database:
            row_cnt += 1

            for fk in table.foreign_keys_iter():
                from_column = list_to_string(fk.from_keys)
                to_column = list_to_string(fk.to_keys)
                self._write_row(ws, row_cnt, [fk.name, database.database_name, table.schema_name,
                                              fk.from_table, from_column, fk.to_table, to_column])

    def _write_relationships_worksheet(self, database):
        """
        Writes the relationship details (FKs and generic relationships) worksheet.
        :param database: 
        :type database: Database
        """
        ws = self.workbook.create_sheet(title="Relationships")
        # Assuming relationships can only be within a single schema.
        self._write_header(ws, ["Name", "Database", "Schema", "From Table", "To Table", "Conditions"])

        row_cnt = 0
        for table in database:
            row_cnt += 1

            for rel in table.relationships_iter():
                self._write_row(ws, row_cnt, [rel.name, database.database_name, table.schema_name,
                                              rel.from_table, rel.to_table, rel.conditions])

    @staticmethod
    def _write_header(ws, cols):
        """
        Writes the header for a worksheet.
        :param ws: The worksheet to write to.
        :param cols: The column headers to write.
        """
        for ccnt in range(0, len(cols)):
            ws.cell(column=(ccnt + 1), row=1, value=cols[ccnt])
            # TODO add formatting to distinguish the header.

    @staticmethod
    def _write_row(ws, row_cnt, cols):
        """
        Writes a row of data.
        :param ws: The worksheet to write to.
        :param row_cnt: The row to write to.
        :param cols: The columns to write.
        """
        for ccnt in range(0, len(cols)):
            ws.cell(column=(ccnt + 1), row=row_cnt, value=cols[ccnt])

    def _write_to_excel(self, filename):
        """
        Writes the data to an Excel file.
        :param filename: The name of the file (without extension) to write to.
        """
        if not filename.endswith(XLSWriter.EXTENSION):
            filename = filename + XLSWriter.EXTENSION

        self.workbook.save(filename)


# -------------------------------------------------------------------------------------------------------------------


class XLSReader:
    """
    Reads data models from an Excel file.  Note that this file follows a very specific format.  
    See test_excel_reader.xlsx for an example of the format.
    Note that this can return multiple databases. 
    Note that multiple tables with the same name in different schemas are not currently supported.
    """
    required_sheets = ["Columns", "Tables", "Foreign Keys", "Relationships"]
    required_columns = {
        "Columns": ["Database", "Schema", "Table", "Column", "Name", "Type"],
        "Tables": ["Database", "Schema", "Table", "Updated", "Update Type", "# Rows", "# Columns",
                   "Primary Key", "Shard Key", "# Shards", "RLS Column"],
        "Foreign Keys": ["Name", "Database", "Schema", "From Table", "From Columns", "To Table", "To Columns"],
        "Relationships": ["Name", "Database", "Schema", "From Table", "To Table", "Conditions"]
    }

    def __init__(self):
        """Creates a new Excel reader."""
        # Column indices for each sheet to make reading of values based on column header.
        self.workbook = None
        self.indices = {}
        self.databases = {}

    def read_xls(self, filepath):
        """
        Reads an Excel file at the given path and returns a dictionary with one or more database keyed by name.
        :param filepath: The path to the Excel document.
        :type filepath: str
        :return: A Database object based on the contents of the Excel document.
        :rtype: dict of str:Database
        """
        self.workbook = xlrd.open_workbook(filepath)
        if self._verify_file_format():
            self._read_databases_from_workbook()
        return self.databases

    def _verify_file_format(self):
        """
        Verifies that the Excel document has the correct tabs and column headers.
        :return: True if the workbook has the correct worksheets and columns in each.
        :rtype: bool
        """

        is_valid = True  # hope for the best.

        sheet_names = self.workbook.sheet_names()
        for required_sheet in XLSReader.required_sheets:
            if required_sheet not in sheet_names:
                eprint("Error:  missing sheet %s!" % required_sheet)
                is_valid = False
            else:
                sheet = self.workbook.sheet_by_name(required_sheet)
                header_row = sheet.row_values(rowx=0, start_colx=0)
                for required_column in XLSReader.required_columns[required_sheet]:
                    if required_column not in header_row:
                        eprint("Error:  missing column %s in sheet %s!" % (required_column, required_sheet))
                        is_valid = False

        return is_valid

    def _get_column_indices(self):
        """
        Reads the sheets to get all of the column indices.  Assumes the format is valid.
        """

        sheet_names = self.workbook.sheet_names()
        for sheet_name in sheet_names:
            if sheet_name in self.required_sheets:
                sheet = self.workbook.sheet_by_name(sheet_name)
                col_indices = {}
                ccnt = 0
                for col in sheet.row_values(rowx=0, start_colx=0):
                    col_indices[col] = ccnt
                    ccnt += 1
                self.indices[sheet_name] = col_indices

    def _read_databases_from_workbook(self):
        """
        Reads one or more database from a workbook.  Errors can still be encountered, but the format should be OK.
        :return: A list of the databases in the file.
        :rtype: dict of Database
        """
        self._get_column_indices()
        self._read_tables_from_workbook()
        self._read_columns_from_workbook()
        self._read_foreign_keys_from_workbook()
        self._read_relationships_from_workbook()

    def _read_tables_from_workbook(self):
        """
        Reads the databases and tables from Excel.  These are used to populate from the remaining sheets.
        """

        # "Tables":        ["Database", "Schema", "Table", "Updated", "Update Type", "# Rows", "# Columns",
        #                   "Primary Key", "Shard Key", "# Shards", "RLS Column"],
        table_sheet = self.workbook.sheet_by_name("Tables")
        indices = self.indices["Tables"]

        for row_count in range(1, table_sheet.nrows):
            row = table_sheet.row_values(rowx=row_count, start_colx=0)

            database_name = row[indices["Database"]]
            database = self.databases.get(database_name, None)
            if database is None:
                database = Database(database_name=database_name)
                self.databases[database_name] = database

            pk = row[indices["Primary Key"]]
            if pk == "":
                pk = None
            else:
                pk = [x.strip() for x in pk.split(',')]

            sk = None
            sk_name = row[indices["Shard Key"]]
            sk_nbr_shards = row[indices["# Shards"]]
            sk = row[indices["Primary Key"]]
            if sk == "":
                sk = None
            else:
                sk = [x.strip() for x in sk_name.split(',')]
            if sk_name != "" and sk_nbr_shards != "":
                sk = ShardKey(shard_keys=sk, number_shards=sk_nbr_shards)

            table = Table(table_name=row[indices["Table"]],
                          schema_name=row[indices["Schema"]],
                          primary_key=pk,
                          shard_key=sk
                          )
            database.add_table(table)

    def _read_columns_from_workbook(self):
        """
        Reads the columns for the tables from Excel.  
        """
        # "Columns":       ["Database", "Schema", "Table", "Column", "Name", "Type"],
        column_sheet = self.workbook.sheet_by_name("Columns")
        indices = self.indices["Columns"]

        for row_count in range(1, column_sheet.nrows):
            row = column_sheet.row_values(rowx=row_count, start_colx=0)

            database_name = row[indices["Database"]]
            database = self.databases.get(database_name, None)
            if database is None:
                eprint("ERROR:  Database %s from the Columns tab is not known." % database_name)

            else:
                table_name = row[indices["Table"]]
                table = database.get_table(table_name)
                if table is None:
                    eprint("ERROR:  Table %s from the Columns tab is not known." % table_name)
                table.add_column(Column(column_name=row[indices["Name"]], column_type=row[indices["Type"]]))

    def _read_foreign_keys_from_workbook(self):
        """
        Reads the foreign keys for the tables from Excel.  
        """

        # "Foreign Keys":  ["Name", "Database", "Schema", "From Table", "Columns", "To Table", "Columns"],
        fk_sheet = self.workbook.sheet_by_name("Foreign Keys")
        indices = self.indices["Foreign Keys"]

        for row_count in range(1, fk_sheet.nrows):
            row = fk_sheet.row_values(rowx=row_count, start_colx=0)

            database_name = row[indices["Database"]]
            database = self.databases.get(database_name, None)
            if database is None:
                eprint("ERROR:  Database %s from the Foreign Keys tab is not known." % database_name)

            else:
                table_name = row[indices["From Table"]]
                table = database.get_table(table_name)
                if table is None:
                    eprint("ERROR:  Table %s from the Foreign Keys tab is not known." % table_name)
                from_keys = row[indices["From Columns"]]
                from_keys = [x.strip() for x in from_keys.split(",")]
                to_keys = row[indices["To Columns"]]
                to_keys = [x.strip() for x in to_keys.split(",")]
                table.add_foreign_key(from_keys=from_keys,
                                      to_table=row[indices["To Table"]],
                                      to_keys=to_keys
                                      )

    def _read_relationships_from_workbook(self):
        """
        Reads the foreign keys for the tables from Excel.  
        """
        # "Relationships": ["Name", "Database", "Schema", "From Table", "To Table", "Conditions"]
        rel_sheet = self.workbook.sheet_by_name("Relationships")
        indices = self.indices["Relationships"]

        for row_count in range(1, rel_sheet.nrows):
            row = rel_sheet.row_values(rowx=row_count, start_colx=0)

            database_name = row[indices["Database"]]
            database = self.databases.get(database_name, None)
            if database is None:
                eprint("ERROR:  Database %s from the Relationships tab is not known." % database_name)

            else:
                table_name = row[indices["From Table"]]
                table = database.get_table(table_name)
                if table is None:
                    eprint("ERROR:  Table %s from the Relationships tab is not known." % table_name)
                table.add_relationship(to_table=row[indices["To Table"]],
                                       conditions=row[indices["Conditions"]]
                                       )


# -------------------------------------------------------------------------------------------------------------------


class TsloadWriter:
    """
    Write the tsload commands with all the flags.
    """

    def __init__(self, default_flags=None):
        """
        Create a tsload writer.
        :param default_flags: this includes the default flags used in tsload command.
        :type default_flags: dict
        """
        self._default_flags = {
            "empty_target": "",
            "max_ignored_rows": "0",
            "skip_second_fraction": "",
            "source_data_format": "",
            "null_value": "",
            "has_header_row": ""
        }
        if default_flags is not None:
            self._default_flags.update(default_flags)

    def write_tsloadcommand(self, database, filename):
        """
        Write tsload command to the file.
        :param database:  The database object to write to Excel.
        :type database: Database
        :param filename:  Name of the Excel file without extension.
        :type filename: str
        """
        with open(filename, "w") as tsload_outfile:

            for table in database:
                flags = self._get_flags_from_csv(database.database_name, table)
                tsload_string = "tsload "
                for flag, value in flags.items():
                    # TODO Add locic or flags without values.
                    tsload_string += '--%s "%s" ' % (flag, value)
                tsload_outfile.write(tsload_string + "\n")

    def _get_flags_from_csv(self, database_name, table):
        """
        This function will read the csv file and determine the flags
        :param database_name: Name of the database
        :type  database_name: str
        :param table: table object
        :type table: Table
        :return: all the dict for the tsload flags.
        :rtype: dict
        """
        flags = self._default_flags.copy()

        flags['target_database'] = database_name
        flags['target_schema'] = table.schema_name
        flags['target_table'] = table.table_name
        flags['source_file'] = table.table_name + '.csv'

        if not os.path.isfile(flags['source_file']):
            return flags

        # todo get default flags from csv

        with open(flags['source_file']) as csv_file:
            csv_reader = csv.DictReader(csv_file)

            for column in table:
                if column.column_type == 'DATE' and flags.get('date_format', None) is None:
                    flags['date_format'] = TsloadWriter._get_date_format(column.column_name, csv_reader)

        return flags

    @staticmethod
    def _get_date_format(column_name, csv_reader):
        """
        :param column_name: Name of the column to get the date format for.
        :type column_name: str
        :param csv_reader: Open file reader.
        :type csv_reader: csv.DictReader
        :return: date_format for tsload command.
        :rtype: str
        """
        # TODO Add logic to determine the actual flag value.

        patterns = ['%Y', '%b %d, %Y', '%b %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%Y/%m/%d', '%m/%d/%y', '%m-%d-%y',
                    '%m-%d-%Y',
                    '%Y-%m-%d', '%y/%m/%d', '%y-%m-%d', '%d/%m/%y', '%d/%m/%Y', '%d-%m-%y', '%d-%m-%Y', '%d%B%y',
                    '%d%b%y',
                    '%d%B%Y', '%d%b%Y']  # all the formats the date

        date_format = '%y/%m/%d'

        # parse = []

        # for fmt in patterns:
        #     try:
        #         dt = datetime.datetime.strptime(v, fmt)
        #         parse.append(fmt)
        #         print parse
        #         break

        #     except ValueError as err:
        #         pass

        # date_format = parse[0]

        return date_format
