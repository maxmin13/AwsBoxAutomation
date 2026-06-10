"""
Created on Mar 8, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from typing import Self
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class SubnetData(BaseData, BaseTag):

    """
    Class that represents an AWS subnet.
    """

    def __init__(self):
        super().__init__()
        self.subnet_id = None
        self.cidr = None
        self.az = None
        self.vpc_id = None
        self.is_default = False

    @classmethod
    def build(cls, subnet: dict) -> Self:
        """
        Builds a Subnet object from its dictionary.
        """
        s = SubnetData()
        s.subnet_id = subnet.get("SubnetId")
        s.cidr = subnet.get("CidrBlock")
        s.az = subnet.get("AvailabilityZone")
        s.vpc_id = subnet.get("VpcId")
        s.is_default = subnet.get("DefaultForAz")  # boolean

        tags = subnet.get("Tags")

        if tags:
            for tag in tags:
                s.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return s
