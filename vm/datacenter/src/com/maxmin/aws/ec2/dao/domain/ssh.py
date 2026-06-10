"""
Created on Mar 7, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class KeyPairData(BaseData, BaseTag):
    """
    Class that represents a SSH key pair.
    """

    def __init__(self):
        super().__init__()
        self.key_pair_id = None
        self.key_pair_nm = None
        self.public_key = None

    @classmethod
    def build(cls, key_pair: dict) -> Self:
        """
        Builds a KeyPair object from its dictionary.
        """
        k = KeyPairData()
        k.key_pair_id = key_pair.get("KeyPairId")
        k.key_pair_nm = key_pair.get("KeyName")
        k.public_key = key_pair.get("PublicKey")

        tags = key_pair.get("Tags")

        if tags:
            for tag in tags:
                k.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return k
