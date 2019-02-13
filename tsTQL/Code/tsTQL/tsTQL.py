import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import select
import gzip
import sys
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
        self.userName = None
        self.password = None
        self.tqlFilePath = None
        self.tqlStatements = None
        self.is_valid = True
        self.tables = []
        self.batchSize = 100

        self.is_initialized = True
        self.single_input = None
        self.output_anchor = None
        self.information_anchor = None

        self.tsmessage = None
        self.tsmessage_type = Sdk.FieldType.string
        self.tsmessage_size = 2000

        # Custom properties
        self.sshConnection = None
        self.channel = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.writer = None
        self.record_creator = None
        self.record_info_out = None

    def write_lists_to_TS(self,lines):
        """
        A non-interface, helper function that handles writing a compressed CSV in Memory and clears the list elements.
        """
        try:
            compressed=gzip.compress(lines.encode())
            if self.channel.send_ready():
                self.channel.sendall(compressed)
            return True
        except:
            self.xmsg("Error", "Error sending Data")
            self.stdin.close()
            self.channel.shutdown_write()
            self.xmsg('Info', 'Completed Sending Commands')
            self.writeChunks(600)
            self.sshConnection.close()
            self.xmsg('Info', 'Connection with Destination Closed')
            self.output_anchor.assert_close()
            self.information_anchor.assert_close()
            sys.exit()
            return False

    def writeChunks(self,intimeout=30):
        """
        A non-interface, helper function that reads the SSH buffers and stores the chunks for reporting.
        """
        timeout = intimeout
        stdout_chunks = []
        stderr_chunks = []
        stdout_chunks.append(self.stdout.channel.recv(len(self.stdout.channel.in_buffer)).decode('utf-8'))
        while not self.channel.closed or self.channel.recv_ready() or self.channel.recv_stderr_ready():
            got_chunk = False
            readq, _, _ = select.select([self.stdout.channel], [], [], timeout)
            for c in readq:
                if c.recv_ready():
                    stdout_chunks.append(self.stdout.channel.recv(len(c.in_buffer)).decode('utf-8'))
                    got_chunk = True
                if c.recv_stderr_ready():
                    stderr_chunks.append(self.stderr.channel.recv_stderr(len(c.in_stderr_buffer)).decode('utf-8'))
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
        columnnames = None
        prevtsrow = None
        tsmessage = ''.join((stderr_chunks))
        for tsrow in tsmessage.splitlines():
            if str(tsrow).strip() != '':
                if str(tsrow).strip()[0] == '-':
                    columnnames = prevtsrow
            self.record_info_out[0].set_from_string(self.record_creator, str(tsrow).strip())
            out_record = self.record_creator.finalize_record()
            self.information_anchor.push_record(out_record, False)
            self.record_creator.reset()
            prevtsrow = str(tsrow).strip()

        tsmessage = ''.join((stdout_chunks))
        if columnnames is not None:
            self.record_info_out[0].set_from_string(self.record_creator, columnnames)
            out_record = self.record_creator.finalize_record()
            self.output_anchor.push_record(out_record, False)
            self.record_creator.reset()
        for tsrow in tsmessage.splitlines():
            self.record_info_out[0].set_from_string(self.record_creator, str(tsrow).strip())
            out_record = self.record_creator.finalize_record()
            self.output_anchor.push_record(out_record, False)
            self.record_creator.reset()
        return True

    def pi_init(self, str_xml: str):
        """
        Handles configuration based on the GUI.
        Called when the Alteryx engine is ready to provide the tool configuration from the GUI.
        :param str_xml: The raw XML from the GUI.
        """
        #  Testing code change

        # Getting the dataName data property from the Gui.html
        self.destinationServer = Et.fromstring(str_xml).find('DestinationServer').text if 'DestinationServer' in str_xml else self.xmsg("Error", "Please Enter a Destination Server")
        self.userName = Et.fromstring(str_xml).find('UserName').text if 'UserName' in str_xml else self.xmsg("Error", "Please Enter a User Name")

        self.tqlFilePath = Et.fromstring(str_xml).find('dataSourceFilePath').text if 'dataSourceFilePath' in str_xml else None

        self.tqlStatements = Et.fromstring(str_xml).find('TQLText').text if 'TQLText' in str_xml else None
        if self.tqlStatements is None and self.tqlFilePath is None:
            self.xmsg("Error", "Please Enter a TQL File or TQL Statement")

        password = Et.fromstring(str_xml).find('Password').text if 'Password' in str_xml else None
        if password is None:
            self.xmsg('Error', "A Password Must be Entered")
        else:
            self.password = self.alteryx_engine.decrypt_password(Et.fromstring(str_xml).find('Password').text, 0)

        self.output_anchor = self.output_anchor_mgr.get_output_anchor('Output')
        self.information_anchor = self.output_anchor_mgr.get_output_anchor('Information')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        """
        The IncomingInterface objects are instantiated here, one object per incoming connection.
        Called when the Alteryx engine is attempting to add an incoming data connection.
        :param str_type: The name of the input connection anchor, defined in the Config.xml file.
        :param str_name: The name of the wire, defined by the workflow author.
        :return: The IncomingInterface object(s).
        """
        return self

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
        #self.xmsg('Error','Missing Incoming Connection')
        #return False

        if self.alteryx_engine.get_init_var(self.n_tool_id, 'UpdateOnly') == 'False':
            self.record_info_out = Sdk.RecordInfo(self.alteryx_engine)
            self.record_info_out.add_field(self.tsmessage, self.tsmessage_type,
                                           self.tsmessage_size)
            self.output_anchor.init(self.record_info_out)
            self.information_anchor.init(self.record_info_out)

            self.record_creator = self.record_info_out.construct_record_creator()

            self.sshConnection = sshClient(self.destinationServer, self.userName, self.password,
                                        22, True, True)
            if self.sshConnection is None:
                self.xmsg('Info', 'Error with SSH Connection')
                return False
            else:
                self.xmsg('Info', 'Connection with Destination Established')

            cmd = 'gzip -dc | tql --query_results_apply_top_row_count 0 --null_string ""'
            #  cmd = 'tql --query_results_apply_top_row_count 0 --pagination_size 1000000 --null_string ""'

            self.xmsg('Info', cmd)
            self.stdin, self.stdout, self.stderr = self.sshConnection.ssh.exec_command(cmd)
            self.xmsg('Info', 'Executing Command')
            self.channel = self.stdout.channel
            self.channel.settimeout(None)
            if self.tqlStatements is not None:
                lines = self.tqlStatements.splitlines()
                for line in lines:
                    self.xmsg('Info',line)
                self.write_lists_to_TS(self.tqlStatements)
            elif self.tqlFilePath is not None:
                with open(self.tqlFilePath,'r') as myFile:
                    lines = "".join(line for line in myFile)
                myFile.close()
                for line in lines.splitlines():
                    self.xmsg('Info',line)
                self.write_lists_to_TS(lines)
        return True

    def pi_close(self, b_has_errors: bool):
        """
        Called after all records have been processed.
        :param b_has_errors: Set to true to not do the final processing.
        """
        if self.alteryx_engine.get_init_var(self.n_tool_id, 'UpdateOnly') == 'False':
            self.stdin.close()
            self.channel.shutdown_write()
            self.xmsg('Info', 'Completed Sending Commands')
            self.writeChunks(600)
            self.sshConnection.close()
            self.xmsg('Info', 'Connection with Destination Closed')
            self.output_anchor.assert_close()
            self.information_anchor.assert_close()

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
        pass

    def ii_init(self, record_info_in: object) -> bool:
        """
        Handles appending the new field to the incoming data.
        Called to report changes of the incoming connection's record metadata to the Alteryx engine.
        :param record_info_in: A RecordInfo object for the incoming connection's fields.
        :return: False if there's an error with the field name, otherwise True.
        """
        pass

    def ii_push_record(self, in_record: object) -> bool:
        """
        Responsible for pushing records out.
        Called when an input record is being sent to the plugin.
        :param in_record: The data for the incoming record.
        :return: False if there's a downstream error, or if there's an error with the field name, otherwise True.
        """
        pass

    def ii_update_progress(self, d_percent: float):
        """
        Called by the upstream tool to report what percentage of records have been pushed.
        :param d_percent: Value between 0.0 and 1.0.
        """

        # Inform the Alteryx engine of the tool's progress.
        pass

    def ii_close(self):
        """
        Called when the incoming connection has finished passing all of its records.
        """
        pass