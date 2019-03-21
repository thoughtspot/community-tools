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

import logging
from datamodelio import TQLCommandGenerator, smart_open
from datamodel import Database, Table, Column, ShardKey, ForeignKey, GenericRelationship, DatamodelConstants, eprint

# -------------------------------------------------------------------------------------------------------------------


class DatabaseDifference(object):
    """
    Contains the differences in a give database.  This is the result of comparing to a different database.
    """

    # TODO replace the following with an Enum if this code is updated to Python 3.

    # The following are more for internal use.
    UNKNOWN_DIFFERENCE = -1

    DIFFERENCE_DESCRIPTION = {}

    TABLE_CREATED = 0
    DIFFERENCE_DESCRIPTION[TABLE_CREATED] = "Table Created"
    TABLE_DROPPED = 1
    DIFFERENCE_DESCRIPTION[TABLE_DROPPED] = "Table Dropped"

    COLUMN_ADDED = 10
    DIFFERENCE_DESCRIPTION[COLUMN_ADDED] = "Column Added"
    COLUMN_DROPPED = 11
    DIFFERENCE_DESCRIPTION[COLUMN_DROPPED] = "Column Dropped"
    COLUMN_MODIFIED = 12
    DIFFERENCE_DESCRIPTION[COLUMN_MODIFIED] = "Column Modified"

    PRIMARY_KEY_ADDED = 20
    DIFFERENCE_DESCRIPTION[PRIMARY_KEY_ADDED] = "Primary Key Added"
    PRIMARY_KEY_DROPPED = 21
    DIFFERENCE_DESCRIPTION[PRIMARY_KEY_DROPPED] = "Primary Key Dropped"
    PRIMARY_KEY_MODIFIED = 22
    DIFFERENCE_DESCRIPTION[PRIMARY_KEY_MODIFIED] = "Primary Key Modified"

    HASH_KEY_ADDED = 30
    DIFFERENCE_DESCRIPTION[HASH_KEY_ADDED] = "Hash Key Added"
    HASH_KEY_DROPPED = 31
    DIFFERENCE_DESCRIPTION[HASH_KEY_DROPPED] = "Hash Key Dropped"
    HASH_KEY_MODIFIED = 32
    DIFFERENCE_DESCRIPTION[HASH_KEY_MODIFIED] = "Hash Key Modified"

    FOREIGN_KEY_ADDED = 40
    DIFFERENCE_DESCRIPTION[FOREIGN_KEY_ADDED] = "Foreign Key Added"
    FOREIGN_KEY_DROPPED = 41
    DIFFERENCE_DESCRIPTION[FOREIGN_KEY_DROPPED] = "Foreign Key Dropped"
    FOREIGN_KEY_MODIFIED = 42
    DIFFERENCE_DESCRIPTION[FOREIGN_KEY_MODIFIED] = "Foreign Key Modified"

    GENERIC_RELATIONSHIP_ADDED = 50
    DIFFERENCE_DESCRIPTION[GENERIC_RELATIONSHIP_ADDED] = "Generic Relationship Added"
    GENERIC_RELATIONSHIP_DROPPED = 51
    DIFFERENCE_DESCRIPTION[GENERIC_RELATIONSHIP_DROPPED] = "Generic Relationship Dropped"
    GENERIC_RELATIONSHIP_MODIFIED = 52
    DIFFERENCE_DESCRIPTION[GENERIC_RELATIONSHIP_MODIFIED] = "Generic Relationship Modified"

    def __init__(self, diff_type, database, schema_name, table_name, description="None"):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a TABLE_DROPPED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was dropped.
        :param diff_type: Type of difference.
        :type diff_type: int
        :param database: The database modified.
        :type database: Database
        :param schema_name: Name of the schema modified.
        :type schema_name: str
        :param table_name: Name of the table modified.
        :param table_name: str
        :param description: Description of the modification.
        :type description: str
        """
        self.diff_type = diff_type
        self.database = database
        self.schema_name = schema_name
        self.table_name = table_name
        self.description = description

        self.command_generator = TQLCommandGenerator()

    def __repr__(self):
        """
        Provides a string representation for printing.
        :return: A string that can be printed.  This method will most likely be overwritten.
        :rtype: str
        """
        return "%s.%s.%s (%s): %s" % (self.database.database_name, self.schema_name, self.table_name, self.diff_type,
                                      DatabaseDifference.DIFFERENCE_DESCRIPTION[self.diff_type])

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return ""


class TableCreatedDifference(DatabaseDifference):
    """
    Class to handle differences because tables were created.
    """

    def __init__(self, database, table, description=None):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a TABLE_DROPPED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was dropped.
        :param database: Database modified.
        :type database: Database
        :param table: Table being modified
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(TableCreatedDifference, self).__init__(diff_type=DatabaseDifference.TABLE_CREATED,
                                                     database=database, schema_name=table.schema_name,
                                                     table_name=table.table_name, description=description)
        self.table = table

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_create_table_statement(table=self.table)


class TableDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because tables were created.
    """

    def __init__(self, database, table, description=None):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a TABLE_DROPPED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was dropped.
        :param database: The database modified.
        :type database: Database
        :param table: Table being dropped.
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(TableDroppedDifference, self).__init__(diff_type=DatabaseDifference.TABLE_DROPPED,
                                                     database=database, schema_name=table.schema_name,
                                                     table_name=table.table_name, description=description)
        self.table = table

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_drop_table_statement(table=self.table)


class PrimaryKeyAddedDifference(DatabaseDifference):
    """
    Class to handle differences because a primary key was added.
    """
    def __init__(self, database, table, primary_key, description=None):
        """
        Contains a difference due to a primary key being added to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param column: Primary key that was added.
        :type column: list of str
        :param description: Description of the modification.
        :type description: str
        """
        super(PrimaryKeyAddedDifference, self).__init__(diff_type=DatabaseDifference.PRIMARY_KEY_ADDED,
                                                    database=database, schema_name=table.schema_name,
                                                    table_name=table.table_name, description=description)
        self.table = table
        self.primary_key = primary_key

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_add_primary_key_statement(table=self.table,
                                                                         primary_key=self.primary_key)


class PrimaryKeyDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because a primary key was dropped.
    """
    def __init__(self, database, table, description=None):
        """
        Contains a difference due to a primary key being dropped to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(PrimaryKeyDroppedDifference, self).__init__(diff_type=DatabaseDifference.PRIMARY_KEY_DROPPED,
                                                          database=database, schema_name=table.schema_name,
                                                          table_name=table.table_name, description=description)
        self.table = table

    def get_alter(self):
        """
        Returns an alter statement to modify the table to drop the PK.
        :return: An alter statement to modify the table to drop the PK.
        :rtype: str
        """
        return self.command_generator.generate_drop_primary_key_statement(table=self.table)


class ShardKeyAddedDifference(DatabaseDifference):
    """
    Class to handle differences because a shard key was added or modified.
    """
    def __init__(self, database, table, number_shards, hash_key, description=None):
        """
        Contains a difference due to a shard key being added to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param number_shards: The number of shards to use.
        :type number_shards: int
        :param hash_key: Shard key that was added.
        :type hash_key: list of str
        :param description: Description of the modification.
        :type description: str
        """
        super(ShardKeyAddedDifference, self).__init__(diff_type=DatabaseDifference.HASH_KEY_ADDED,
                                                        database=database, schema_name=table.schema_name,
                                                        table_name=table.table_name, description=description)
        self.table = table
        self.number_shards = number_shards
        self.hash_key = hash_key

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_add_hash_key_statement(table=self.table,
                                                                      number_shards=self.number_shards,
                                                                      hash_key=self.hash_key)


class ShardKeyDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because a shard key was dropped.
    """
    def __init__(self, database, table, description=None):
        """
        Contains a difference due to a shard key being dropped to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(ShardKeyDroppedDifference, self).__init__(diff_type=DatabaseDifference.HASH_KEY_DROPPED,
                                                          database=database, schema_name=table.schema_name,
                                                          table_name=table.table_name, description=description)
        self.table = table

    def get_alter(self):
        """
        Returns an alter statement to modify the table to drop the PK.
        :return: An alter statement to modify the table to drop the PK.
        :rtype: str
        """
        return self.command_generator.generate_drop_hash_key_statement(table=self.table)


class ForeignKeyAddedDifference(DatabaseDifference):
    """
    Class to handle differences because a foreign key was added.
    """
    def __init__(self, database, table, foreign_key, description=None):
        """
        Contains a difference due to a foreign key being added to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param foreign_key: Foreign key that was added.
        :type foreign_key: ForeignKey
        :param description: Description of the modification.
        :type description: str
        """
        super(ForeignKeyAddedDifference, self).__init__(diff_type=DatabaseDifference.FOREIGN_KEY_ADDED,
                                                        database=database, schema_name=table.schema_name,
                                                        table_name=table.table_name, description=description)
        self.table = table
        self.foreign_key = foreign_key

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_add_foreign_key_statement(table=self.table,
                                                                         foreign_key=self.foreign_key)


class ForeignKeyDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because a foreign key was dropped.
    """
    def __init__(self, database, table, fk_name, description=None):
        """
        Contains a difference due to a foreign key being dropped to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(ForeignKeyDroppedDifference, self).__init__(diff_type=DatabaseDifference.FOREIGN_KEY_DROPPED,
                                                          database=database, schema_name=table.schema_name,
                                                          table_name=table.table_name, description=description)
        self.table = table
        self.fk_name = fk_name

    def get_alter(self):
        """
        Returns an alter statement to modify the table to drop the PK.
        :return: An alter statement to modify the table to drop the PK.
        :rtype: str
        """
        return self.command_generator.generate_drop_constraint_statement(table=self.table, constraint_name=self.fk_name)


class GenericRelationshipAddedDifference(DatabaseDifference):
    """
    Class to handle differences because a generic constraint was added.
    """
    def __init__(self, database, table, relationship, description=None):
        """
        Contains a difference due to a generic constraint being added to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param relationship: Foreign key that was added.
        :type relationship: GenericRelationship
        :param description: Description of the modification.
        :type description: str
        """
        super(GenericRelationshipAddedDifference, self).__init__(diff_type=DatabaseDifference.GENERIC_RELATIONSHIP_ADDED,
                                                        database=database, schema_name=table.schema_name,
                                                        table_name=table.table_name, description=description)
        self.table = table
        self.relationship = relationship

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_add_relationship_constraint_statement(table=self.table,
                                                                                     relationship=self.relationship)


class GenericRelationshipDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because a generic constraint was dropped.
    """
    def __init__(self, database, table, gr_name, description=None):
        """
        Contains a difference due to a generic relationship constraint being dropped to the table.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param description: Description of the modification.
        :type description: str
        """
        super(GenericRelationshipDroppedDifference, self).__init__(diff_type=DatabaseDifference.GENERIC_RELATIONSHIP_DROPPED,
                                                          database=database, schema_name=table.schema_name,
                                                          table_name=table.table_name, description=description)
        self.table = table
        self.gr_name = gr_name

    def get_alter(self):
        """
        Returns an alter statement to modify the table to drop the PK.
        :return: An alter statement to modify the table to drop the PK.
        :rtype: str
        """
        return self.command_generator.generate_drop_constraint_statement(table=self.table, constraint_name=self.gr_name)


class ColumnAddedDifference(DatabaseDifference):
    """
    Class to handle differences because a column was added.
    """

    def __init__(self, database, table, column, description=None):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a COLUMN_ADDED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was added.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param column: Column that was added.
        :type column: Column
        :param description: Description of the modification.
        :type description: str
        """
        super(ColumnAddedDifference, self).__init__(diff_type=DatabaseDifference.COLUMN_ADDED,
                                                      database=database, schema_name=table.schema_name,
                                                      table_name=table.table_name, description=description)
        self.table = table
        self.column = column

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_add_column_statement(table=self.table,
                                                                     column=self.column)


class ColumnDroppedDifference(DatabaseDifference):
    """
    Class to handle differences because a column was dropped.
    """

    def __init__(self, database, table, column, description=None):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a COLUMN_DROPPED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was dropped.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param column: Column that was dropped.
        :type column: Column
        :param description: Description of the modification.
        :type description: str
        """
        super(ColumnDroppedDifference, self).__init__(diff_type=DatabaseDifference.COLUMN_DROPPED,
                                                     database=database, schema_name=table.schema_name,
                                                     table_name=table.table_name, description=description)
        self.table = table
        self.column = column

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_drop_column_statement(table=self.table, column=self.column)


class ColumnModifiedDifference(DatabaseDifference):
    """
    Class to handle differences because a column was modified.
    """

    def __init__(self, database, table, column, description=None):
        """
        Contains a difference for the given database as compared to another.  For example, if the given database
        has a table that is not in the other database, then there will be a COLUMN_MODIFIED difference.  This implies
        that to make the given database the same, the opposite of the difference should be applied.  I.e. create the
        database is it was modified.
        :param database: The database modified.
        :type database: Database
        :param table: Table being modified.
        :param table: Table
        :param column: Column that was modified.
        :type column: Column
        :param description: Description of the modification.
        :type description: str
        """
        super(ColumnModifiedDifference, self).__init__(diff_type=DatabaseDifference.COLUMN_MODIFIED,
                                                      database=database, schema_name=table.schema_name,
                                                      table_name=table.table_name, description=description)
        self.table = table
        self.column = column

    def get_alter(self):
        """
        Returns an alter statement to modify the database to match the other database.
        :return: An alter statement to modify the database to match the other database.
        :rtype: str
        """
        return self.command_generator.generate_modify_column_statement(table=self.table, column=self.column)


class DDLCompare(object):
    """
    This class will compare two different databases and return the differences between them.
    """

    def __init__(self):
        """
        Creates a new DDLCompare instance that can calculate the differences between two databases.
        """

    @staticmethod
    def compare_databases(db1, db2):
        """
        Compares two databases and returns a tuple of the differences.  The first are the changes relative to the
        db1 and the second relative to db2.
        :param db1: The first database to compare, usually the old database.
        :type db1: Database
        :param db2: The second database to compare, usually the newer database.
        :type db2: Database
        :return: A tuple containing the database differences for each database.
        :rtype: (list of DatabaseDifference[], list of DatabaseDifference)
        """
        diff1 = []
        diff2 = []

        # Get the list of tables from each database.  Note that different schema names will be interpreted as
        # different tables.  This also assumes there is only one database and gets the first one.
        # TODO:  Add support for multiple databases.
        table_names1 = sorted(db1.get_table_names())
        table_names2 = sorted(db2.get_table_names())

        # the tables are sorted, so go through them in order.
        cnt1 = cnt2 = 0
        while cnt1 < len(table_names1) and cnt2 < len(table_names2):
            if table_names1[cnt1] < table_names2[cnt2]: # table 1 is a new table.
                tn = table_names1[cnt1]
                table = db1.get_table(table_names1[cnt1])
                diff2.append(TableCreatedDifference(database=db2, table=table))
                diff1.append(TableDroppedDifference(database=db1, table=table))
                cnt1 += 1
            elif table_names1[cnt1] > table_names2[cnt2]: # table 2 is a new table.
                table = db2.get_table(table_names2[cnt2])
                diff2.append(TableDroppedDifference(database=db2, table=table))
                diff1.append(TableCreatedDifference(database=db1, table=table))
                cnt2 += 1
            else:  # same table, so compare the tables for differences.
                logging.debug("compare tables named %s" % table_names1[cnt1])
                DDLCompare._compare_tables (db1=db1, table_1=db1.get_table(table_names1[cnt1]),
                                            db2=db2, table_2=db2.get_table(table_names2[cnt2]),
                                            diff1=diff1, diff2=diff2)
                cnt1 += 1
                cnt2 += 1

        while cnt1 < len(table_names1):  # if there are any left, they are all new.
            table = db1.get_table(table_names1[cnt1])
            diff2.append(TableCreatedDifference(database=db2, table=table))
            diff1.append(TableDroppedDifference(database=db1, table=table))
            cnt1 += 1

        while cnt2 < len(table_names2):  # if there are any left, they are all new.
            table = db2.get_table(table_names2[cnt2])
            diff2.append(TableDroppedDifference(database=db2, table=table))
            diff1.append(TableCreatedDifference(database=db1, table=table))
            cnt2 += 1

        return diff1, diff2

    @staticmethod
    def _compare_tables(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables for columns, PKs, hash, FKs, and relationships.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """

        DDLCompare._compare_primary_keys(db1=db1, table_1=table_1, db2=db2, table_2=table_2, diff1=diff1, diff2=diff2)
        DDLCompare._compare_shard_keys(db1=db1, table_1=table_1, db2=db2, table_2=table_2, diff1=diff1, diff2=diff2)
        DDLCompare._compare_foreign_keys(db1=db1, table_1=table_1, db2=db2, table_2=table_2, diff1=diff1, diff2=diff2)
        DDLCompare._compare_relationships(db1=db1, table_1=table_1, db2=db2, table_2=table_2, diff1=diff1, diff2=diff2)
        DDLCompare._compare_columns(db1=db1, table_1=table_1, db2=db2, table_2=table_2, diff1=diff1, diff2=diff2)


    @staticmethod
    def _compare_primary_keys(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables' primary keys.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """

        # Compare primary keys.  The PK can either be missing or different sets of columns.
        pk1 = table_1.primary_key
        pk2 = table_2.primary_key
        if pk1 != pk2:
            if not pk1 and pk2:  # There isn't a primary key on the first table, but is on the second.
                # add to the first table and remove from the second.
                diff1.append(PrimaryKeyAddedDifference(database=db1, table=table_1, primary_key=pk2))
                diff2.append(PrimaryKeyDroppedDifference(database=db2, table=table_2))
            elif pk1 and not pk2:  # There isn't a primary key on the second table, but is on the first.
                # add to the second table and remove from the first.
                diff2.append(PrimaryKeyAddedDifference(database=db2, table=table_2, primary_key=pk1))
                diff1.append(PrimaryKeyDroppedDifference(database=db1, table=table_1))
            else:  # both have primary keys, but they are different.
                # remove the old keys and add back the new ones.  Can't just change.
                diff1.append(PrimaryKeyDroppedDifference(database=db1, table=table_1))
                diff1.append(PrimaryKeyAddedDifference(database=db1, table=table_1, primary_key=pk2))
                diff2.append(PrimaryKeyDroppedDifference(database=db2, table=table_2))
                diff2.append(PrimaryKeyAddedDifference(database=db2, table=table_2, primary_key=pk1))

    @staticmethod
    def _compare_shard_keys(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables' hash keys.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """

        # Compare shard keys.  The SK can be missing, have a different number of shards, or different sets of columns.
        sk1 = table_1.shard_key
        sk2 = table_2.shard_key

        if sk1 != sk2:
            if not sk1 and sk2:  # There isn't a shard key on the first table, but is on the second.
                # add to the first table and remove from the second.
                diff1.append(ShardKeyAddedDifference(database=db1, table=table_1,
                                                     number_shards=sk2.number_shards, hash_key=sk2.shard_keys))
                diff2.append(ShardKeyDroppedDifference(database=db2, table=table_2))
            elif sk1 and not sk2:  # There isn't a hash key on the second table, but is on the first.
                # add to the second table and remove from the first.
                diff2.append(ShardKeyAddedDifference(database=db2, table=table_2, number_shards=sk1.number_shards,
                                                     hash_key=sk1.shard_keys))
                diff1.append(ShardKeyDroppedDifference(database=db1, table=table_1))
            else:  # both have hash keys, but they are different.
                # Shard keys can be overwritten with new hash commands.
                diff1.append(ShardKeyAddedDifference(database=db1, table=table_1,
                                                     number_shards=sk2.number_shards, hash_key=sk2.shard_keys))
                diff2.append(ShardKeyAddedDifference(database=db2, table=table_2, number_shards=sk1.number_shards,
                                                     hash_key=sk1.shard_keys))


    @staticmethod
    def _compare_foreign_keys(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables' foreign keys.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """
        foreign_key_names1 = sorted([fk_name for fk_name in table_1.foreign_keys])
        foreign_key_names2 = sorted([fk_name for fk_name in table_2.foreign_keys])

        # the foreign_keys are sorted, so go through them in order.
        cnt1 = cnt2 = 0
        while cnt1 < len(foreign_key_names1) and cnt2 < len(foreign_key_names2):
            if foreign_key_names1[cnt1] < foreign_key_names2[cnt2]: # foreign_key 1 is a new foreign_key.
                foreign_key = table_1.get_foreign_key(foreign_key_names1[cnt1])
                diff2.append(ForeignKeyAddedDifference(database=db2, table=table_2, foreign_key=foreign_key))
                diff1.append(ForeignKeyDroppedDifference(database=db1, table=table_1, fk_name=foreign_key.name))
                cnt1 += 1
            elif foreign_key_names1[cnt1] > foreign_key_names2[cnt2]: # foreign_key 2 is a new foreign_key.
                foreign_key = table_2.get_foreign_key(foreign_key_names2[cnt2])
                diff1.append(ForeignKeyAddedDifference(database=db1, table=table_1, foreign_key=foreign_key))
                diff2.append(ForeignKeyDroppedDifference(database=db2, table=table_2, fk_name=foreign_key.name))
                cnt2 += 1
            else:  # same foreign_key, so compare the foreign_keys for differences.
                foreign_key_1 = table_1.get_foreign_key(foreign_key_names1[cnt1])
                foreign_key_2 = table_2.get_foreign_key(foreign_key_names2[cnt2])
                if foreign_key_1 != foreign_key_2:
                    diff1.append(ForeignKeyDroppedDifference(database=db1, table=table_1, fk_name=foreign_key_1.name))
                    diff1.append(ForeignKeyAddedDifference(database=db1, table=table_1, foreign_key=foreign_key_2))
                    diff2.append(ForeignKeyDroppedDifference(database=db2, table=table_2, fk_name=foreign_key_2.name))
                    diff2.append(ForeignKeyAddedDifference(database=db2, table=table_2, foreign_key=foreign_key_1))
                cnt1 += 1
                cnt2 += 1

        while cnt1 < len(foreign_key_names1):  # if there are any left, they are all new.
            foreign_key = table_1.get_foreign_key(foreign_key_names1[cnt1])
            diff2.append(ForeignKeyAddedDifference(database=db2, table=table_2, foreign_key=foreign_key))
            diff1.append(ForeignKeyDroppedDifference(database=db1, table=table_1, fk_name=foreign_key.name))
            cnt1 += 1

        while cnt2 < len(foreign_key_names2):  # if there are any left, they are all new.
            foreign_key = table_2.get_foreign_key(foreign_key_names2[cnt2])
            diff1.append(ForeignKeyAddedDifference(database=db1, table=table_1, foreign_key=foreign_key))
            diff2.append(ForeignKeyDroppedDifference(database=db2, table=table_2, fk_name=foreign_key.name))
            cnt2 += 1

    @staticmethod
    def _compare_relationships(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables' relationships.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """
        relationship_names1 = sorted([gr_name for gr_name in table_1.relationships])
        relationship_names2 = sorted([gr_name for gr_name in table_2.relationships])

        # the relationships are sorted, so go through them in order.
        cnt1 = cnt2 = 0
        while cnt1 < len(relationship_names1) and cnt2 < len(relationship_names2):
            if relationship_names1[cnt1] < relationship_names2[cnt2]: # relationship 1 is a new relationship.
                relationship = table_1.get_relationship(relationship_names1[cnt1])
                diff2.append(GenericRelationshipAddedDifference(database=db2, table=table_2, relationship=relationship))
                diff1.append(GenericRelationshipDroppedDifference(database=db1, table=table_1, gr_name=relationship.name))
                cnt1 += 1
            elif relationship_names1[cnt1] > relationship_names2[cnt2]: # relationship 2 is a new relationship.
                relationship = table_2.get_relationship(relationship_names2[cnt2])
                diff1.append(GenericRelationshipAddedDifference(database=db1, table=table_1, relationship=relationship))
                diff2.append(GenericRelationshipDroppedDifference(database=db2, table=table_2, gr_name=relationship.name))
                cnt2 += 1
            else:  # same relationship, so compare the relationships for differences.
                relationship_1 = table_1.get_relationship(relationship_names1[cnt1])
                relationship_2 = table_2.get_relationship(relationship_names2[cnt2])
                if relationship_1 != relationship_2:
                    diff1.append(GenericRelationshipDroppedDifference(database=db1, table=table_1, gr_name=relationship_1.name))
                    diff1.append(GenericRelationshipAddedDifference(database=db1, table=table_1, relationship=relationship_2))
                    diff2.append(GenericRelationshipDroppedDifference(database=db2, table=table_2, gr_name=relationship_2.name))
                    diff2.append(GenericRelationshipAddedDifference(database=db2, table=table_2, relationship=relationship_1))
                cnt1 += 1
                cnt2 += 1

        while cnt1 < len(relationship_names1):  # if there are any left, they are all new.
            relationship = table_1.get_relationship(relationship_names1[cnt1])
            diff2.append(GenericRelationshipAddedDifference(database=db2, table=table_2, relationship=relationship))
            diff1.append(GenericRelationshipDroppedDifference(database=db1, table=table_1, gr_name=relationship.name))
            cnt1 += 1

        while cnt2 < len(relationship_names2):  # if there are any left, they are all new.
            relationship = table_2.get_relationship(relationship_names2[cnt2])
            diff1.append(GenericRelationshipAddedDifference(database=db1, table=table_1, relationship=relationship))
            diff2.append(GenericRelationshipDroppedDifference(database=db2, table=table_2, gr_name=relationship.name))
            cnt2 += 1

    @staticmethod
    def _compare_columns(db1, table_1, db2, table_2, diff1, diff2):
        """
        Compares two tables for columns.
        :param db1: The first database being compared.
        :type db1: Database
        :param table_1: The first table to use.
        :type table_1: Table
        :param db2: The second database being compared.
        :type db2: Database
        :param table_2: The second table to use.
        :type table_2: Table
        :param diff1: The differences to add to for the first database.
        :type diff1: list of DatabaseDifference
        :param diff2: The differences to add to for the second database.
        :type diff2: list of DatabaseDifference
        """
        # get the names of the columns sorted for comparison.
        column_names1 = sorted(table_1.get_column_names())
        column_names2 = sorted(table_2.get_column_names())

        # the columns are sorted, so go through them in order.
        cnt1 = cnt2 = 0
        while cnt1 < len(column_names1) and cnt2 < len(column_names2):
            if column_names1[cnt1] < column_names2[cnt2]: # column 1 is a new column.
                column = table_1.get_column(column_names1[cnt1])
                diff2.append(ColumnAddedDifference(database=db2, table=table_2, column=column))
                diff1.append(ColumnDroppedDifference(database=db1, table=table_1, column=column))
                cnt1 += 1
            elif column_names1[cnt1] > column_names2[cnt2]: # column 2 is a new column.
                column = table_2.get_column(column_names2[cnt2])
                diff1.append(ColumnAddedDifference(database=db1, table=table_1, column=column))
                diff2.append(ColumnDroppedDifference(database=db2, table=table_2, column=column))
                cnt2 += 1
            else:  # same column, so compare the columns for differences.
                column_1 = table_1.get_column(column_names1[cnt1])
                column_2 = table_2.get_column(column_names2[cnt2])
                if column_1.column_type != column_2.column_type:
                    diff1.append(ColumnModifiedDifference(database=db1, table=table_1, column=column_2))
                    diff2.append(ColumnModifiedDifference(database=db2, table=table_2, column=column_1))
                cnt1 += 1
                cnt2 += 1

        while cnt1 < len(column_names1):  # if there are any left, they are all new.
            column = table_1.get_column(column_names1[cnt1])
            diff2.append(ColumnAddedDifference(database=db2, table=table_2, column=column))
            diff1.append(ColumnDroppedDifference(database=db1, table=table_1, column=column))
            cnt1 += 1

        while cnt2 < len(column_names2):  # if there are any left, they are all new.
            column = table_2.get_column(column_names2[cnt2])
            diff1.append(ColumnAddedDifference(database=db1, table=table_1, column=column))
            diff2.append(ColumnDroppedDifference(database=db2, table=table_2, column=column))
            cnt2 += 1

class TQLAlterWriter(object):
    """
    Writes ALTER statements to modify a database based on database differences.
    """

    def __init__(self):
        """
        Creates a new writer.
        """
        pass

    def write_alters(self, ddl_differences, filename=None):
        """
        Main function to write the Database to TQL.
        :param ddl_differences: The differences with this database to create statements for.
        :type ddl_differences: list of DatabaseDifference
        :param filename: File to write to or STDOUT is not set.  The caller is expected to close the output stream.
        :type filename: str
        the filename or outfile will be provided.
        """
        with smart_open(filename) as outfile:
            for diff in ddl_differences:
                outfile.write(diff.get_alter())
