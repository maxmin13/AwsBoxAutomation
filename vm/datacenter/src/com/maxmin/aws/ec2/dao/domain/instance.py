"""
Created on Mar 6, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class InstanceData(BaseData, BaseTag):
    """
    Instance available in AWS.
    """

    def __init__(self):
        super().__init__()

        self.instance_id = None
        self.state = None
        self.az = None
        self.private_ip = None
        self.public_ip = None
        self.instance_profile = None
        self.subnet_id = None
        self.image_id = None
        self.vpc_id = None
        self.cloud_init_data = None
        self.security_group_ids = []

    @classmethod
    def build(cls, instance: dict) -> Self:
        """
        Builds an instance object from its dictionary.
        """
        i = InstanceData()

        i.instance_id = instance.get("InstanceId")
        i.state = instance.get("State").get("Name")
        i.az = instance.get("Placement").get("AvailabilityZone")
        i.private_ip = instance.get("PrivateIpAddress")
        i.public_ip = instance.get("PublicIpAddress")
        i.instance_profile = instance.get("IamInstanceProfile")
        i.subnet_id = instance.get("SubnetId")
        i.image_id = instance.get("ImageId")
        i.vpc_id = instance.get("VpcId")

        network_interfaces = instance.get("NetworkInterfaces")

        if network_interfaces:
            for security_group in network_interfaces[0].get("Groups"):
                i.security_group_ids.append(security_group.get("GroupId"))

        tags = instance.get("Tags")

        if tags:
            for tag in tags:
                i.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return i
