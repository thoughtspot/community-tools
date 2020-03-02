import paramiko
import io
import select
import gzip
import socket
import csv


class ThoughtSpotInstance(object):
    """
    A class that represents a ThoughtSpot cluster.
    ...
    Attributes
    ----------
    hostname:  str
        The IP Address or FQDN of the ThoughtSpot instance (without the port number)
    username:  str
        The ssh user name with access and ability to execute ThoughtSpot TQL and tsLoad commands.
    password:  str
        The unencrypted password of associated username.
    port:  int
        The ssh port used to connect to the ThoughtSpot instance.
    ssh:  instance of the paramiko.SSHClient class
        The primary class that represents the ssh tunnel to the ThoughtSpot server
    transport:  SSHClient transport
        The class that represents transport layer between the application and the ThoughtSpot server
    channel:  SSHClient channel
        The class that represents the stdin, stdout and stderr of the ssh transport
    compress:  boolean
        A flag used by the SSH library to compress traffic between the application and the ThoughtSpot server.
    bufsize:  int
        The size of the buffer to use for the ssh transport
    status:  str
        The current status of the ThoughtSpotInstance class.  This is used to determine the success or failure of a
        method from the class by the calling method.
        TODO: rewrite to raise exception
    response:  str
        A message from the ThoughtSpotInstance class to the calling application regarding the status of the method
    stderr:  str
        A buffer for the ssh stderr messages
    stdout:  str
        A buffer for the ssh stdout messages
    stdin:  str
        A buffer for the ssh stdin
    logger:  an instance of the Python logging class
        The logging class used by the application.  There may be more pythonic ways to handle.  TBD
    thoughtspot_messages:  python list
        Used to consolidate all the stdout messages
    thoughtspot_errors:  python list
        Used to consolidate all the stderr messages

    Methods
    -------
    __fetch_thoughtspot_instance()
        Instantiates the connection to the ThoughtSpot server

    close()
        Closes the connection to the ThoughtSpot Server

    execute_sql(sql)
        Executes the TQL command using the connection and passes the SQL/DDL to the ThoughtSpot server.

    create_database(database_name)
        Creates the create table ddl and passes the parameter to execute_sql

    initiate_load(thoughtspot_database, thoughtspot_table, truncate, boolean_string, max_ignored_rows, verbosity)
        Executes the tsLoad command and opens a transport using the connection and passes the tsLoad connection
        string to the ThoughtSpot server.

    load_data(row_buffer)
        Passes a csv formatted string to the connection transport from the initiate_load method.

    stop_load()
        Closes the transport to the ThoughtSpot server and initiates the formatting of the std_out and std_err messages.

    write_chunks(intimeout=30)
        Formats the std_out and std_err messages and returns a string

    """

    def __init__(self, hostname, username, use_key_file, password, thoughtspot_rsa_file_path, port, logger, compress=True):
        """
        :param hostname:
            The IP address or FQDN without the port of the ThoughSpot primary server
        :param username:
            The ssh username/id of the user able to initiate TQL or tsLoad jobs
        :param use_key_file
            A flag to tell the application to use a PEM file or password (True or False)
        :param password:
            The ssh password of the username/id
        :param thoughtspot_rsa_file_path
            the full path to the PEM key file if needed
        :param port:
            The ssh port of the ThoughtSpot server
        :param logger:
            An instance of the python Logger class
        :param compress:
            A flag to indicate the application to use compression in its ssh communications
        """

        self.hostname = hostname
        self.username = username
        self.use_key_file = use_key_file
        self.password = password
        self.thoughtspot_rsa_file_path = thoughtspot_rsa_file_path
        self.port = port
        self.ssh = None
        self.transport = None
        self.channel = None
        self.compress = compress
        self.bufsize = 655360
        self.status = None
        self.response = None
        self.stderr = None
        self.stdout = None
        self.stdin = None
        self.logger_error = logger.error
        self.logger_info = logger.info
        self.logger_debug = logger.debug
        self.thoughtspot_messages = []
        self.thoughtspot_errors = []
        self.__fetch_thoughtspot_instance()

    def __repr__(self):
        return 'ThoughtSpot connection to Host Name: %s and User: %s' % (self.hostname, self.username)

    def __fetch_thoughtspot_instance(self):
        """
        Instantiates the ssh transport
        :return: returns a the status of the the connection
        """
        self.logger_debug('Connection Port: %d' % self.port)
        try:
            if self.use_key_file:
                key = paramiko.RSAKey.from_private_key_file(self.thoughtspot_rsa_file_path)
                self.logger_info('Using key file to login')
            else:
                self.logger_info('Using password to login')
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.use_key_file:
                self.ssh.connect(hostname=self.hostname,
                                 port=self.port,
                                 username=self.username,
                                 pkey=key,
                                 compress=True)
            else:
                self.ssh.connect(hostname=self.hostname,
                                 port=self.port,
                                 username=self.username,
                                 password=self.password,
                                 compress=True)
            self.transport = self.ssh.get_transport()
            self.transport.window_size = 4294967294
            self.transport.use_compression(self.compress)
            self.transport.set_keepalive(60)
            response_text = ('succeeded: %s@%s:%d' % (self.username,
                                                      self.hostname,
                                                      int(self.port)))
            self.logger_info(response_text)
            self.response = response_text
            self.status = "good"
        except socket.error as e:
            self.transport = None
            response_text = ('Failed to Connect: %s@%s:%d: %s' % (self.username,
                                                                  self.hostname,
                                                                  self.port,
                                                                  str(e)))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"
        except paramiko.AuthenticationException as e:
            self.transport = None
            response_text = ('Failed to Authenticate: %s@%s:%d: %s' % (self.username,
                                                                       self.hostname,
                                                                       self.port,
                                                                       str(e)))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"
        except:
            self.transport = None
            response_text = ('Unexpected Error: %s@%s:%d' % (self.username,
                                                             self.hostname,
                                                             self.port))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"

        return self.status

    def close(self):
        """
        Closes the ssh connection and sets the transport to None
        """
        if self.ssh is not None:
            self.ssh.close()
            self.transport = None

    def execute_sql(self, sql):
        """
        Creates the tql command to pass the DDL in the supplied parameter
        :param sql: Str representation of the SQL/DDL to execute
        """
        cmd = "tql"
        try:
            self.stdin, self.stdout, self.stderr = self.ssh.exec_command(cmd)
            self.channel = self.stdout.channel
            self.channel.send(sql)
            self.stdin.close()
            self.channel.shutdown_write()
            self.write_chunks()
            self.logger_info("Executed command: %s " % sql)
            return True
        except socket.error as e:
            response_text = ('Error: %s' % str(e))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"

    def create_database(self, database_name):
        """
        Issues the tql to pass the create database statement
        :param database_name: str that represents the table to generate
        :return: True or False based upon successful completion
        """
        tql_string = 'create database ' + database_name + ';'
        self.execute_sql(tql_string)

    def initiate_load(self, thoughtspot_database, thoughtspot_table, thoughtspot_schema, truncate, boolean_string,
                      max_ignored_rows, verbosity):
        """
        Issues the tsload command with parameters provided and opens the stdin channel
        :param thoughtspot_database:  Name of the ThoughtSpot database
        :param thoughtspot_table:  Name of the ThoughtSpot table
        :param truncate: Flag to determine to truncate the data before loading
        :param boolean_string:  The boolean string representation that ThoughtSpot will expect
        :param max_ignored_rows:  Number of bad rows before tsload will error
        :param verbosity: The detail of stdout messages of the tsload statement
        :return: True or False based upon successful execution
        """
        if truncate == 'True':
            empty_target = '--empty_target'
        else:
            empty_target = ''

        # ThoughtSpot Load Command
        cmd = 'gzip -dc | tsload --target_database ' + thoughtspot_database + \
              ' --target_table ' + thoughtspot_table + ' --target_schema ' + thoughtspot_schema + \
              ' --field_separator \',\' --null_value \'\' ' + \
              '--date_time_format \'%Y-%m-%d %H:%M:%S\' --skip_second_fraction ' + \
              '--date_format \'%Y-%m-%d\' ' + empty_target + ' --boolean_representation \'' + boolean_string + \
              '\' --max_ignored_rows ' + str(max_ignored_rows) + ' --v ' + str(verbosity)
        self.logger_debug(cmd)
        try:
            self.stdin, self.stdout, self.stderr = self.ssh.exec_command(cmd)
            self.channel = self.stdout.channel
            self.channel.settimeout(None)
            self.logger_info("Running Load Command")
            return True
        except socket.error as e:
            response_text = ('Could not Execute Load Command:  connection error %s' % str(e))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"
            return False

    def load_data(self, row_buffer):
        """
        Pass the row_buffer to the stdin channel opened by the initiate load method
        :param row_buffer: python list of rows
        :return: True or False based upon successful completion
        """
        try:
            in_data = io.StringIO()
            csv_writer = csv.writer(in_data, delimiter=',')
            csv_writer.writerows(row_buffer)
            compressed = gzip.compress(in_data.getvalue().encode())
            if self.channel.send_ready():
                self.channel.sendall(compressed)
            return True
        except socket.error as e:
            response_text = ('Could not Execute Load Command:  connection error %s' % str(e))
            self.logger_error(response_text)
            self.response = response_text
            self.status = "bad"
            return False

    def stop_load(self):
        """
        Closes the stdin channel and shutdowns the ability to write rows
        return: NA
        """
        self.stdin.close()
        self.channel.shutdown_write()
        self.write_chunks(600)
        self.logger_info("Completed Loading Data")

    def write_chunks(self, intimeout=30):
        """
        Populates the stderr and stdout collections with the data read from the ThoughtSpot server
        :param intimeout: Wait timeout until the channel closes
        :return: populated tsMessages list
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
                self.thoughtspot_messages.append(str(tsrow).strip())
        for tsmessage in stderr_chunks:
            for tsrow in tsmessage.splitlines():
                self.thoughtspot_errors.append(str(tsrow).strip())
