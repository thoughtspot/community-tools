import os
import logging


class AppLogger(object):
    """
    An Application specific logger class
    ...
    Attributes
    ----------
    verbosity:  str
        A flag that represents the level of logging in the console
    logger:  an instance of the Python logging class
        The logging class used by the application.  There may be more pythonic ways to handle.

    Methods
    -------
    @logger.setter()
        Instantiates the python Logger class and populates attributes
    info()
        A short cut to the logger.info channel
    debug()
        A short cut to the logger.debug channel
    error()
        A short cut to the logger.error channel
    """

    def __init__(self, name, verbosity):
        """
        Instantiate the logger class
        :param name: The name of the logger
        :param verbosity: The level of detail to publish in the console
        """
        self.verbosity = verbosity
        self.logger = name

    @property
    def info(self):
        return self.__logger.info

    @property
    def debug(self):
        return self.__logger.debug

    @property
    def error(self):
        return self.__logger.error

    @property
    def logger(self):
        return self.__logger

    @logger.setter
    def logger(self, name):
        """
        Creates the logger with appropriate parameters
        :param name: The name of the logger
        :return: Instantiated logger object
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        #  Hardcoded log file and location

        try:
            os.environ['APPDATA']
        except KeyError:
            self.__logger = None
            return
        directory = os.environ['APPDATA']+'/ThoughtSpot/logs'
        if not os.path.exists(directory):
            os.makedirs(directory)
        log_filename = os.environ['APPDATA']+'/ThoughtSpot/logs/ts_instance.log'
        file_handler = logging.FileHandler(log_filename, 'w')
        console_handler = logging.StreamHandler()
        if self.verbosity == 1:
            file_handler.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.ERROR)
        elif self.verbosity == 0:
            file_handler.setLevel(logging.ERROR)
            console_handler.setLevel(logging.ERROR)
        else:
            file_handler.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.INFO)

        fmt = '%(asctime)s Logger: %(module)s: %(funcName)s: %(lineno)d %(message)s'
        log_format = logging.Formatter(fmt)

        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        self.__logger = logger
