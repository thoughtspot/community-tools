import AlteryxPythonSDK as Sdk
from ts_controller import ThoughtSpotController
from alteryx_xmsg import XMSG


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
        self.ts_controller = None
        self.xmsg = XMSG(self.alteryx_engine, self.n_tool_id)
        self.is_valid = True
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
        #  Instantiate the log file and parameters for the ThoughtSpot connection
        self.ts_controller = ThoughtSpotController(self.alteryx_engine, str_xml)
        if self.ts_controller.status == 'bad':
            self.xmsg.error(self.ts_controller.status_response)

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
        self.xmsg.error('Missing Incoming Connection')
        return False

    def pi_close(self, b_has_errors: bool):
        """
        Called after all records have been processed.
        :param b_has_errors: Set to true to not do the final processing.
        """
        self.output_anchor.assert_close()


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
        # Properties
        self.parent = parent
        self.ts_controller = self.parent.ts_controller
        self.parameters = self.parent.ts_controller.parameters
        self.logger = self.parent.ts_controller.logger
        self.xmsg = self.parent.xmsg
        self.record_info_in = None
        self.field_lists = []
        self.counter = 0
        self.completed_status = True
        self.DataField: Sdk.Field = None
        self.record_creator = None
        self.record_info_out = None

    def write_list_to_ts(self):
        """
        A non-interface, helper function that handles writing a compressed CSV in Memory and clears the list elements.
        """
        if self.ts_controller.send_rows_to_server(self.field_lists):
            for sublist in self.field_lists:
                del sublist[:]
        else:
            self.xmsg.error("Error Writing Data to ThoughtSpot.  Check Browse Tool or ThoughtSpot log at "
                            "AppData/Roaming/ThoughtSpot/Logs fo ThoughtSpot Errors")
            return False
        return True

    def write_server_messages(self):
        for tsmessage in self.ts_controller.server_messages:
            if tsmessage.find('Failed') != -1:
                self.completed_status = False
            self.record_info_out[0].set_from_string(self.record_creator, tsmessage)
            out_record = self.record_creator.finalize_record()
            self.parent.output_anchor.push_record(out_record, False)
            self.record_creator.reset()

        for tsmessage in self.ts_controller.server_errors:
            if tsmessage.find('Failed') != -1:
                self.completed_status = False
            self.record_info_out[0].set_from_string(self.record_creator, tsmessage)
            out_record = self.record_creator.finalize_record()
            self.parent.output_anchor.push_record(out_record, False)
            self.record_creator.reset()

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
            self.record_info_out.add_field(self.parent.tsmessage,
                                           self.parent.tsmessage_type,
                                           self.parent.tsmessage_size)
            self.parent.output_anchor.init(self.record_info_out)
            self.record_creator = self.record_info_out.construct_record_creator()

            for field in range(record_info_in.num_fields):
                self.field_lists.append([record_info_in[field].name])

            #  Create the ThoughtSpot Controller object
            self.xmsg.info('Connecting to:  %s' % self.parameters.thoughtspot_host_name)
            if self.ts_controller.initiate_thoughtspot():
                self.xmsg.info('Connection Established with ThoughtSpot Server')
            else:
                self.xmsg.error(self.ts_controller.status_response)
                return False

            #  Create Database if needed
            if self.parameters.ts_create_database == 'True':
                self.xmsg.info('Creating ThoughtSpot Database %s' % self.parameters.thoughtspot_database_name)
                if self.ts_controller.create_database():
                    self.xmsg.info('Created ThoughtSpot Database')
                else:
                    self.xmsg.error(self.ts_controller.status_response)
                    self.write_server_messages()
                    self.ts_controller.close()
                    return False

            #  Create Table if needed
            if self.parameters.ts_create_table == 'True':
                self.xmsg.info('Dropping and Creating table %s' % self.parameters.thoughtspot_table_name)
                if self.ts_controller.create_table(self.record_info_in):
                    self.xmsg.info('Completed Dropping and Creating Table')
                else:
                    self.xmsg.error(self.ts_controller.status_response)
                    self.write_server_messages()
                    self.ts_controller.close()
                    return False

            self.xmsg.info('Initiating Load Command on ThoughtSpot')
            if self.ts_controller.initiate_load_on_thoughtspot():
                self.xmsg.info('Completed Initiating Load Command on ThoughtSpot')
            else:
                self.xmsg.error(self.ts_controller.status_response)
                self.write_server_messages()
                self.ts_controller.close()
                return False
        self.xmsg.info('Streaming Records')
        return True

    def ii_push_record(self, in_record: object) -> bool:
        """
        Responsible for pushing records out.
        Called when an input record is being sent to the plugin.
        :param in_record: The data for the incoming record.
        :return: False if there's a downstream error, or if there's an error with the field name, otherwise True.
        """
        self.counter += 1

        if not self.parent.is_valid:
            return False

        for field in range(self.record_info_in.num_fields):
            in_value = self.record_info_in[field].get_as_string(in_record)
            self.field_lists[field].append(in_value) if in_value is not None else self.field_lists[field].append('')

        if self.counter == self.parameters.buffer_size:
            if self.write_list_to_ts():
                self.counter = 0
            else:
                return False
        return True

    def ii_update_progress(self, d_percent: float):
        """
        Called by the upstream tool to report what percentage of records have been pushed.
        :param d_percent: Value between 0.0 and 1.0.
        """

        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the downstream tool of this tool's progress.
        self.parent.output_anchor.update_progress(d_percent)

    def ii_close(self):
        """
        Called when the incoming connection has finished passing all of its records.
        """
        if self.parent.alteryx_engine.get_init_var(self.parent.n_tool_id, 'UpdateOnly') == 'False':
            if self.parent.is_valid:
                # First element for each list will always be the field names.
                if len(self.field_lists[0]) > 1:
                    self.write_list_to_ts()
            self.ts_controller.stop_load_on_thoughtspot()
            self.xmsg.info('Completed Streaming Rows')
            self.ts_controller.close_connection()
            #  Write Messages from ThoughtSpot to Downstream tool
            self.write_server_messages()
            if self.completed_status:
                self.xmsg.info('Connection with Destination Closed without errors')
            else:
                self.xmsg.error('Connection with Destination Closed with Errors.  Please check output and log')
            # Close outgoing connection
            self.parent.output_anchor.close()
