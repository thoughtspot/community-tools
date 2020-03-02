import xml.etree.ElementTree as Et
import xml.dom.minidom


class Parameters(object):
    """
    A class that represents the input parameters for the application
    ...
    Attributes
    ----------
    logger:  an instance of the Python logging class
        The logging class used by the application.  There may be more pythonic ways to handle.
    project:  str
        The name of the project for the data movement
    thoughtspot_host_name:  str
        The FQDN or IP address of the ThoughtSpot host
    thoughtspot_port:  int
        The ssh port used to connect to the ThoughtSpot instance.
    thoughtspot_user_name:  str
        The ThoughtSpot user name that can login and run SSH commands on the Thoughtspot server
    thoughtspot_password:  str
        The encrypted password for the user.
    thoughtspot_rsa_file_path:  str
        A path and file name to a key file for passwordless access
    thoughtspot_database_name:  SSHClient channel
        The name of the ThoughtSpot database
    thoughtspot_schema:  boolean
        The name of the ThoughtSpot schema.

    Methods
    -------
    __fetch__definition()
        Instantiates the Definition Class and loads the parameters
    create_json()
        Creates the JSON metadata string
    records_for_json()
        Format the incoming excel tables as proper JSON
    """

    def __init__(self, input_xml, alteryx_engine, logger):
        """
        Initializes the parameter definition class
        :param input_xml: The xml file that contains the parameters
        :param logger: Instantiated python logger
        """
        self.input_xml = input_xml
        self.logger = logger
        self.alteryx_engine = alteryx_engine
        self.error = None
        self.__fetch__definition()

    def __repr__(self):
        return 'Defintion File(%s)' % self.input_xml

    def __fetch__definition(self):
        """
        Pulls the parameters the rax XML provided by the html gui
        :return:
        """
        dom = xml.dom.minidom.parseString(self.input_xml)
        self.logger.debug('Loading parameters: %s' % (dom.toprettyxml()))
        setattr(self, 'thoughtspot_host_name', Et.fromstring(self.input_xml).find('DestinationServer').text
                if 'DestinationServer' in self.input_xml else None)
        if self.thoughtspot_host_name is None:
            self.error = "Please Enter a ThoughtSpot Server"
            return

        setattr(self,'thoughtspot_database_name', Et.fromstring(self.input_xml).find('TargetDatabase').text
                if 'TargetDatabase' in self.input_xml else None)
        if self.thoughtspot_database_name is None:
            self.error = "Please Enter a Database Name"
            return

        setattr(self, 'thoughtspot_schema', Et.fromstring(self.input_xml).find('TargetSchema').text
                if 'TargetSchema' in self.input_xml else 'falcon_default_schema')

        setattr(self, 'thoughtspot_user_name', Et.fromstring(self.input_xml).find('UserName').text
                if 'UserName' in self.input_xml else None)
        if self.thoughtspot_user_name is None:
            self.error = "Please Enter a ThoughtSpot User Name"
            return

        password = Et.fromstring(self.input_xml).find('Password').text if 'Password' in self.input_xml else None
        setattr(self, 'thoughtspot_rsa_file_path', Et.fromstring(self.input_xml).find('rsaFilePath').text
                if 'rsaFilePath' in self.input_xml else None)
        if self.thoughtspot_rsa_file_path is not None:
            setattr(self, 'use_key_file', True)
            setattr(self, 'thoughtspot_password', None)
        else:
            if password is None:
                self.error = "A Password or Key file Must be Entered"
                return
            else:
                #  Can be used for unencrypted passwords.  remove # on line 95 and place a # on lines 97 and 98
                #  setattr(self, 'thoughtspot_password', password)
                setattr(self, 'use_key_file', False)
                setattr(self, 'thoughtspot_password', self.alteryx_engine.decrypt_password(
                        Et.fromstring(self.input_xml).find('Password').text, 0))

        setattr(self, 'thoughtspot_table_name', Et.fromstring(self.input_xml).find('TableName').text
                if 'TableName' in self.input_xml else None)
        if self.thoughtspot_table_name is None:
            self.error = "Please Enter a ThoughtSpot Table Name"
            return

        port_test = Et.fromstring(self.input_xml).find('DestinationPort').text
        self.logger.info(port_test)
        if port_test is None:
            setattr(self, 'thoughtspot_port', 22)
        else:
            setattr(self, 'thoughtspot_port', int(port_test))

        setattr(self, 'buffer_size', int(Et.fromstring(self.input_xml).find('BufferSize').text)
                if 'BufferSize' in self.input_xml else None)
        if self.buffer_size is None:
            self.error = "Please Enter the row buffer size (Default: 1000)"
            return

        setattr(self, 'verbosity', Et.fromstring(self.input_xml).find('Verbosity').text
                if 'Verbosity' in self.input_xml else 0)
        setattr(self, 'maxingoredrows', Et.fromstring(self.input_xml).find('MaxIgnoredRows').text
                if 'MaxIgnoredRows' in self.input_xml else 0)
        setattr(self, 'truncate', Et.fromstring(self.input_xml).find('Truncate').text
                if 'Truncate' in self.input_xml else False)
        setattr(self, 'ts_create_database',  Et.fromstring(self.input_xml).find('CreateDatabase').text
                if 'CreateDatabase' in self.input_xml else False)
        setattr(self, 'booleanstring',  Et.fromstring(self.input_xml).find('BooleanString').text
                if 'BooleanString' in self.input_xml else 'T_F')
        setattr(self, 'ts_create_table', Et.fromstring(self.input_xml).find('CreateTable').text
                if 'CreateTable' in self.input_xml else False)

        primary_keys = Et.fromstring(self.input_xml).find('PrimaryKey').text \
            if 'PrimaryKey' in self.input_xml else None
        if primary_keys is not None:
            setattr(self, 'primary_keys', '","'.join(primary_keys.split(",")))
        else:
            setattr(self, 'primary_keys', None)

        hash_test = Et.fromstring(self.input_xml).find('HashValue').text
        self.logger.info(hash_test)
        if hash_test is None:
            setattr(self, 'hash_number', 0)
            setattr(self, 'partition_keys', None)
        else:
            setattr(self, 'hash_number', int(hash_test))
            partition_keys = Et.fromstring(self.input_xml).find('PartitionKey').text \
                if 'PartitionKey' in self.input_xml else None
            if partition_keys is not None:
                setattr(self, 'partition_keys', '","'.join(partition_keys.split(",")))
            else:
                setattr(self, 'partition_keys', None)
