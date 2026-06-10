"""
Created on Mar 7, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseTag


class RouteTable(BaseTag):

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


class Route(object):

    """
    Class that represents a route in a route table
    """

    def __init__(self):
        super().__init__()
        self.route_table_id = None
        self.internet_gateway_id = None
        self.destination_cidr = None
        self.state = None
