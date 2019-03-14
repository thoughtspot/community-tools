import pandas as pd
import AlteryxPythonSDK as Sdk

dbtypes={'Alteryx' : {0:'BOOL',1:'BOOL',2:'INT',3:'INT',4:'INT',5:'BIGINT',6:'DOUBLE',7:'DOUBLE',8:'DOUBLE',9:'VARCHAR(0)',
                      10:'VARCHAR(0)',11:'VARCHAR(0)',12:'VARCHAR(0)',13:'DATE',14:'TIME',15:'DATETIME',16:'VARCHAR(0)'}}

class Table(object):
    def __init__(self,record_info_in,tableName,alteryx_engine,n_tool_id,primaryKey='Sale_PK'):
        self.record_info_in = record_info_in
        self.tableName = tableName
        self.primaryKey = primaryKey
        self.alteryx_engine = alteryx_engine
        self.n_tool_id = n_tool_id
        self.columns = []
        self.columnTypes = []
        self.df = None
        self.__fetch__table()

    def __repr__(self):
        return 'Table(%s )' % (self.tableName)

    def __fetch__table(self):
        types = dbtypes['Alteryx']  # deal with datatype differences
        for field in range(self.record_info_in.num_fields):
            self.columns.append(self.db_colname(self.record_info_in[field].name))
            #self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, '{}'.format(self.db_colname(self.record_info_in[field].name)))
            self.columnTypes.append(types[self.record_info_in[field].type])
        tableDictionary = {'Column':self.columns,'Column_Type':self.columnTypes}
        self.df = pd.DataFrame(tableDictionary)
        #self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, '{} | {}'.format(str(column),str(type)))

    def db_colname(self, pandas_colname):
        #colname = '"' + pandas_colname.replace(' ', '_').strip() + '"'
        colname = '"' + pandas_colname.strip() + '"'
        return colname
