"""
Created on Mar 9, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseTag


class Vpc(BaseTag):

    """
    Class that represents an AWS VPC.
    """

    def __init__(self):
        super().__init__()
        self.vpc_id = None
        self.state = None
        self.cidr = None
