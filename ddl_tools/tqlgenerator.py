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
from datamodel import Table, Column, ForeignKey, GenericRelationship, DatamodelConstants

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
        string = (', ').join((('"{0}"').format(v) for v in a_list))
    else:
        string = (', ').join((('{0}').format(v) for v in a_list))
    return string


class TQLCommandGenerator:
    """
    Creates TQL commands that can be written to output or files.  Newlines are included in commands.
    TODO:  Decide if we want to make newlines optional based on a flag.
    """

    def __init__(self, uppercase=False, lowercase=False, camelcase=False):
        """
        Creates a new TQLWriter to write database models to TQL.
        :param uppercase: Converts all names to uppercase.
        :type uppercase: bool
        :param lowercase: Converts all names to lowercase.
        :type lowercase: bool
        :param lowercase: Converts all names to lowercase.
        :type lowercase: bool
        :param camelcase: Converts all names to camelcase.
        :type camelcase: bool
        """
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.camelcase = camelcase

    def to_case(self, string):
        """
        Converts the string to the proper case based on setting.
        :param string: The string to potentially convert.
        :type string: str
        :return: The string in the appropriate case.
        :rtype: str
        """
        if string == DatamodelConstants.DEFAULT_SCHEMA:
            return string
        if self.lowercase:
            return string.lower()
        if self.uppercase:
            return string.upper()
        if self.camelcase:
            return TQLCommandGenerator.to_camel(string)
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
        newval = val.strip('_')
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

    def generate_create_database_statement(self, database_name):
        """
        Returns a CREATE DATABASE statement.
        :param database_name: Name of the database to create.
        :return:  A TQL CREATE DATABASE statement.
        """
        db_name = self.to_case(database_name)
        cmd = 'CREATE DATABASE "%s";\n' % db_name
        return cmd

    def generate_use_database_statement(self, database_name):
        """
        Returns a USE <database_name> statement.
        :param database_name: Name of the database to use.
        :return:  A TQL USE database statement.
        """
        db_name = self.to_case(database_name)
        cmd = 'USE "%s";\n' % db_name
        return cmd

    def generate_create_schema_statement(self, schema_name):
        """
        Returns a CREATE SCHEMA statement.
        :param schema_name: Name of the schema to create.
        :return:  A TQL CREATE SCHEMA statement.
        """
        name = self.to_case(schema_name)
        cmd = 'CREATE SCHEMA "%s";\n' % name
        return cmd

    def generate_create_table_statement(self, table):
        """
        Returns a CREATE TABLE statement.
        :param table:  The table to create.
        :type table:  Table
        :return: A TQL CREATE TABLE statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'CREATE TABLE "%s"."%s" (\n' % (schema_name, table_name)
        first = True
        for column in table:
            column_name = column.column_name
            if self.lowercase:
                column_name = column_name.lower()
            else:
                if self.uppercase:
                    column_name = column_name.upper()
            if first:
                cmd += '    "%s" %s\n' % (column_name, column.column_type)
                first = False
            else:
                cmd += '   ,"%s" %s\n' % (column_name, column.column_type)

        if len(table.primary_key) != 0:
            key = list_to_string(table.primary_key, quote=True)
            cmd += '   ,CONSTRAINT PRIMARY KEY (%s)\n' % key
        if table.shard_key is not None:
            key = list_to_string(table.shard_key.shard_keys, quote=True)
            cmd += ') PARTITION BY HASH(%d) KEY(%s);\n' % (table.shard_key.number_shards, key)
        else:
            cmd += ');\n'
        return cmd

    def generate_drop_table_statement(self, table):
        """
        Returns a DROP TABLE statement.
        :param table:  The table to create.
        :type table:  Table
        :return: A TQL DROP TABLE statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'DROP TABLE "%s"."%s";\n' % (schema_name, table_name)
        return cmd

    def generate_add_primary_key_statement(self, table, primary_key):
        """
        Returns an ALTER TABLE ... ADD CONSTRAINT PRIMARY KEY statement.
        :param table:  The table to add the primary key to.
        :type table:  Table
        :return: An ALTER TABLE ... ADD CONSTRAINT PRIMARY KEY statement.
        :param primary_key: The primary key to add.
        :type primary_key: list of str
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" ADD CONSTRAINT PRIMARY KEY (%s);\n' % (
         schema_name, table_name, list_to_string(primary_key, quote=True))
        return cmd

    def generate_drop_primary_key_statement(self, table):
        """
        Returns an ALTER TABLE ... DROP CONSTRAINT PRIMARY KEY statement.
        :param table:  The table to drop the primary key from.
        :type table:  Table
        :return: An ALTER TABLE ... DROP CONSTRAINT PRIMARY KEY statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" DROP CONSTRAINT PRIMARY KEY;\n' % (schema_name, table_name)
        return cmd

    def generate_add_hash_key_statement(self, table, number_shards, hash_key):
        """
        Returns an ALTER TABLE ... SET FACT ... statement.
        :param table:  The table to add the hash key to.
        :type table:  Table
        :return: An ALTER TABLE ... SET FACT ... statement.
        :param number_shards: The number of shards to use.
        :type number_shards: int
        :param hash_key: The hash key to add.
        :type hash_key: list of str
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" SET FACT PARTITION BY HASH (%d) KEY (%s);\n' % (
         schema_name, table_name, number_shards, list_to_string(hash_key, quote=True))
        return cmd

    def generate_drop_hash_key_statement(self, table):
        """
        Returns an ALTER TABLE ... SET DIMENSION statement.
        :param table:  The table to drop the hash key from.
        :type table:  Table
        :return: An ALTER TABLE ... SET DIMENSION statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" SET DIMENSIONS;\n' % (schema_name, table_name)
        return cmd

    def generate_add_foreign_key_statement(self, table, foreign_key):
        """
        Returns an ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ... statement.
        :param table:  The table to add the foreign key to.
        :type table:  Table
        :return: An ALTER TABLE ... SET FACT ... statement.
        :param foreign_key: The foreign key to add.
        :type foreign_key: ForeignKey
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" ADD CONSTRAINT FOREIGN KEY "%s" (%s) REFERENCES "%s" (%s);\n' % (
         schema_name, table_name, foreign_key.name, list_to_string(foreign_key.from_keys, quote=True),
         foreign_key.to_table, list_to_string(foreign_key.to_keys, quote=True))
        return cmd

    def generate_add_relationship_constraint_statement(self, table, relationship):
        """
        Returns an ALTER TABLE ... ADD RELATIONSHIP ... statement.
        :param table:  The table to add the relationship to.
        :type table:  Table
        :return: An ALTER TABLE ... ADD RELATIONSHIP ... statement.
        :param relationship: The relationship to add.
        :type relationship: GenericRelationship
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" ADD RELATIONSHIP "%s" WITH "%s" AS %s;\n' % (
         schema_name, table_name, relationship.name,
         relationship.to_table, relationship.conditions)
        return cmd

    def generate_drop_constraint_statement(self, table, constraint_name):
        """
        Returns an ALTER TABLE ... DROP CONSTRAINT statement.
        :param table:  The table to drop the foreign key from.
        :type table:  Table
        :param constraint_name: Name of the foreign key to drop.
        :type constraint_name:  str
        :return: An ALTER TABLE ... DROP CONSTRAINT statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" DROP CONSTRAINT "%s";\n' % (schema_name, table_name, constraint_name)
        return cmd

    def generate_add_column_statement(self, table, column):
        """
        Returns an ALTER TABLE ... ADD COLUMN statement.
        :param table:  The table to add the column to.
        :type table:  Table
        :param column: The column being added.
        :type column:  Column
        :return: An ALTER TABLE ... ADD COLUMN statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" ADD COLUMN "%s" %s DEFAULT ' % (schema_name, table_name,
         column.column_name, column.column_type)
        if column.column_type.startswith('VARCHAR'):
            cmd += "''"
        else:
            cmd += '0'
        cmd += ';\n'
        return cmd

    def generate_modify_column_statement(self, table, column):
        """
        Returns an ALTER TABLE ... MODIFY COLUMN statement.
        :param table:  The table to modify the column of.
        :type table:  Table
        :param column: The column as it should look.
        :type column:  Column
        :return: An ALTER TABLE ... MODIFY COLUMN statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" MODIFY COLUMN "%s" %s;\n' % (schema_name, table_name,
         column.column_name, column.column_type)
        return cmd

    def generate_drop_column_statement(self, table, column):
        """
        Returns an ALTER TABLE ... DROP COLUMN statement.
        :param table:  The table from which to drop the column.
        :type table:  Table
        :param column: The column being dropped.
        :type column:  Column
        :return: An ALTER TABLE ... DROP COLUMN statement.
        :rtype: str
        """
        table_name = self.to_case(table.table_name)
        schema_name = self.to_case(table.schema_name)
        cmd = 'ALTER TABLE "%s"."%s" DROP COLUMN "%s";\n' % (schema_name, table_name, column.column_name)
        return cmd

    def generate_foreign_key_statement(self, table, foreign_key):
        """
        Returns an alter table statement for adding foreign keys.  These should come after table creation.
        :param table: The table containing the foreign key.
        :type table: Table
        :param foreign_key: The foreign key to create an ALTER statement for.
        :type foreign_key: ForeignKey
        :return: A TQL ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY statement.
        :rtype: list of str
        """
        schema_name = self.to_case(table.schema_name)
        from_table = self.to_case(foreign_key.from_table)
        from_key_str = list_to_string(foreign_key.from_keys, quote=True)
        to_table = self.to_case(foreign_key.to_table)
        to_key_str = list_to_string(foreign_key.to_keys, quote=True)
        cmd = 'ALTER TABLE "%s"."%s" ADD CONSTRAINT "%s" FOREIGN KEY (%s) REFERENCES "%s"."%s" (%s);\n' % (
         schema_name,
         from_table,
         foreign_key.name,
         from_key_str,
         schema_name,
         to_table,
         to_key_str)
        return cmd

    def generate_relationships(self, table, relationship):
        """
        Returns an alter table statement for relationships.  These should come after table creation.
        :param table: The table with the generic relationships.
        :type table: Table
        :param relationship: The generic relationship to create the ALTER statement for.
        :type relationship: GenericRelationship
        """
        schema_name = self.to_case(table.schema_name)
        from_table = self.to_case(relationship.from_table)
        to_table = self.to_case(relationship.to_table)
        cmd = 'ALTER TABLE "%s"."%s" ADD RELATIONSHIP "%s" WITH "%s"."%s" AS %s;\n' % (
         schema_name,
         from_table,
         relationship.name,
         schema_name,
         to_table,
         relationship.conditions)
        return cmd
# okay decompiling tqlgenerator.pyc
