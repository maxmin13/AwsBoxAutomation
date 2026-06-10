"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.subnet import SubnetDao
from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.service.domain.subnet import Subnet
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.subnet import SubnetData
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class SubnetService(object):
    def load_subnet(
        self,
        subnet_nm: str,
    ) -> Subnet:
        """
        Loads the subnet with a tag with key 'name' equal to subnet_nm.
        Returns a Subnet object.
        """

        if not subnet_nm:
            raise AwsServiceException("Subnet name is mandatory!")

        try:
            subnet_dao = SubnetDao()
            subnet_datas = subnet_dao.load_all(subnet_nm)

            if len(subnet_datas) > 1:
                raise AwsServiceException("Found more than one subnet!")
            elif len(subnet_datas) == 0:
                Logger.debug("Subnet not found!")

                response = None
            else:
                subnet_data = subnet_datas[0]

                vpc_dao = VpcDao()
                vpc_data = vpc_dao.load(subnet_data.vpc_id)

                if not vpc_data:
                    raise AwsServiceException("VPC not found!")

                response = Subnet()
                response.subnet_id = subnet_data.subnet_id
                response.az = subnet_data.az
                response.cidr = subnet_data.cidr
                response.vpc_id = vpc_data.vpc_id

                for t in subnet_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the subnet!")

    def create_subnet(
        self, subnet_nm: str, az: str, cidr: str, vpc_nm: str, tags: list
    ) -> None:
        """
        Creates a subnet with a tag with key 'name' equal to subnet_nm and waits until it's available.
        """

        if not subnet_nm:
            raise AwsServiceException("Subnet name is mandatory")

        if not az:
            raise AwsServiceException("Availability zone is mandatory!")

        if not cidr:
            raise AwsServiceException("CIDR is mandatory!")

        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        try:
            vpc_service = VpcService()
            vpc = vpc_service.load_vpc(vpc_nm)

            if not vpc:
                raise AwsServiceException("VPC not found!")

            subnet = self.load_subnet(subnet_nm)

            if subnet:
                raise AwsServiceException("Subnet already created!")

            Logger.debug("Creating subnet ...")

            subnet_data = SubnetData()
            subnet_data.az = az
            subnet_data.cidr = cidr
            subnet_data.vpc_id = vpc.vpc_id

            subnet_data.tags.append(TagData("name", subnet_nm))
            if tags:
                for tag in tags:
                    subnet_data.tags.append(TagData(tag.key, tag.value))

            subnet_dao = SubnetDao()
            subnet_dao.create(subnet_data)

            Logger.debug("Subnet successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the subnet!")

    def delete_subnet(
        self,
        subnet_nm: str,
    ) -> None:
        """
        Deletes the subnet with a tag with key 'name' equal to subnet_nm.
        """

        if not subnet_nm:
            raise AwsServiceException("Subnet name is mandatory!")

        try:
            subnet = self.load_subnet(subnet_nm)

            if subnet:
                subnet_data = SubnetData
                subnet_data.subnet_id = subnet.subnet_id

                subnet_dao = SubnetDao()
                subnet_dao.delete(subnet_data)

                Logger.debug("Subnet deleted!")
            else:
                Logger.debug("Subnet not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the subnet!")
