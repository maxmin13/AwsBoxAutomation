from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.ec2.dao.domain.vpc import VpcData
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class VpcDao(Ec2Dao):
    def load(self, vpc_id: str) -> VpcData:
        """
        Loads a VPC by its unique identifier.
        Returns a VpcData object.
        """
        try:
            response = self.ec2.describe_vpcs(
                VpcIds=[
                    vpc_id,
                ],
            ).get(
                "Vpcs"
            )[0]

            return VpcData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the VPC!")

    def load_all(self, vpc_nm: str) -> list:
        """
        Loads all VPCs with a tag with key 'name' equals vpc_nm.
        Returns a list of VpcData objects.
        """
        try:
            response = self.ec2.describe_vpcs(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [vpc_nm],
                    },
                ],
            ).get("Vpcs")

            vpc_datas = []

            for vpc in response:
                vpc_datas.append(VpcData.build(vpc))

            return vpc_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the VPCs!")

    def create(self, vpc_data: VpcData) -> None:
        """
        Creates a VPC and waits until it's available.
        """
        try:
            tag_specifications = [{"ResourceType": "vpc", "Tags": []}]

            for tag_data in vpc_data.tags:
                tag_specifications[0]["Tags"].append(tag_data.to_dictionary())

            identifier = (
                self.ec2.create_vpc(
                    CidrBlock=vpc_data.cidr,
                    TagSpecifications=tag_specifications,
                )
                .get("Vpc")
                .get("VpcId")
            )

            waiter = self.ec2.get_waiter("vpc_available")
            waiter.wait(VpcIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the VPC!")

    def delete(self, vpc_data: VpcData) -> None:
        """
        Deletes the VPC.
        """
        try:
            self.ec2.delete_vpc(VpcId=vpc_data.vpc_id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the VPC!")
