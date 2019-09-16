import pandas as pd
from ts_logger import AppLogger
from ts_parameters import Parameters
from ts_instance import ThoughtSpotInstance
from ts_table import ThoughtSpotTable


class ThoughtSpotController(object):
    def __init__(self, alteryx_engine, input_xml):
        self.alteryx_engine = alteryx_engine
        self.input_xml = input_xml
        self.logger = None
        self.parameters = None
        self.status = "good"
        self.status_response = ""
        self.thoughtspot_connection = None
        self.table = None
        self.server_messages = None
        self.server_errors = None
        self.counter = 0
        self.file_header = True
        self.__init__controller()

    def __repr__(self):
        return True

    def __init__controller(self):
        self.logger = AppLogger('alteryx_ts_logger', 2)
        if self.logger is None:
            self.status = 'bad'
            self.status_response = 'Please add a HOMEPATH environment variable for logging'
            return
        self.logger.info('Loading Alteryx Parameter XML')
        self.parameters = Parameters(self.input_xml, self.alteryx_engine, self.logger)
        if self.parameters.error is not None:
            self.status = 'bad'
            self.status_response = self.parameters.error
            self.logger.info(self.parameters.error)
        self.logger.info('Completed Loading Alteryx Parameter XML')
        return

    def initiate_thoughtspot(self):
        """
        Instantiates the ThoughtSpot Database class
        :return:  Status of the connection
        """
        self.logger.info('Connecting to:  %s' % self.parameters.thoughtspot_host_name)
        thoughtspot_connection = ThoughtSpotInstance(self.parameters.thoughtspot_host_name,
                                                     self.parameters.thoughtspot_user_name,
                                                     self.parameters.use_key_file,
                                                     self.parameters.thoughtspot_password,
                                                     self.parameters.thoughtspot_rsa_file_path,
                                                     self.parameters.thoughtspot_port,
                                                     self.logger)
        self.thoughtspot_connection = thoughtspot_connection
        if thoughtspot_connection.status == 'bad':
            self.status = 'bad'
            self.status_response = 'ThoughtSpot instance could not connect'
            self.logger.error(self.status_response)
            return False
        self.logger.info('ThoughtSpot Connection Status: %s' % thoughtspot_connection.status)
        return True

    def create_database(self):
        self.logger.info('Creating Database')
        self.thoughtspot_connection.create_database(self.parameters.thoughtspot_database_name)
        if self.thoughtspot_connection.status == 'bad':
            self.status = 'bad'
            self.status_response = self.thoughtspot_connection.response
            self.logger.error(self.status_response)
            self.write_messages_to_log()
            return False
        self.logger.info('Completed creating database')
        return True

    def create_table(self, record_info_in):
        """
        A non-interface, helper function that uses TQL to drop and create a table.
        """
        self.logger.info('Dropping and Creating Table')
        dbtypes = {'Alteryx': {0: 'BOOL', 1: 'BOOL', 2: 'INT', 3: 'INT', 4: 'INT', 5: 'BIGINT', 6: 'DOUBLE',
                               7: 'DOUBLE', 8: 'DOUBLE', 9: 'VARCHAR(0)', 10: 'VARCHAR(0)', 11: 'VARCHAR(0)',
                               12: 'VARCHAR(0)', 13: 'DATE', 14: 'TIME', 15: 'DATETIME', 16: 'VARCHAR(0)'}}
        types = dbtypes['Alteryx']
        columns = []
        column_types = []
        for field in range(record_info_in.num_fields):
            columns.append(record_info_in[field].name)
            column_types.append(types[record_info_in[field].type])
        column_dictionary = pd.DataFrame({'Column': columns, 'Column_Type': column_types})
        column_names = ['COLUMN_NAME', 'TYPE_NAME', 'ISKEY', 'KEEP', 'FOREIGN_KEY', 'FOREIGN_TABLE',
                        'FK_NAME']
        foreign_keys = pd.DataFrame(columns=column_names)
        self.table = ThoughtSpotTable(self.logger, self.parameters.thoughtspot_database_name,
                                      self.parameters.thoughtspot_schema, self.parameters.thoughtspot_table_name,
                                      column_dictionary, self.parameters.primary_keys, foreign_keys)
        #  self.logger.info(self.table.ddl_string)
        self.logger.info('Executing Drop and Create Table Statements')
        self.thoughtspot_connection.execute_sql(self.table.ddl_string)
        if self.thoughtspot_connection.status == 'bad':
            self.status = 'bad'
            self.logger.info('Error Creating table: %s' % self.table.table_name)
            self.logger.info('Connection Response: %s' % self.thoughtspot_connection.response)
            self.status_response = self.thoughtspot_connection.response
            self.write_messages_to_log()
            return False
        self.logger.info('Completed Dropping and Creating Table')
        return True

    def write_messages_to_log(self):
        self.logger.info('Writing stdout and stderr from ThoughtSpot Server to the log')
        self.server_messages = self.thoughtspot_connection.thoughtspot_messages
        self.server_errors = self.thoughtspot_connection.thoughtspot_errors
        for tsmessage in self.server_messages:
            self.logger.debug(tsmessage)
        for tsmessage in self.thoughtspot_connection.thoughtspot_errors:
            self.logger.debug(tsmessage)

    def initiate_load_on_thoughtspot(self):
        self.logger.info('Initiating Load')
        self.thoughtspot_connection.initiate_load(self.parameters.thoughtspot_database_name,
                                                  self.parameters.thoughtspot_table_name,
                                                  self.parameters.thoughtspot_schema,
                                                  self.parameters.truncate, self.parameters.booleanstring,
                                                  self.parameters.maxingoredrows, self.parameters.verbosity)
        if self.thoughtspot_connection.status == 'bad':
            self.status = 'bad'
            self.status_response = self.thoughtspot_connection.response
            self.logger.debug('ThoughtSpot message: %s', self.thoughtspot_connection.response)
            self.write_messages_to_log()
            return False
        self.logger.info('Initiate Successful')
        return True

    def send_rows_to_server(self, field_lists):
        """
        A non-interface, helper function that handles writing a compressed CSV in Memory and clears the list elements.
        """
        data_list = list(zip(*field_lists))
        if self.file_header:
            self.thoughtspot_connection.load_data(data_list[1:])
            self.file_header = False
        else:
            self.thoughtspot_connection.load_data(data_list)
        if self.thoughtspot_connection.status == 'bad':
            self.status = 'bad'
            self.status_response = self.thoughtspot_connection.response
            self.logger.info(self.status_response)
            return False
        return True

    def stop_load_on_thoughtspot(self):
        self.logger.info('Stopping load on server')
        self.thoughtspot_connection.stop_load()
        self.write_messages_to_log()

    def close_connection(self):
        self.thoughtspot_connection.close()
