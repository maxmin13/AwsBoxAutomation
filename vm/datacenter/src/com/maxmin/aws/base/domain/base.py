"""
Created on Mar 6, 2024

@author: vagrant
"""
from abc import ABC, abstractmethod
from typing import Self
from re import sub


class BaseData(ABC):
    """
    Class extended by the domain classes used by the daos.
    """

    def to_dictionary(self) -> dict:
        """
        Returns a dictionary from the current object, with all the property names with the first letter capital,
        ex:
            for a Tag object it would return:

                {
                    'Key': 'name',
                    'Value': 'myinternetgateway'
                }
        """
        dictionary = self.__dict__
        new_dict = dict()

        for prop, value in dictionary.items():
            prop = sub(r"(_|-)+", " ", prop).title().replace(" ", "")
            new_dict[prop] = value

        return new_dict

    @classmethod
    @abstractmethod
    def build(cls, obj: dict) -> Self:
        """
        Static method, creates an class object from a dictionary.
        """
        pass


class BaseTag(ABC):
    def __init__(self):
        self.tags = []

    def get_tag_value(self, key: str) -> str:
        """
        Returns the value of of a tag by key
        """
        value = None
        tags = self.tags
        for tag in tags:
            if tag.key == key:
                value = tag.value
                break

        return value
