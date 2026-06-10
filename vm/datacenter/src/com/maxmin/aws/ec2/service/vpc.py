"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.vpc import VpcData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.service.domain.vpc import Vpc
from com.maxmin.aws.ec2.service.domain.tag import Tag


class VpcService(object):
    def load_vpc(
        self,
        vpc_nm: str,
    ) -> Vpc:
        """
        Loads the VPC with a tag with key 'name' equal to vpc_nm.
        Returns a Vpc object.
        """
        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        try:
            vpc_dao = VpcDao()
            vpc_datas = vpc_dao.load_all(vpc_nm)

            if len(vpc_datas) > 1:
                raise AwsServiceException("Found more than one VPC!")
            elif len(vpc_datas) == 0:
                Logger.debug("VPC not found!")

                response = None
            else:
                vpc_data = vpc_datas[0]

                response = Vpc()
                response.vpc_id = vpc_data.vpc_id
                response.state = vpc_data.state
                response.cidr = vpc_data.cidr

                for t in vpc_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the VPC!")

    def create_vpc(self, vpc_nm: str, cidr: str, tags: list) -> None:
        """
        Creates a VPC with a tag with key 'name' equal to vpc_nm and waits until it's available.
        """

        if not vpc_nm:
            raise AwsServiceException("VPC name tag is mandatory!")

        if not cidr:
            raise AwsServiceException("CIDR identifier is mandatory!")

        try:
            vpc_data = self.load_vpc(vpc_nm)

            if vpc_data:
                raise AwsServiceException("VPC already created!")

            Logger.debug("Creating VPC ...")

            vpc_data = VpcData()
            vpc_data.cidr = cidr

            vpc_data.tags.append(TagData("name", vpc_nm))
            if tags:
                for tag in tags:
                    vpc_data.tags.append(TagData(tag.key, tag.value))

            vpc_dao = VpcDao()
            vpc_dao.create(vpc_data)

            Logger.debug("VPC successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the VPC!")

    def delete_vpc(
        self,
        vpc_nm: str,
    ) -> None:
        """
        Deletes a VPC with a tag with key 'name' equal to vpc_nm.
        """

        if not vpc_nm:
            raise AwsServiceException("VPC name tag is mandatory!")

        try:
            vpc = self.load_vpc(vpc_nm)

            if vpc:
                vpc_data = VpcData()
                vpc_data.vpc_id = vpc.vpc_id

                vpc_dao = VpcDao()
                vpc_dao.delete(vpc_data)

                Logger.debug("VPC deleted!")
            else:
                Logger.debug("VPC not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the VPC!")
