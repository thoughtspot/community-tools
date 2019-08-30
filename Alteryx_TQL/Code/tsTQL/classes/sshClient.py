import paramiko
import logging
import socket
import select

class sshClient(object):
    def __init__(self,hostname, username, password, port, compress=True, verbose=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.ssh = None
        self.transport = None
        self.channel = None
        self.compress = compress
        self.bufsize = 655360
        self.verbose = verbose
        self.logger = None
        self.status = None
        self.response = None
        self.__fetch__sshClient()

    def __repr__(self):
        return 'SSH connection for Host Name: %s and User: %s' % (self.hostname, self.username)

    def __fetch__sshClient(self):
        self.logger = logging.getLogger('sshClient')
        fmt = '%(asctime)s MySSH:%(funcName)s:%(lineno)d %(message)s'
        format = logging.Formatter(fmt)
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        self.logger.addHandler(handler)
        self.set_verbosity()
        self.info = self.logger.info
        self.info('connecting %s@%s:%d' % (self.username, self.hostname, self.port))
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.hostname,
                             port=self.port,
                             username=self.username,
                             password=self.password,
                             compress=True)
            self.transport = self.ssh.get_transport()
            self.transport.window_size = 4294967294
            self.transport.use_compression(self.compress)
            self.transport.set_keepalive(60)
            responsetxt = ('succeeded: %s@%s:%d' % (self.username,
                                                    self.hostname,
                                                    self.port))
            self.info(responsetxt)
            self.response = responsetxt
            self.status = "Good"
        except socket.error as e:
            self.transport = None
            responsetxt = ('Failed to Connect: %s@%s:%d: %s' % (self.username,
                                                                self.hostname,
                                                                self.port,
                                                                str(e)))
            self.info(responsetxt)
            self.response = responsetxt
            self.status = "Bad"
        except paramiko.AuthenticationException as e:
            self.transport = None
            responsetxt = ('Failed to Authenticate: %s@%s:%d: %s' % (self.username,
                                                                     self.hostname,
                                                                     self.port,
                                                                     str(e)))
            self.info(responsetxt)
            self.response = responsetxt
            self.status = "Bad"
        return self.transport is not None

    def close(self):
        self.info('closing connection')
        if self.ssh is not None:
            self.ssh.close()
            self.transport = None

    # def run(self, cmd, input_data=None, want_exitcode=False, timeout=60000):
    #     self.info('running command: %s' % (cmd))
    #     if self.transport is None:
    #         self.info('no connection to %s@%s:%s' % (str(self.username),
    #                                                  str(self.hostname),
    #                                                  str(self.port)))
    #         return -1, 'ERROR: connection not established\n'
    #
    #     stdin, stdout, stderr = self.ssh.exec_command(cmd)
    #     self.info('executed command')
    #     channel = stdout.channel
    #     channel.settimeout(None)
    #     self._run_send_input(channel,input_data)
    #     stdin.close()
    #     channel.shutdown_write()
    #     self.info('shutdown write channel')
    #     stdout_chunks = []
    #     stdout_chunks.append(stdout.channel.recv(len(stdout.channel.in_buffer)).decode('utf-8'))
    #     self.info('recieving output from command')
    #     while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
    #         got_chunk = False
    #         readq, _, _ = select.select([stdout.channel], [], [], timeout)
    #         for c in readq:
    #             if c.recv_ready():
    #                 stdout_chunks.append(stdout.channel.recv(len(c.in_buffer)).decode('utf-8'))
    #                 got_chunk = True
    #             if c.recv_stderr_ready():
    #                 stdout_chunks.append(stderr.channel.recv_stderr(len(c.in_stderr_buffer)))
    #                 got_chunk = True
    #         if not got_chunk \
    #                 and stdout.channel.exit_status_ready() \
    #                 and not stderr.channel.recv_stderr_ready() \
    #                 and not stdout.channel.recv_ready():
    #             stdout.channel.shutdown_read()
    #             stdout.channel.close()
    #             break
    #     stdout.close()
    #     stderr.close()
    #     self.info('done recieving output')
    #     if want_exitcode:
    #         return (''.join(str(stdout_chunks)), stdout.channel.recv_exit_status())
    #     return ''.join(stdout_chunks)
    #     return status, output

    def set_verbosity(self):
        if self.verbose > 0:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.ERROR)

    def _run_send_input(self, channel, input_data):
        if input_data != None:
            lineCounter = 1
            self.info('loading data')
            if channel.send_ready() and lineCounter == 1:
                #with input_data as fp:
                for line in input_data:
                    channel.send(line)
                    lineCounter += 1
            self.info('done loading data')
