"""
Created on Mar 8, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseTag


class Subnet(BaseTag):

    """
    Class that represents an AWS subnet.
    """

    def __init__(self):
        super().__init__()
        self.subnet_id = None
        self.cidr = None
        self.az = None
        self.vpc_id = None
