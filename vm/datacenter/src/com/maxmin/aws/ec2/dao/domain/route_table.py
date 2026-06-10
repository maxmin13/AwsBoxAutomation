"""
Created on Mar 7, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from typing import Self
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class RouteTableData(BaseData, BaseTag):

    """
    Class that represents an AWS route table.
    A route table is a set of rules that determines where network traffic is directed.
    Each subnet in a AWS VPC is associated with a route table which controls the traffic flow between subnets.
    """

    def __init__(self):
        super().__init__()
        self.route_table_id = None
        self.vpc_id = None
        self.associated_subnet_ids = []

    @classmethod
    def build(cls, route_table: dict) -> Self:
        """
        Builds a Subnet object from its dictionary.
        """
        rt = RouteTableData()
        rt.route_table_id = route_table.get("RouteTableId")
        rt.vpc_id = route_table.get("VpcId")

        for association in route_table.get("Associations"):
            subnet_id = association.get("SubnetId")
            if subnet_id:
                rt.associated_subnet_ids.append(subnet_id)

        tags = route_table.get("Tags")

        if tags:
            for tag in tags:
                rt.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return rt


class RouteData(BaseData):

    """
    Class that represents a route in a route table
    """

    def __init__(self):
        super().__init__()
        self.route_table_id = None
        self.internet_gateway_id = None
        self.destination_cidr = None
        self.origin = None
        self.state = None

    @classmethod
    def build(cls, route: dict, route_table_id: str) -> Self:
        """
        Builds a Route object from its dictionary.
        """
        ro = RouteData()
        ro.route_table_id = route_table_id
        ro.internet_gateway_id = route.get("GatewayId")
        ro.destination_cidr = route.get("DestinationCidrBlock")
        ro.origin = route.get("Origin")
        ro.state = route.get("State")

        return ro
