"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.subnet import SubnetData


class SubnetDao(Ec2Dao):
    def load(self, subnet_id: str) -> SubnetData:
        """
        Loads a subnet by its unique identifier.
        Returns a SubnetData object.
        """
        try:
            response = self.ec2.describe_subnets(
                SubnetIds=[
                    subnet_id,
                ],
            ).get(
                "Subnets"
            )[0]

            return SubnetData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the subnet!")

    def load_all(self, subnet_nm: str) -> list:
        """
        Loads all subnets with a tag with key 'name' equal to subnet_nm.
        Returns a list of SubnetData objects.
        """
        try:
            response = self.ec2.describe_subnets(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [subnet_nm],
                    },
                ],
            ).get("Subnets")

            subnet_datas = []

            for subnet in response:
                subnet_datas.append(SubnetData.build(subnet))

            return subnet_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the subnet!")

    def create(self, subnet_data: SubnetData) -> None:
        """
        Creates a subnet and waits until it's available.
        """
        try:
            tag_specifications = [{"ResourceType": "subnet", "Tags": []}]

            for tag_data in subnet_data.tags:
                tag_specifications[0]["Tags"].append(tag_data.to_dictionary())

            identifier = (
                self.ec2.create_subnet(
                    TagSpecifications=tag_specifications,
                    AvailabilityZone=subnet_data.az,
                    CidrBlock=subnet_data.cidr,
                    VpcId=subnet_data.vpc_id,
                )
                .get("Subnet")
                .get("SubnetId")
            )

            waiter = self.ec2.get_waiter("subnet_available")
            waiter.wait(SubnetIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the subnet!")

    def delete(self, subnet_data: SubnetData) -> None:
        """
        Deletes the subnet.
        """
        try:
            self.ec2.delete_subnet(SubnetId=subnet_data.subnet_id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the subnet!")
