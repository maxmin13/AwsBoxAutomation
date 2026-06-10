"""
Created on Mar 11, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData


class TagData(BaseData):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    @classmethod
    def build(cls, tag: dict) -> Self:
        """
        Builds a Tag object from its dictionary.
        """
        t = TagData()
        t.key = tag.get("Key")
        t.value = tag.get("Value")

        return t
