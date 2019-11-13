class ThoughtSpotTable(object):
    """
    A class that represents a ThoughtSpot table.
    ...
    Attributes
    ----------
    logger:  an instance of the Python logging class
        The logging class used by the application.  There may be more pythonic ways to handle.  TBD
    database:  python list
        Used to consolidate all the stdout messages
    schema:  python list
        Used to consolidate all the stderr messages
    table_name: str
        Used to pass the Thoughtspot table name
    columns:  python dictionary
        A python dictionary of the column names and types for the table
    primary_keys:  str
        A comma delimited string of primary keys for the table
    foreign_keys:  python Series
        A series of foreign keys and the appropriate metadata for the alter table commands
        application

    Methods
    -------
    __init__table()
        Instantiates the creation of the ThoughtSpot specific table metadata

    get_schema(name, column_df)
        Creates the DDL for the create table statement that is specific to ThoughtSpot

    add_constraints()
        Creates the DDL for the alter table statements that are specific to ThoughtSpot
    """
    def __init__(self, logger, database, schema, table_name, columns, primary_keys, foreign_keys, partition_keys,
                 hash_number):
        """
        :param logger:
            An instance of the python Logger class
        :param database:
            A string that represents the name of the ThoughtSpot database
        :param schema:
            A string that represents the schema used for the ThoughtSpot database
        :param table_name:
            A string that represents the table to be created
        :param columns:
            A python dictionary with the Column Name and ThoughtSpot column type for the DDL
        :param primary_keys:
            A comma separated string that represents the primary keys.
        :param foreign_keys:
            A series of foreign keys and the appropriate metadata for the alter table commands
        :param partition_keys:
            A series of columns and the appropriate metadata for the partition statement
        :param hash_number:
            The number of shards for the table
        """
        self.logger = logger
        self.database = database
        self.schema = schema
        self.table_name = table_name
        self.columns = columns
        self.primary_key = primary_keys
        self.foreign_keys = foreign_keys
        self.partition_keys = partition_keys
        self.hash_number = hash_number
        self.ddl_string = ""
        self.alter_statements = ""
        self.__init__table()

    def __repr__(self):
        return self.ddl_string

    def __init__table(self):
        """
        controller method to create DDL for the drop and create statement that meets the tql specification
        :return:  Instantiated ThoughtSpot table Object
        """
        self.ddl_string = ""
        self.alter_statements = ""
        self.ddl_string += ("\nUSE \"%s\";\n" % self.database)
        if self.schema != "falcon_default_schema":
            self.ddl_string += ("CREATE SCHEMA \"%s\";\n" % self.schema)
            self.table_name = ('\"%s\".\"%s\"' % (self.schema, self.table_name))
        self.ddl_string += "\nDROP TABLE %s;\n" % self.table_name
        self.ddl_string += ("\n%s" % self.get_schema(self.table_name, self.columns))
        if self.primary_key is not None:
            self.ddl_string += ("CONSTRAINT PRIMARY KEY (\"%s\")\n" % self.primary_key)
        else:
            self.ddl_string = self.ddl_string[:-4]
        self.ddl_string = self.ddl_string + ")\n"
        self.logger.info(self.ddl_string)
        if self.hash_number > 1:
            self.ddl_string += ("PARTITION BY HASH (%d)\n " % self.hash_number)
            if self.partition_keys is not None:
                self.ddl_string += ("KEY (\"%s\")\n" % self.partition_keys)
            # else:
            #     self.ddl_string = self.ddl_string[:-4]
        self.ddl_string = self.ddl_string + ";\n"

        self.logger.info(self.ddl_string)
        self.add_constraints()

    @staticmethod
    def get_schema(name, columns_series):
        """
        Specifically creates the create table section of the DDL
        :param name: The name of the table
        :param columns_series: A series of columns and corresponding ThoughtSpot column types
        :return: Create table portion of the ddl
        """
        columns = ""
        for index, row in columns_series.iterrows():
            columns += '"{}" {},\n  '.format(row['Column'], row['Column_Type'])
        template_create = """CREATE TABLE %(name)s (  
  %(columns)s"""
        create_ddl = template_create % {'name': name, 'columns': columns}
        return create_ddl

    def add_constraints(self):
        """
        Formats the Alter Table DDL statements that meet tql specification
        :return: NA
        """
        if len(self.foreign_keys) > 0:
            self.alter_statements += ("\nUSE \"%s\";\n" % self.database)

        foreign_keys_grouped = self.foreign_keys.groupby('FK_NAME')
        for FK_NAME, foreign_keys in foreign_keys_grouped:
            table_column_str = '", "'.join(str(i) for i in foreign_keys.COLUMN_NAME)
            foreign_column_str = '", "'.join(str(i) for i in foreign_keys.FOREIGN_KEY)
            foreign_table = foreign_keys['FOREIGN_TABLE'].iloc[0]
            self.alter_statements += ("\nALTER TABLE \"%s\".\"%s\"\n" % (self.schema, self.table_name))
            self.alter_statements += ("  ADD CONSTRAINT \"%s\" FOREIGN KEY (\"%s\")\n" %
                                      (FK_NAME, table_column_str))
            self.alter_statements += ("    REFERENCES \"%s\".\"%s\" (\"%s\");\n" %
                                      (self.schema, foreign_table, foreign_column_str))
        self.logger.debug(self.alter_statements)
