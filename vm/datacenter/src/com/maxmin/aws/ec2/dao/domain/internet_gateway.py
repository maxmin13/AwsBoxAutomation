"""
Created on Mar 7, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class InternetGatewayData(BaseData, BaseTag):

    """
    Class that represents an AWS Internet gateway.
    Internet gateways provide two-way public connectivity to applications running in AWS Regions and/or in Local Zones.
    """

    def __init__(self):
        super().__init__()
        self.internet_gateway_id = None
        self.attached_vpc_ids = []

    @classmethod
    def build(cls, internet_gateway: dict) -> Self:
        """
        Builds an Internet gateway object from its dictionary.
        """
        ig = InternetGatewayData()
        ig.internet_gateway_id = internet_gateway.get("InternetGatewayId")

        for attachment in internet_gateway.get("Attachments"):
            ig.attached_vpc_ids.append(attachment.get("VpcId"))

        tags = internet_gateway.get("Tags")

        if tags:
            for tag in tags:
                ig.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return ig
