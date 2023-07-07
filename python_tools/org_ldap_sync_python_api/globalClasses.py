#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""File to define classes which are used globally."""


class Constants():
    """Class to define constants in. Used as enumerations."""
    # Authentication Constants
    AUTHENTICATION_SUCCESS = 1
    AUTHENTICATION_FAILURE = 2
    # Operation Status
    OPERATION_SUCCESS = 3
    OPERATION_FAILURE = 4
    # Conflict Status
    GROUP_ALREADY_EXISTS = 5
    USER_ALREADY_EXISTS = 6
    ORG_ALREADY_EXISTS = 7
    # Conflicting Assignment
    ORG_CONFLICT = 8

    # Privileges
    PRIVILEGE_ADMINSTRATION = "ADMINISTRATION"

    # Org
    ALL_ORG_ID = -1
    DEFAULT_ORG_ID = 0

    # Operation Type
    Add = "ADD"
    Replace = "REPLACE"
    Remove = "REMOVE"


class Result():
    """Class to send back the results in."""

    def __init__(self, status, data=None):
        """@param status: Status of the operation executed. (In case of an
           error the status has the specific constant denoting the type of
           error.)
           @param data: Data expected from the operation. None when nothing is
           expected. (In case of an error the data can either be the response
           object of a request which caused the error or exception object in
           case of an exception.)
        """
        self.status = status
        self.data = data
