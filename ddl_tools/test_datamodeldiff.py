import unittest
from datamodel import DatamodelConstants, Database, Table, Column, ShardKey
from datamodeldiff import *


class TestDDLCompare(unittest.TestCase):
    """
    Tests the DDLCompare class.  Note that changes in one are reflected in the other.
    These tests just compare the basic differences.
    """

    def test_new_and_drop_table(self):
        """Tests adding / dropping a table.  It's added in one and dropped in the other."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")
        db1.add_table(Table(table_name="table_from_1"))

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0]) is TableDroppedDifference)
        self.assertEqual(diff1[0].table_name, "table_from_1")
        self.assertTrue(type(diff2[0]) is TableCreatedDifference)
        self.assertEqual(diff2[0].table_name, "table_from_1")

    def test_add_and_drop_column(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1")
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        t2.add_column(column=Column(column_name="column1", column_type="INT"))
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is ColumnAddedDifference))
        self.assertEqual(diff1[0].table_name, "table1")
        self.assertEqual(diff1[0].column.column_name, "column1")
        self.assertEqual(diff1[0].column.column_type, "INT")

        self.assertTrue(type(diff2[0] is ColumnDroppedDifference))
        self.assertEqual(diff2[0].table_name, "table1")
        self.assertEqual(diff2[0].column.column_name, "column1")
        self.assertEqual(diff2[0].column.column_type, "INT")

    def test_change_column(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1")
        t1.add_column(column=Column(column_name="column1", column_type="INT"))
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        t2.add_column(column=Column(column_name="column1", column_type="FLOAT"))
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is ColumnModifiedDifference))
        self.assertEqual(diff1[0].table_name, "table1")
        self.assertEqual(diff1[0].column.column_name, "column1")
        self.assertEqual(diff1[0].column.column_type, "FLOAT")

        self.assertTrue(type(diff2[0] is ColumnModifiedDifference))
        self.assertEqual(diff2[0].table_name, "table1")
        self.assertEqual(diff2[0].column.column_name, "column1")
        self.assertEqual(diff2[0].column.column_type, "INT")

    def test_add_and_drop_pk(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1", primary_key="column1")
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is PrimaryKeyDroppedDifference))
        self.assertEqual(diff1[0].table_name, "table1")
        self.assertEqual(diff1[0].table.primary_key, ["column1"])

        self.assertTrue(type(diff2[0] is PrimaryKeyAddedDifference))
        self.assertEqual(diff2[0].table_name, "table1")
        self.assertEqual(diff1[0].table.primary_key, ["column1"])

    def test_add_and_drop_sk(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1", shard_key=ShardKey(shard_keys="column1", number_shards=16))
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is ShardKeyDroppedDifference))
        self.assertEqual(diff1[0].table_name, "table1")

        self.assertTrue(type(diff2[0] is ShardKeyAddedDifference))
        self.assertEqual(diff2[0].table_name, "table1")

    # foreign key added/dropped
    def test_add_and_drop_fk(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1", primary_key="column1")
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is PrimaryKeyDroppedDifference))
        self.assertEqual(diff1[0].table_name, "table1")

        self.assertTrue(type(diff2[0] is PrimaryKeyAddedDifference))
        self.assertEqual(diff2[0].table_name, "table1")

    # generic relationship added/dropped
    def test_add_and_drop_rel(self):
        """Tests adding / dropping a column from a table."""
        dc = DDLCompare()

        db1 = Database(database_name="database1")
        db2 = Database(database_name="database2")

        t1 = Table(table_name="table1")
        t1.add_relationship(relationship=GenericRelationship(from_table="table_1", to_table="table_2",
                                                             conditions="table1.col1 = table2.col2"))
        db1.add_table(t1)

        t2 = Table(table_name="table1")
        db2.add_table(t2)

        diff1, diff2 = dc.compare_databases(db1=db1, db2=db2)

        self.assertTrue(type(diff1[0] is GenericRelationshipDroppedDifference))
        self.assertEqual(diff1[0].table_name, "table1")

        self.assertTrue(type(diff2[0] is GenericRelationshipAddedDifference))
        self.assertEqual(diff2[0].table_name, "table1")
