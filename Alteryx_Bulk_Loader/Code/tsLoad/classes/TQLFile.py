import AlteryxPythonSDK as Sdk

class TQLFile(object):
    def __init__(self,database,createTable,schema,alteryx_engine,n_tool_id):
        self.database = database
        self.createTable = createTable
        self.schema = schema
        self.outString = ""
        self.alteryx_engine = alteryx_engine
        self.n_tool_id = n_tool_id
        self.__fetch__tqlfile()

    def __repr__(self):
        return self.outString

    def __fetch__tqlfile(self):
        if self.database:
            self.outString = self.outString + ("USE \"%s\";\n" % self.database)
        if self.createTable==True and self.schema != "falcon_default_schema":
            self.outString = self.outString + ("CREATE SCHEMA \"%s\";\n" % self.schema)

    def add_table_def(self,table):
        self.outString = self.outString + ("\nDROP TABLE \"%s\".\"%s\";\n" % (self.schema, table.tableName))
        self.outString = self.outString + ("\n%s" % self.get_schema(table.tableName, table.df))
        if table.primaryKey is not None:
            self.outString = self.outString + ("PRIMARY KEY (\"%s\")\n" % (table.primaryKey))
        else:
            self.outString = self.outString[:-4]
        self.outString = self.outString + (");\n")

    def get_schema(self, name, df):
        columns = ""
        for index, row in df.iterrows():
            columns += '{} {},\n  '.format(row['Column'],row['Column_Type'])
            #self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, '{}'.format(row['Column_Type']))
        template_create = """CREATE TABLE %(name)s (  
  %(columns)s"""
        # print 'COLUMNS:\n', columns
        create = template_create % {'name': name, 'columns': columns}
        return create