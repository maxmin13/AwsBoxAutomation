"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.ec2.dao.domain.internet_gateway import InternetGatewayData
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class InternetGatewayDao(Ec2Dao):
    def load(self, internet_gateway_id: str) -> InternetGatewayData:
        """
        Loads an Internet gateway by its unique identifier.
        Returns a InternetGatewayData object.
        """
        try:
            response = self.ec2.describe_internet_gateways(
                InternetGatewayIds=[
                    internet_gateway_id,
                ],
            ).get("InternetGateways")[0]

            return InternetGatewayData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the Internet gateway!")

    def load_all(self, internet_gateway_nm: str) -> list:
        """
        Loads all Internet gateway with a tag with key 'name' equals internet_gateway_nm.
        Returns a list of InternetGatewayData objects.
        """
        try:
            response = self.ec2.describe_internet_gateways(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [internet_gateway_nm],
                    },
                ],
            ).get("InternetGateways")

            internet_gateway_datas = []

            for internet_gateway in response:
                internet_gateway_datas.append(
                    InternetGatewayData.build(internet_gateway)
                )

            return internet_gateway_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the Internet gateways!")

    def create(self, internet_gateway_data: InternetGatewayData) -> None:
        """
        Creates an Internet gateway and waits until it's available.
        """
        try:
            tag_specifications = [
                {"ResourceType": "internet-gateway", "Tags": []}
            ]

            for tag in internet_gateway_data.tags:
                tag_specifications[0]["Tags"].append(tag.to_dictionary())

            identifier = (
                self.ec2.create_internet_gateway(
                    TagSpecifications=tag_specifications,
                )
                .get("InternetGateway")
                .get("InternetGatewayId")
            )

            waiter = self.ec2.get_waiter("internet_gateway_exists")
            waiter.wait(InternetGatewayIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the Internet gateway!")

    def delete(self, internet_gateway_data: InternetGatewayData) -> None:
        """
        Deletes the Internet gateway.
        """
        try:
            self.ec2.delete_internet_gateway(
                InternetGatewayId=internet_gateway_data.internet_gateway_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the Internet gateway!")

    def attach(self, internet_gateway_data: InternetGatewayData):
        """
        Attaches the Internet gateway to VPCs,
        enabling connectivity between the Internet and the VPC.
        """
        try:
            for vpc_id in internet_gateway_data.attached_vpc_ids:
                self.ec2.attach_internet_gateway(
                    InternetGatewayId=internet_gateway_data.internet_gateway_id,
                    VpcId=vpc_id,
                )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException(
                "Error attaching the Internet gateway to the VPC!"
            )

    def detach(self, internet_gateway_data: InternetGatewayData):
        """
        Detaches the Internet gateway from VPCs, disabling connectivity to the Internet.
        """
        try:
            for vpc_id in internet_gateway_data.attached_vpc_ids:
                self.ec2.detach_internet_gateway(
                    InternetGatewayId=internet_gateway_data.internet_gateway_id,
                    VpcId=vpc_id,
                )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException(
                "Error detaching the Internet gateway from the VPC!"
            )
