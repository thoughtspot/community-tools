import AlteryxPythonSDK as Sdk


class XMSG(object):
    """
    Alteryx Message Generator
    ...
    Attributes
    ----------
    alteryx_engine:  an instance of the Alteryx Engine
        Used to write messages to the Alteryx Console

    Methods
    -------
    info()
        A short cut to the xmsg.info channel
    error()
        A short cut to the xmsg.error channel
    """

    def __init__(self, alteryx_engine, n_tool_id):
        """
        Instantiate the logger class
        :param alteryx_engine: The instantiated alteryx engine
        :param n_tool_id: The canvas tool id
        """
        self.alteryx_engine = alteryx_engine
        self.n_tool_id = n_tool_id

    def info(self, msg_string):
        return self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, msg_string)

    def error(self, msg_string):
        return self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)

    def xmsg(self):
        return self
