"""
Created on Mar 7, 2024

@author: vagrant
"""

from com.maxmin.aws.base.domain.base import BaseTag


class KeyPair(BaseTag):
    """
    Class that represents a SSH key pair.
    """

    def __init__(self):
        super().__init__()
        self.key_pair_id = None
        self.public_key = None
