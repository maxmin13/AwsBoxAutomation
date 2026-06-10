"""
Created on Mar 7, 2024

@author: vagrant
"""

from com.maxmin.aws.base.domain.base import BaseTag


class InternetGateway(BaseTag):

    """
    Class that represents an AWS Internet gateway.
    Internet gateways provide two-way public connectivity to applications running in AWS Regions and/or in Local Zones.
    """

    def __init__(self):
        super().__init__()
        self.internet_gateway_id = None
        self.attached_vpc_ids = []
