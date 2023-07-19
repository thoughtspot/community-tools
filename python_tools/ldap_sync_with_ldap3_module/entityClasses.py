#! /usr/bin/env python3
# Copyright: ThoughtSpot Inc. 2016
# Author: Vishwas B Sharma (vishwas.sharma@thoughtspot.com)
"""Classes to define and use Entity types we support in TS."""


class EntityType():
    """Entity Class to define and use different types of entities.
       Used like enumerations.
    """
    USER = "User"
    GROUP = "Group"


class EntityProperty():
    """Property class to act as a place holder for Entity properties.
       Both Users and Groups have certain properties. Some of these
       can be used to uniquely identify the User/Group. Two of them
       are ID and Name. As these are the ones which are used widely
       for most operations we send back any listing operations as
       objects of this class.
    """

    def __init__(self, prop_id, prop_name, prop_type):
        """@param prop_id: ID used to view/delete User/Group entities.
           @param prop_name: Unique name property of the entity.
           @param prop_type: Type property of the entity.
        """
        self.id = prop_id
        self.name = prop_name
        self.type = prop_type

    def __repr__(self):
        return "ID: {} Name: {} Type: {}".format(self.id, self.name, self.type)
