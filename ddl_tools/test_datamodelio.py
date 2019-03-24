import unittest
from StringIO import StringIO
from datamodel import DatamodelConstants, Database, Table, Column, ShardKey
from datamodelio import DDLParser, TQLWriter, XLSWriter, XLSReader, TsloadWriter

# -------------------------------------------------------------------------------------------------------------------


class TestDDLParser(unittest.TestCase):
    """Tests the DDLParser class."""

    def test_create_ddlparser_with_defaults(self):
        """Test creating a parser with defaults."""
        dp = DDLParser("testdb")
        self.assertEquals(dp.database_name, "testdb")
        self.assertEquals(dp.schema_name, DatamodelConstants.DEFAULT_SCHEMA)

    def test_create_ddlparser_with_all_params(self):
        """Test creating a parser with all values provided."""
        dp = DDLParser("testdb", "testschema")
        self.assertEquals(dp.database_name, "testdb")
        self.assertEquals(dp.schema_name, "testschema")

    def test_column_types(self):
        """Tests converting various types of columns."""
        self.assertEqual("BIGINT", DDLParser._convert_type("integer"))
        self.assertEqual("INT", DDLParser._convert_type("rowversion"))
        self.assertEqual(
            "VARCHAR(0)", DDLParser._convert_type("uniqueidentifier")
        )
        self.assertEqual("INT", DDLParser._convert_type("serial"))
        self.assertEqual("BOOL", DDLParser._convert_type("bit"))
        self.assertEqual("UNKNOWN", DDLParser._convert_type("blob"))
        self.assertEqual("UNKNOWN", DDLParser._convert_type("binary"))
        self.assertEqual("BIGINT", DDLParser._convert_type("number"))
        self.assertEqual("INT", DDLParser._convert_type("number(1)"))
        self.assertEqual("INT", DDLParser._convert_type("NUMBER(1)"))
        self.assertEqual("INT", DDLParser._convert_type("NUMBER(3,0)"))
        self.assertEqual("BIGINT", DDLParser._convert_type("NUMBER(10,0)"))
        self.assertEqual("BIGINT", DDLParser._convert_type("NUMBER(*,0)"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("NUMBER(4,2)"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("decimal"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("numeric"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("float"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("double"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("money"))
        self.assertEqual("DOUBLE", DDLParser._convert_type("real"))
        self.assertEqual("DATETIME", DDLParser._convert_type("datetime"))
        self.assertEqual("TIME", DDLParser._convert_type("time"))
        self.assertEqual("DATE", DDLParser._convert_type("date"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("text"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("varchar"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("char"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("varchar(88)"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("long"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("enum"))
        self.assertEqual("VARCHAR(0)", DDLParser._convert_type("xml"))
        self.assertEqual("UNKNOWN", DDLParser._convert_type("something_new"))


# -------------------------------------------------------------------------------------------------------------------


class TestTQLWriter(unittest.TestCase):
    """Tests the TQLWriter class."""

    @staticmethod
    def get_simple_db():
        """
        Returns a simple database with one table for testing.
        :return: Database with one table.
        :rtype: Database
        """
        database = Database(database_name="database1")
        table = Table(table_name="table1")
        table.add_column(Column(column_name="col1", column_type="INT"))
        table.add_column(Column(column_name="Col2", column_type="DOUBLE"))
        table.add_column(Column(column_name="COL3", column_type="FLOAT"))
        database.add_table(table)

        return database

    def test_write_simple_db(self):
        """Tests creating a single table with no keys or shards."""
        database = TestTQLWriter.get_simple_db()

        writer = TQLWriter()
        filename = "/tmp/datamodelio.test"
        writer.write_tql(database=database, filename=filename)
        with open(filename, "r") as input_file:
            tql = input_file.readlines()
            tql = "".join(tql)

            self.assertIn('USE "database1"', tql)
            self.assertIn('DROP TABLE "falcon_default_schema"."table1"', tql)
            self.assertIn('CREATE TABLE "falcon_default_schema"."table1"', tql)
            self.assertIn('"col1" INT', tql)
            self.assertIn('"Col2" DOUBLE', tql)
            self.assertIn('"COL3" FLOAT', tql)
            self.assertNotIn("PRIMARY KEY", tql)

    def test_write_upper(self):
        """Test writing with upper flag set."""
        database = TestTQLWriter.get_simple_db()

        writer = TQLWriter(uppercase=True)
        filename = "/tmp/datamodelio.test"
        writer.write_tql(database=database, filename=filename)
        with open(filename, "r") as input_file:
            tql = input_file.readlines()
            tql = "".join(tql)

            self.assertIn('USE "DATABASE1"', tql)
            self.assertIn('DROP TABLE "falcon_default_schema"."TABLE1"', tql)
            self.assertIn('CREATE TABLE "falcon_default_schema"."TABLE1"', tql)
            self.assertIn('"COL1" INT', tql)
            self.assertIn('"COL2" DOUBLE', tql)
            self.assertIn('"COL3" FLOAT', tql)
            self.assertNotIn("PRIMARY KEY", tql)

    def test_write_lower(self):
        """Test writing with upper flag set."""
        database = TestTQLWriter.get_simple_db()

        writer = TQLWriter(lowercase=True)
        filename = "/tmp/datamodelio.test"
        writer.write_tql(database=database, filename=filename)
        with open(filename, "r") as input_file:
            tql = input_file.readlines()
            tql = "".join(tql)

            self.assertIn('USE "database1"', tql)
            self.assertIn('DROP TABLE "falcon_default_schema"."table1"', tql)
            self.assertIn('CREATE TABLE "falcon_default_schema"."table1"', tql)
            self.assertIn('"col1" INT', tql)
            self.assertIn('"col2" DOUBLE', tql)
            self.assertIn('"col3" FLOAT', tql)
            self.assertNotIn("PRIMARY KEY", tql)

    @staticmethod
    def get_complex_db():
        """
        Returns a more complex database with two tables and keys for testing.
        :return: Database with two tables and keys.
        :rtype: Database
        """
        database = Database(database_name="database2")
        table1 = Table(
            table_name="table1",
            primary_key="col1",
            shard_key=ShardKey("col1", 128),
        )
        table1.add_column(Column(column_name="col1", column_type="INT"))
        table1.add_column(Column(column_name="Col2", column_type="DOUBLE"))
        table1.add_column(Column(column_name="COL3", column_type="FLOAT"))
        database.add_table(table1)

        table2 = Table(
            table_name="table2",
            primary_key=["col4", "Col5"],
            shard_key=ShardKey(["col4", "Col5"], 96),
        )
        table2.add_column(Column(column_name="col4", column_type="VARCHAR(0)"))
        table2.add_column(Column(column_name="Col5", column_type="DATE"))
        table2.add_column(Column(column_name="COL6", column_type="BOOL"))
        database.add_table(table2)

        table2.add_foreign_key(
            from_keys="Col5", to_table="table1", to_keys="COL3"
        )
        table1.add_relationship(
            to_table="table2", conditions='("table1"."col1" == "table2."COL6")'
        )

        return database

    def test_write_complex_db(self):
        """Test writing a more complex table."""
        database = TestTQLWriter.get_complex_db()

        writer = TQLWriter(create_db=True)
        filename = "/tmp/datamodelio.test"
        writer.write_tql(database=database, filename=filename)
        with open(filename, "r") as input_file:
            tql = input_file.readlines()
            tql = "".join(tql)

            print(tql)

            self.assertIn('CONSTRAINT PRIMARY KEY ("col1")', tql)
            self.assertIn('CONSTRAINT PRIMARY KEY ("col4", "Col5")', tql)
            self.assertIn('PARTITION BY HASH(128) KEY("col1")', tql)
            self.assertIn('PARTITION BY HASH(96) KEY("col4", "Col5")', tql)

            self.assertIn(
                'ALTER TABLE "falcon_default_schema"."table2" ADD CONSTRAINT "FK_table2_to_table1" '
                + 'FOREIGN KEY ("Col5") '
                + 'REFERENCES "falcon_default_schema"."table1" ("COL3");',
                tql,
            )
            self.assertIn(
                'ALTER TABLE "falcon_default_schema"."table1" ADD RELATIONSHIP "REL_table1_to_table2" '
                'WITH "falcon_default_schema"."table2" AS ("table1"."col1" == "table2."COL6");',
                tql,
            )


# -------------------------------------------------------------------------------------------------------------------


class TestXLSWriter(unittest.TestCase):
    """Tests creating Excel worksheets."""

    def test_create_excel(self):
        """Test writing to Excel.  Only test is existance.  Checks shoudl be made for validity."""
        database = Database(database_name="xdb")

        table = Table(
            table_name="table1",
            schema_name="s1",
            primary_key="column_1",
            shard_key=ShardKey("column_1", 128),
        )
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(Column(column_name="column_2", column_type="DOUBLE"))
        table.add_column(Column(column_name="column_3", column_type="FLOAT"))
        database.add_table(table)

        table = Table(
            table_name="table2", schema_name="s1", primary_key="column_1"
        )
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(
            Column(column_name="column_2", column_type="DATETIME")
        )
        table.add_column(Column(column_name="column_3", column_type="BOOL"))
        table.add_column(Column(column_name="column_4", column_type="DOUBLE"))
        table.add_foreign_key(
            from_keys="column_1", to_table="table_1", to_keys="column_1"
        )
        table.add_relationship(
            to_table="table1", conditions="table2.column_4 = table1.column_2"
        )
        database.add_table(table)

        writer = XLSWriter()
        writer.write_database(database, "test_excel")


# TODO Add read of the file to spot check creation.

# -------------------------------------------------------------------------------------------------------------------


class TestXLSReader(unittest.TestCase):
    """Tests creating Excel worksheets."""

    def test_reading_excel(self):
        """Tests reading a worksheet."""
        databases = XLSReader().read_xls("test_excel_reader.xlsx")

        database = databases.get("xdb")
        self.assertIsNotNone(database)

        table1 = database.get_table("table1")
        self.assertIsNotNone(table1)
        self.assertEqual(table1.table_name, "table1")
        self.assertEqual(table1.schema_name, "s1")
        self.assertEqual(table1.primary_key, ["column_1"])
        self.assertEqual(table1.shard_key.shard_keys, ["column_1"])
        self.assertEqual(table1.shard_key.number_shards, 128)

        self.assertTrue(table1.has_column("column_1"))
        self.assertEqual(table1.get_column("column_1").column_type, "INT")
        self.assertTrue(table1.has_column("column_3"))
        self.assertEqual(table1.get_column("column_3").column_type, "FLOAT")

        table2 = database.get_table("table2")
        self.assertIsNotNone(table2)
        self.assertEqual(table2.table_name, "table2")
        self.assertEqual(table2.schema_name, "s1")
        self.assertEqual(table2.primary_key, ["column_1"])
        self.assertEqual(table2.shard_key.shard_keys, ["column_1", "column_2"])
        self.assertEqual(table2.shard_key.number_shards, 128)

        self.assertTrue(table2.has_column("column_1"))
        self.assertEqual(table2.get_column("column_1").column_type, "INT")
        self.assertTrue(table2.has_column("column_4"))
        self.assertEqual(table2.get_column("column_4").column_type, "DOUBLE")

        fk = table2.get_foreign_key("FK_table2_to_table1")
        self.assertIsNotNone(fk)
        self.assertEqual(fk.from_table, "table2")
        self.assertEqual(fk.from_keys, ["column_1"])
        self.assertEqual(fk.to_table, "table1")
        self.assertEqual(fk.to_keys, ["column_1"])

        rel = table2.get_relationship("REL_table2_to_table1")
        self.assertIsNotNone(rel)
        self.assertEqual(rel.from_table, "table2")
        self.assertEqual(rel.to_table, "table1")
        self.assertEqual(rel.conditions, "table2.column_4 = table1.column_2")

        table3 = database.get_table("table3")
        fk = table3.get_foreign_key("FK_table3_to_table4")
        self.assertIsNotNone(fk)
        self.assertEqual(fk.from_table, "table3")
        self.assertEqual(fk.from_keys, ["column_1", "column_2"])
        self.assertEqual(fk.to_table, "table4")
        self.assertEqual(fk.to_keys, ["column_1", "column_3"])


# -------------------------------------------------------------------------------------------------------------------


class TestTsloadWriter(unittest.TestCase):
    """ Test the tsload writer"""

    def test_with_csvfile(self):
        """test the tsload writer when the csv exists"""
        # todo Create the csv file.
        database = Database(database_name="xdb")

        table = Table(
            table_name="table1",
            schema_name="s1",
            primary_key="column_1",
            shard_key=ShardKey("column_1", 128),
        )
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(Column(column_name="column_2", column_type="DOUBLE"))
        table.add_column(Column(column_name="column_3", column_type="FLOAT"))
        table.add_column(Column(column_name="column_3", column_type="DATE"))
        database.add_table(table)

        table = Table(
            table_name="table2",
            schema_name="s1",
            primary_key="column_1",
            shard_key=ShardKey("column_1", 128),
        )
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(Column(column_name="column_2", column_type="FLOAT"))
        table.add_column(Column(column_name="column_3", column_type="DOUBLE"))
        database.add_table(table)

        table = Table(
            table_name="table3",
            schema_name="s1",
            primary_key="column_1",
            shard_key=ShardKey("column_1", 128),
        )
        table.add_column(Column(column_name="column_1", column_type="INT"))
        table.add_column(Column(column_name="column_2", column_type="FLOAT"))
        table.add_column(Column(column_name="column_3", column_type="VARCHAR"))
        database.add_table(table)

        tsload_writer = TsloadWriter()
        tsload_writer.write_tsloadcommand(database, "tsloadwriter_test")
        with open("tsloadwriter_test", "r") as infile:
            line = infile.readline()
            self.assertTrue(line.startswith("tsload "))
            self.assertTrue(line.index('--target_database "xdb"') > 0)
            self.assertTrue(line.index('--target_schema "s1"'))


# create a csv files
# todo complete for all the other flags

# -------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
