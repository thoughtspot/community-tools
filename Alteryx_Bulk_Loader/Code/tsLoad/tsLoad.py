import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import csv
import io
import select
import gzip
import sys
from classes.Table import Table
from classes.TQLFile import TQLFile
from classes.sshClient import sshClient

class AyxPlugin:
    """
    Implements the plugin interface methods, to be utilized by the Alteryx engine to communicate with a plugin.
    Prefixed with "pi", the Alteryx engine will expect the below five interface methods to be defined.
    """

    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        """
        Constructor is called whenever the Alteryx engine wants to instantiate an instance of this plugin.
        :param n_tool_id: The assigned unique identification for a tool instance.
        :param alteryx_engine: Provides an interface into the Alteryx engine.
        :param output_anchor_mgr: A helper that wraps the outgoing connections for a plugin.
        """

        # Default properties
        self.n_tool_id = n_tool_id
        self.alteryx_engine = alteryx_engine
        self.output_anchor_mgr = output_anchor_mgr

        # Custom properties
        self.destinationServer = None
        self.targetDatabase = None
        self.targetSchema = None
        self.userName = None
        self.password = None
        self.tableName = None
        self.truncate = False
        self.primaryKey = None
        self.createTable = False
        self.createDatabase = False
        self.verbosity = 0
        self.maxIgnoredRows = 5
        self.booleanString = None
        self.is_valid = True
        self.tables = []
        self.batchSize = 100

        self.is_initialized = True
        self.single_input = None
        self.output_anchor = None
        self.output_field = None

        self.tsmessage = "TSMessage"
        self.tsmessage_type = Sdk.FieldType.string
        self.tsmessage_size = 2000

    def pi_init(self, str_xml: str):
        """
        Handles configuration based on the GUI.
        Called when the Alteryx engine is ready to provide the tool configuration from the GUI.
        :param str_xml: The raw XML from the GUI.
        """

        # Getting the dataName data property from the Gui.html
        self.destinationServer = Et.fromstring(str_xml).find('DestinationServer').text if 'DestinationServer' in str_xml else self.xmsg("Error", "Please Enter a Destination Server")
        self.targetDatabase = Et.fromstring(str_xml).find('TargetDatabase').text if 'TargetDatabase' in str_xml else self.xmsg("Error", "Please Enter a Target Database")
        self.targetSchema = Et.fromstring(str_xml).find('TargetSchema').text if 'TargetSchema' in str_xml else 'falcon_default_schema'
        self.userName = Et.fromstring(str_xml).find('UserName').text if 'UserName' in str_xml else self.xmsg("Error", "Please Enter a User Name")
        password = Et.fromstring(str_xml).find('Password').text if 'Password' in str_xml else None
        if password is None:
            self.xmsg('Error', "A Password Must be Entered")
        else:
            self.password = self.alteryx_engine.decrypt_password(Et.fromstring(str_xml).find('Password').text, 0)
        self.tableName = Et.fromstring(str_xml).find('TableName').text if 'TableName' in str_xml else self.xmsg("Error", "Please Enter a Table Name")
        self.verbosity = Et.fromstring(str_xml).find('Verbosity').text if 'Verbosity' in str_xml else 0
        self.maxIgnoredRows = Et.fromstring(str_xml).find('MaxIgnoredRows').text if 'MaxIgnoredRows' in str_xml else 0
        self.truncate = Et.fromstring(str_xml).find('Truncate').text if 'Truncate' in str_xml else False
        self.createDatabase = Et.fromstring(str_xml).find('CreateDatabase').text if 'CreateDatabase' in str_xml else False
        self.booleanString = Et.fromstring(str_xml).find('BooleanString').text if 'BooleanString' in str_xml else 'T_F'
        self.createTable = Et.fromstring(str_xml).find('CreateTable').text if 'CreateTable' in str_xml else False
        self.primaryKey = Et.fromstring(str_xml).find('PrimaryKey').text if 'PrimaryKey' in str_xml else None
        #if self.createTable == True and self.primaryKey is None:
        #    self.xmsg('Error', 'A Create Table must have a selected Primary Key')
        # Getting the output anchor from Config.xml by the output connection name
        self.output_anchor = self.output_anchor_mgr.get_output_anchor('Output')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        """
        The IncomingInterface objects are instantiated here, one object per incoming connection.
        Called when the Alteryx engine is attempting to add an incoming data connection.
        :param str_type: The name of the input connection anchor, defined in the Config.xml file.
        :param str_name: The name of the wire, defined by the workflow author.
        :return: The IncomingInterface object(s).
        """
        self.single_input = IncomingInterface(self)
        return self.single_input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        """
        Called when the Alteryx engine is attempting to add an outgoing data connection.
        :param str_name: The name of the output connection anchor, defined in the Config.xml file.
        :return: True signifies that the connection is accepted.
        """
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        """
        Handles generating a new field for no incoming connections.
        Called when a tool has no incoming data connection.
        :param n_record_limit: Set it to <0 for no limit, 0 for no records, and >0 to specify the number of records.
        :return: False if there's an error with the field name, otherwise True.
        """
        self.xmsg('Error','Missing Incoming Connection')
        return False

    def pi_close(self, b_has_errors: bool):
        """
        Called after all records have been processed.
        :param b_has_errors: Set to true to not do the final processing.
        """
        self.output_anchor.assert_close()

    def xmsg(self, msg_type: str, msg_string: str):
        """
        A non-interface, non-operational placeholder for the eventual localization of predefined user-facing strings.
        :param msg_string: The user-facing string.
        :return: msg_string
        """
        if msg_type == "Info":
            self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info,msg_string)
        elif msg_type == "Error":
            self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error,msg_string)
        return True

class IncomingInterface:
    """
    This class is returned by pi_add_incoming_connection, and it implements the incoming interface methods, to be\
    utilized by the Alteryx engine to communicate with a plugin when processing an incoming connection.
    Prefixed with "ii", the Alteryx engine will expect the below four interface methods to be defined.
    """
    def __init__(self, parent: object):
        """
        Constructor for IncomingInterface.
        :param parent: AyxPlugin
        """
        # Default properties
        self.parent = parent

        # Custom properties
        self.record_info_in = None
        self.field_lists = []
        self.counter = 0
        self.table = None
        self.sshConnection = None
        self.DataField: Sdk.Field = None
        self.channel = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.inData = io.StringIO()
        self.writer = None
        self.record_creator = None
        self.tsmessage = None
        self.record_info_out = None

    def write_lists_to_TS(self):
        """
        A non-interface, helper function that handles writing a compressed CSV in Memory and clears the list elements.
        """
        try:
            inData = io.StringIO()
            writer = csv.writer(inData, delimiter=',')
            writer.writerows(zip(*self.field_lists))
            #self.parent.xmsg("Info", "Completed Streaming Rows")
            compressed=gzip.compress(inData.getvalue().encode())
            if self.channel.send_ready():
                #self.parent.xmsg("Info", "Start Writing Rows")
                self.channel.sendall(compressed)
                #self.parent.xmsg("Info", "Completed Writing Rows")
            for sublist in self.field_lists:
                del sublist[:]
            return True
        except:
            self.parent.xmsg("Error", "Error Writing Data")
            self.stdin.close()
            self.channel.shutdown_write()
            self.writeChunks(600)
            self.sshConnection.close()
            self.parent.xmsg('Info', 'Connection with Destination Closed')
            self.parent.output_anchor.close() # Close outgoing connections.elf.stdin.close()
            self.channel.shutdown_write()
            sys.exit()
            return False

    def writeChunks(self,intimeout=30):
        """
        A non-interface, helper function that reads the SSH buffers and stores the chunks for reporting.
        """
        timeout = intimeout
        stdout_chunks = []
        stdout_chunks.append(self.stdout.channel.recv(len(self.stdout.channel.in_buffer)).decode('utf-8'))
        while not self.channel.closed or self.channel.recv_ready() or self.channel.recv_stderr_ready():
            got_chunk = False
            readq, _, _ = select.select([self.stdout.channel], [], [], timeout)
            for c in readq:
                if c.recv_ready():
                    stdout_chunks.append(self.stdout.channel.recv(len(c.in_buffer)).decode('utf-8'))
                    got_chunk = True
                if c.recv_stderr_ready():
                    stdout_chunks.append(self.stderr.channel.recv_stderr(len(c.in_stderr_buffer)).decode('utf-8'))
                    got_chunk = True
            if not got_chunk \
                    and self.stdout.channel.exit_status_ready() \
                    and not self.stderr.channel.recv_stderr_ready() \
                    and not self.stdout.channel.recv_ready():
                self.stdout.channel.shutdown_read()
                self.stdout.channel.close()
                break
        self.stdout.close()
        self.stderr.close()
        for tsmessage in stdout_chunks:
            for tsrow in tsmessage.splitlines():
                self.record_info_out[0].set_from_string(self.record_creator, str(tsrow).strip())
                out_record = self.record_creator.finalize_record()
                self.parent.output_anchor.push_record(out_record, False)
                self.record_creator.reset()
        return True

    def createTable(self):
        """
        A non-interface, helper function that uses TQL to drop and create a table.
        """
        self.table = Table(self.record_info_in, self.parent.tableName, self.parent.alteryx_engine,
                           self.parent.n_tool_id,self.parent.primaryKey)
        tqlFile = TQLFile(self.parent.targetDatabase, self.parent.createTable, self.parent.targetSchema,
                          self.parent.alteryx_engine, self.parent.n_tool_id)
        tqlFile.add_table_def(self.table)
        cmd = "tql"
        self.stdin, self.stdout, self.stderr = self.sshConnection.ssh.exec_command(cmd)
        self.parent.xmsg('Info', 'Executing Create Table')
        self.channel = self.stdout.channel
        self.channel.send(str(tqlFile.outString))
        self.stdin.close()
        self.channel.shutdown_write()
        self.writeChunks()
        return True

    def createDatabase(self):
        """
        A non-interface, helper function that uses TQL to drop and create a table.
        """
        tqlString = "create database " + self.parent.targetDatabase + ";"
        cmd = "tql"
        self.stdin, self.stdout, self.stderr = self.sshConnection.ssh.exec_command(cmd)
        self.parent.xmsg('Info', 'Executing Create Database')
        self.channel = self.stdout.channel
        self.channel.send(str(tqlString))
        self.stdin.close()
        self.channel.shutdown_write()
        self.writeChunks()
        return True

    def ii_init(self, record_info_in: object) -> bool:
        """
        Handles appending the new field to the incoming data.
        Called to report changes of the incoming connection's record metadata to the Alteryx engine.
        :param record_info_in: A RecordInfo object for the incoming connection's fields.
        :return: False if there's an error with the field name, otherwise True.
        """

        if self.parent.alteryx_engine.get_init_var(self.parent.n_tool_id, 'UpdateOnly') == 'False':
            self.record_info_in = record_info_in  # For later reference.
            self.record_info_out = Sdk.RecordInfo(self.parent.alteryx_engine)
            self.record_info_out.add_field(self.parent.tsmessage,self.parent.tsmessage_type,self.parent.tsmessage_size)
            self.parent.output_anchor.init(self.record_info_out)
            self.record_creator = self.record_info_out.construct_record_creator()

            for field in range(record_info_in.num_fields):
                self.field_lists.append([record_info_in[field].name])

            self.sshConnection = sshClient(self.parent.destinationServer, self.parent.userName, self.parent.password, 22, True, True)

            if self.sshConnection is None:
                self.parent.xmsg('Info','Error with SSH Connection')
                return False
            else:
                self.parent.xmsg('Info','Connection with Destination Established')

            if self.parent.createDatabase == 'True':
                self.createDatabase()

            if self.parent.createTable == 'True':
                self.createTable()

            if self.parent.truncate == 'True':
                empty_target = '--empty_target'
            else:
                empty_target = ''

            #cmd = 'tsload --target_database ' + self.parent.targetDatabase + ' --target_table ' + self.parent.tableName + ' --field_separator \',\' --has_header_row --date_format \'%Y-%m-%d\' --empty_target --max_ignored_rows 5'
            cmd = 'gzip -dc | tsload --target_database ' + self.parent.targetDatabase + ' --target_table ' + self.parent.tableName + ' --field_separator \',\' --null_value \'\' --date_time_format \'%Y-%m-%d %H:%M:%S\' --has_header_row --skip_second_fraction --date_format \'%Y-%m-%d\' ' + empty_target + ' --boolean_representation \'' + self.parent.booleanString + '\' --max_ignored_rows ' + self.parent.maxIgnoredRows + ' --v ' + str(self.parent.verbosity)
            self.parent.xmsg('Info', cmd)
            self.stdin, self.stdout, self.stderr = self.sshConnection.ssh.exec_command(cmd)
            self.parent.xmsg('Info', 'Executing Load Command')
            self.channel = self.stdout.channel
            self.channel.settimeout(None)
        return True

    def ii_push_record(self, in_record: object) -> bool:
        """
        Responsible for pushing records out.
        Called when an input record is being sent to the plugin.
        :param in_record: The data for the incoming record.
        :return: False if there's a downstream error, or if there's an error with the field name, otherwise True.
        """
        self.counter +=1

        if not self.parent.is_valid:
            return False

        for field in range(self.record_info_in.num_fields):
            in_value = self.record_info_in[field].get_as_string(in_record)
            self.field_lists[field].append(in_value) if in_value is not None else self.field_lists[field].append('')
            #self.parent.xmsg('Info', str(self.field_lists))

        if self.counter == self.parent.batchSize:
            self.write_lists_to_TS()
            self.counter = 0

        return True

    def ii_update_progress(self, d_percent: float):
        """
        Called by the upstream tool to report what percentage of records have been pushed.
        :param d_percent: Value between 0.0 and 1.0.
        """

        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)  # Inform the Alteryx engine of the tool's progress
        self.parent.output_anchor.update_progress(d_percent)  # Inform the downstream tool of this tool's progress.

    def ii_close(self):
        """
        Called when the incoming connection has finished passing all of its records.
        """
        if self.parent.alteryx_engine.get_init_var(self.parent.n_tool_id, 'UpdateOnly') == 'False':
            if self.parent.is_valid:
                # First element for each list will always be the field names.
                if len(self.field_lists[0]) > 1:
                    self.write_lists_to_TS()
        
            self.stdin.close()
            self.channel.shutdown_write()
            self.parent.xmsg('Info', 'Completed Streaming Rows')
            self.writeChunks(600)
            self.sshConnection.close()
            self.parent.xmsg('Info', 'Connection with Destination Closed')
            self.parent.output_anchor.close() # Close outgoing connections.
