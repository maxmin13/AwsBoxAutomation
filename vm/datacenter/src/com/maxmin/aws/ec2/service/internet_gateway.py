"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.domain.internet_gateway import InternetGatewayData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.internet_gateway import InternetGatewayDao
from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.service.domain.internet_gateway import InternetGateway
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger


class InternetGatewayService(object):
    def load_internet_gateway(
        self,
        internet_gateway_nm: str,
    ) -> InternetGateway:
        """
        Loads the Internet gateway with a tag with key 'name' equal to internet_gateway_nm.
        Returns an Internet Gateway object.
        """

        if not internet_gateway_nm:
            raise AwsServiceException("Internet gateway name is mandatory!")

        try:
            internet_gateway_dao = InternetGatewayDao()
            internet_gateway_datas = internet_gateway_dao.load_all(
                internet_gateway_nm
            )

            if len(internet_gateway_datas) > 1:
                raise AwsServiceException(
                    "Found more than one Internet gateway!"
                )
            elif len(internet_gateway_datas) == 0:
                Logger.debug("Internet gateway not found!")

                response = None
            else:
                internet_gateway_data = internet_gateway_datas[0]

                vpc_dao = VpcDao()

                for vpc_id in internet_gateway_data.attached_vpc_ids:
                    vpc_data = vpc_dao.load(vpc_id)

                    if not vpc_data:
                        raise AwsServiceException("VPC not found!")

                response = InternetGateway()
                response.internet_gateway_id = (
                    internet_gateway_data.internet_gateway_id
                )
                response.attached_vpc_ids = (
                    internet_gateway_data.attached_vpc_ids
                )

                for t in internet_gateway_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the Internet gateway!")

    def create_internet_gateway(
        self, internet_gateway_nm: str, vpc_nm: str, tags: list
    ) -> None:
        """
        Creates an Internet gateway with a tag with key 'name' equal to internet_gateway_nm and waits until it's available,
        attaches the VPC to the Internet gateway.
        """

        if not internet_gateway_nm:
            raise AwsServiceException("Internet gateway name is mandatory")

        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        try:
            vpc_service = VpcService()
            vpc = vpc_service.load_vpc(vpc_nm)

            if not vpc:
                raise AwsServiceException("VPC not found!")

            internet_gateway = self.load_internet_gateway(internet_gateway_nm)

            if internet_gateway:
                raise AwsServiceException("Internet gateway already created!")

            Logger.debug("Creating Internet gateway ...")

            internet_gateway_data = InternetGatewayData()

            internet_gateway_data.tags.append(
                TagData("name", internet_gateway_nm)
            )
            if tags:
                for tag in tags:
                    internet_gateway_data.tags.append(
                        TagData(tag.key, tag.value)
                    )

            internet_gateway_dao = InternetGatewayDao()
            internet_gateway_dao.create(internet_gateway_data)

            Logger.debug("Internet gateway successfully created!")

            internet_gateway = self.load_internet_gateway(internet_gateway_nm)
            internet_gateway_data.internet_gateway_id = (
                internet_gateway.internet_gateway_id
            )
            internet_gateway_data.attached_vpc_ids.append(vpc.vpc_id)

            internet_gateway_dao.attach(internet_gateway_data)

            Logger.debug("Internet gateway attached to the VPC!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the Internet gateway!")

    def delete_internet_gateway(
        self,
        internet_gateway_nm: str,
    ) -> None:
        """
        Detaches the Internet gateway with a tag with key 'name' equal to internet_gateway_nm and deletes it.
        """

        if not internet_gateway_nm:
            raise AwsServiceException("Internet gateway name is mandatory!")

        try:
            internet_gateway = self.load_internet_gateway(internet_gateway_nm)

            if internet_gateway:
                internet_gateway_data = InternetGatewayData()
                internet_gateway_data.internet_gateway_id = (
                    internet_gateway.internet_gateway_id
                )
                internet_gateway_data.attached_vpc_ids = (
                    internet_gateway.attached_vpc_ids
                )

                internet_gateway_dao = InternetGatewayDao()
                internet_gateway_dao.detach(internet_gateway_data)
                internet_gateway_dao.delete(internet_gateway_data)

                Logger.debug("Internet gateway deleted!")
            else:
                Logger.debug("Internet gateway not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the Internet gateway!")
