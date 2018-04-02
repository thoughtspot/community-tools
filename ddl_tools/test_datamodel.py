import unittest
from datamodel import ShardKey, ForeignKey, GenericRelationship, Column, Table, Database, DatamodelConstants, DatabaseValidator

# -------------------------------------------------------------------------------------------------------------------


class TestColumn(unittest.TestCase):
    """Tests the Column class."""

    def test_create_column(self):
        """Tests creating a column with all parameters.  Just create with a few types."""
        col1 = Column(column_name="column_1", column_type="INT")
        self.assertEqual(col1.column_name, "column_1")
        self.assertEqual(col1.column_type, "INT")

        col2 = Column(column_name="column_2", column_type="DOUBLE")
        self.assertEqual(col2.column_name, "column_2")
        self.assertEqual(col2.column_type, "DOUBLE")

        col3 = Column(column_name="column_3", column_type="DATETIME")
        self.assertEqual(col3.column_name, "column_3")
        self.assertEqual(col3.column_type, "DATETIME")

    # noinspection PyTypeChecker

    def test_create_column_without_parameters(self):
        """Tests creating columns with missing parameters."""
        with self.assertRaises(AssertionError):
            Column(column_name="column_1", column_type=None)
        with self.assertRaises(AssertionError):
            Column(column_name=None, column_type="INT")

    def test_create_column_with_bad_type(self):
        """Tries to create a column with a bad data type."""
        with self.assertRaises(ValueError):
            Column(column_name="column_1", column_type="bit")


# -------------------------------------------------------------------------------------------------------------------


class TestForeignKey(unittest.TestCase):
    """Tests the ForeignKey class."""

    def test_creating_FK_with_all_paramenters_and_single_key(self):
        """Tests creating a foreign key with a single key column and no defaults."""
        fk = ForeignKey(
            from_table="tableA",
            from_keys="colA",
            to_table="tableB",
            to_keys="colB",
            name="TestFK",
        )

        self.assertEquals(fk.from_table, "tableA")
        self.assertEquals(fk.from_keys, ["colA"])
        self.assertEquals(fk.to_table, "tableB")
        self.assertEquals(fk.to_keys, ["colB"])
        self.assertEquals(fk.name, "TestFK")

    def test_creating_FK_with_no_name_and_single_key(self):
        """Tests creating a foreign key with a single key column and no defaults."""
        fk = ForeignKey(
            from_table="tableA",
            from_keys="colA",
            to_table="tableB",
            to_keys="colB",
        )

        self.assertEquals(fk.from_table, "tableA")
        self.assertEquals(fk.from_keys, ["colA"])
        self.assertEquals(fk.to_table, "tableB")
        self.assertEquals(fk.to_keys, ["colB"])
        self.assertEquals(fk.name, "FK_tableA_to_tableB")

    def test_creating_fk_with_missing_parameters(self):

        with self.assertRaises(AssertionError):
            ForeignKey(
                from_table=None,
                from_keys="colA",
                to_table="tableB",
                to_keys="colB",
            )
        with self.assertRaises(AssertionError):
            ForeignKey(
                from_table="tableA",
                from_keys=None,
                to_table="tableB",
                to_keys="colB",
            )
        with self.assertRaises(AssertionError):
            ForeignKey(
                from_table="tableA",
                from_keys="colA",
                to_table=None,
                to_keys="colB",
            )
        with self.assertRaises(AssertionError):
            ForeignKey(
                from_table="tableA",
                from_keys="colA",
                to_table="tableB",
                to_keys=None,
            )

    def test_creating_fk_with_compound_keys(self):
        """Tests creating a foreign key that uses more than one column."""

        fk = ForeignKey(
            from_table="tableA",
            from_keys=["colA", "colB"],
            to_table="tableB",
            to_keys=["colA", "colB"],
        )
        self.assertEqual(fk.from_keys, ["colA", "colB"])
        self.assertEqual(fk.to_keys, ["colA", "colB"])

    def test_creating_fk_with_mismatched_key_columns(self):
        """Tests creating a foreign key that uses more than one column."""
        with self.assertRaises(AssertionError):
            ForeignKey(
                from_table="tableA",
                from_keys="colA",
                to_table="tableB",
                to_keys=["colA", "colB"],
            )


# -------------------------------------------------------------------------------------------------------------------


class TestGenericRelationship(unittest.TestCase):
    """
    Tests the GenericRelationship class.  Most of the methods are inherited from ForeignKey, 
    so only differences are tested.
    """

    def test_create_rel_with_name(self):
        """Tests creation with a specific name."""
        gr = GenericRelationship(
            from_table="tableA",
            to_table="tableB",
            name="REL_test",
            conditions="col1 = col2",
        )
        self.assertEqual("REL_test", gr.name)

    def test_create_rel_default_name(self):
        """Tests creation with a default name."""
        gr = GenericRelationship(
            from_table="tableA", to_table="tableB", conditions="col1 = col2"
        )
        self.assertEqual(gr.name, "REL_tableA_to_tableB")

    def test_set_conditions(self):
        """Tests setting conditions in the model."""
        the_condition = "tableA.colA > tableB.colB"
        gr = GenericRelationship(
            from_table="tableA", to_table="tableB", conditions=the_condition
        )
        self.assertEqual(gr.conditions, the_condition)


# -------------------------------------------------------------------------------------------------------------------


class TestTable(unittest.TestCase):
    """Tests the Table class"""

    def test_create_table_no_errors(self):
        """Tests creating a table with the basics and no errors."""
        table = Table(table_name="Table1")
        self.assertEqual(table.table_name, "Table1")

    # noinspection PyTypeChecker

    def test_create_table_with_errors(self):
        """Test creating a table with invalid values."""
        with self.assertRaises(AssertionError):
            Table(table_name=None)

        with self.assertRaises(AssertionError):
            Table(table_name="Table1", schema_name=None)

    def test_create_table_with_primary_keys(self):
        """Tests creating a table with primary keys."""
        table = Table(table_name="Table1", primary_key="column_1")
        self.assertEqual(table.primary_key, ["column_1"])

        table = Table(
            table_name="Table2", primary_key=["column_1", "column_2"]
        )
        self.assertEqual(table.primary_key, ["column_1", "column_2"])

    def test_create_table_with_schema(self):
        """Tests creating a table with a schema."""
        table = Table(table_name="Table")
        self.assertEqual(table.schema_name, "falcon_default_schema")

        table = Table(table_name="Table", schema_name="some_other_schema")
        self.assertEqual(table.schema_name, "some_other_schema")

    @staticmethod
    def get_test_table():
        """
        Returns a table for testing columns and such.
        :returns: A table with columns for testing.
        :rtype: Table
        """
        table = Table(table_name="Table", schema_name="test")
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(Column(column_name="column_2", column_type="DOUBLE"))
        table.add_column(
            Column(column_name="column_3", column_type="DATETIME")
        )
        table.add_column(Column(column_name="column_4", column_type="BOOL"))

        return table

    def test_add_column(self):
        """Tests adding columns."""
        table = self.get_test_table()
        # just verify columns were added.  Details of columns will be tested below.
        self.assertEqual(4, table.number_columns())

    def test_drop_column(self):
        """Tests dropping columns."""
        table = self.get_test_table()
        table.drop_column("column_3")
        self.assertEqual(3, table.number_columns())
        self.assertFalse(table.has_column("column_3"))

    def test_has_column(self):
        """Tests if the table has a given column."""
        table = self.get_test_table()
        self.assertTrue(table.has_column("column_1"))
        self.assertTrue(table.has_column("column_2"))
        self.assertTrue(table.has_column("column_3"))
        self.assertTrue(table.has_column("column_4"))
        self.assertFalse(table.has_column("column_5"))

    def test_column_iteration(self):
        """Tests iteration over columns."""
        cnt = 1
        for col in self.get_test_table():
            self.assertEqual("column_%d" % cnt, col.column_name)
            cnt += 1

    def test_set_primary_key(self):
        """Tests setting primary keys."""
        table = Table(table_name="table1", primary_key="pk1")
        self.assertEqual(["pk1"], table.primary_key)
        table.set_primary_key("pk2")
        self.assertEqual(["pk2"], table.primary_key)
        table.set_primary_key(["pk1", "pk2"])
        self.assertEqual(["pk1", "pk2"], table.primary_key)

    def test_add_foreign_key(self):
        """Tests adding foreign keys."""
        table = Table(table_name="table1", primary_key="pk1")
        table.add_foreign_key(
            ForeignKey(
                name="fk1",
                from_table="table1",
                from_keys="col1",
                to_table="table2",
                to_keys="col2",
            )
        )
        table.add_foreign_key(
            name="fk2", from_keys="col3", to_table="table3", to_keys="col4"
        )

        fk = table.foreign_keys["fk1"]
        self.assertEquals("table1", fk.from_table)
        fk = table.get_foreign_key("fk2")
        self.assertEqual("table1", fk.from_table)
        self.assertEqual(["col3"], fk.from_keys)
        self.assertEqual("table3", fk.to_table)
        self.assertEqual(["col4"], fk.to_keys)

        fk = table.get_foreign_key("fkx")
        self.assertIsNone(fk)

    def test_add_relationship(self):
        """Tests adding relationships."""
        table = Table(table_name="table1", primary_key="pk1")
        table.add_relationship(
            GenericRelationship(
                from_table="table1",
                to_table="table2",
                conditions="table1.col1 = table2.col2",
                name="rel1",
            )
        )
        table.add_relationship(
            to_table="table3",
            conditions="table1.col1 = table3.col3",
            name="rel2",
        )

        rel = table.get_relationship("rel1")
        self.assertEqual("rel1", rel.name)
        rel = table.relationships["rel2"]
        self.assertEqual("rel2", rel.name)
        self.assertEqual("table1", rel.from_table)
        self.assertEqual("table3", rel.to_table)
        self.assertEqual("table1.col1 = table3.col3", rel.conditions)

        rel = table.get_relationship("foo")
        self.assertIsNone(rel)


# -------------------------------------------------------------------------------------------------------------------


class TestDatabase(unittest.TestCase):
    """Tests the Database class."""

    @staticmethod
    def create_test_database():
        """Creates a database for testing."""
        database = Database("database1")
        database.add_table(Table(table_name="table1", schema_name="schema1"))
        database.add_table(Table(table_name="table2"))
        return database

    def test_add_and_get_tables(self):
        """Tests adding and getting tables from the database."""
        database = self.create_test_database()

        self.assertEqual(database.get_table("table1").table_name, "table1")
        self.assertEqual(database.get_table("table1").schema_name, "schema1")
        self.assertEqual(database.get_table("table2").table_name, "table2")
        self.assertEqual(
            database.get_table("table2").schema_name,
            DatamodelConstants.DEFAULT_SCHEMA,
        )

    def test_get_table_names(self):
        """Tests getting table names from the database."""
        database = self.create_test_database()
        table_names = database.get_table_names()
        self.assertIn("table1", table_names)
        self.assertIn("table2", table_names)
        self.assertNotIn("table3", table_names)

    def test_drop_table(self):
        """Tests dropping tables from the database."""
        database = self.create_test_database()
        table_names = database.get_table_names()
        self.assertIn("table1", table_names)
        self.assertIn("table2", table_names)

        database.drop_table("table1")
        table_names = database.get_table_names()
        self.assertNotIn("table1", table_names)
        self.assertIn("table2", table_names)

    def test_get_schema_names(self):
        """Tests getting table names from the database."""
        database = self.create_test_database()
        schema_names = database.get_schema_names()
        self.assertIn("schema1", schema_names)
        self.assertIn(DatamodelConstants.DEFAULT_SCHEMA, schema_names)

        database.drop_table("table1")
        schema_names = database.get_schema_names()
        self.assertNotIn("schema1", schema_names)
        self.assertIn(DatamodelConstants.DEFAULT_SCHEMA, schema_names)

    def test_table_iteration(self):
        """Test iterating over tables."""
        database = self.create_test_database()
        cnt = 1
        for t in database:
            self.assertEqual("table%d" % cnt, t.table_name)
            cnt += 1


# -------------------------------------------------------------------------------------------------------------------


class TestDatabaseValidator(unittest.TestCase):
    """Tests validation of databases."""

    def test_valid_database(self):
        """Tests a good database to make sure there are no false positives."""
        good_db = Database(database_name="good_db")
        table1 = Table(
            table_name="table1",
            primary_key=["col1", "col2"],
            shard_key=ShardKey(shard_keys="col1", number_shards=128),
        )
        table1.add_column(Column(column_name="col1", column_type="INT"))
        table1.add_column(Column(column_name="col2", column_type="INT"))
        good_db.add_table(table1)

        table2 = Table(
            table_name="table2",
            primary_key=["col3", "col4"],
            shard_key=ShardKey(shard_keys="col3", number_shards=128),
        )
        table2.add_foreign_key(
            from_keys=["col3", "col4"],
            to_table="table1",
            to_keys=["col1", "col2"],
        )
        table2.add_column(Column(column_name="col3", column_type="INT"))
        table2.add_column(Column(column_name="col4", column_type="INT"))
        good_db.add_table(table2)

        dv = DatabaseValidator(good_db)
        results = dv.validate()
        self.assertTrue(results.is_valid)
        self.assertEqual([], results.issues)

    def test_bad_database(self):
        """Test invalid databases."""
        # TODO add bad database tests.
        pass


# -------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
