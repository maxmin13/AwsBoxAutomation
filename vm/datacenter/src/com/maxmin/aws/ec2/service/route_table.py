"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.domain.route_table import RouteTableData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.route_table import RouteTableDao, RouteDao
from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.service.domain.route_table import RouteTable, Route
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.subnet import SubnetService
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.service.internet_gateway import InternetGatewayService


class RouteTableService(object):
    def load_route_table(
        self,
        route_table_nm: str,
    ) -> RouteTable:
        """
        Loads the route table with a tag with key 'name' equal to route_table_nm.
        Returns a RouteTable object.
        """
        if not route_table_nm:
            raise AwsServiceException("Route table name is mandatory!")

        try:
            route_table_dao = RouteTableDao()
            route_table_datas = route_table_dao.load_all(route_table_nm)

            if len(route_table_datas) > 1:
                raise AwsServiceException("Found more than one route table!")
            elif len(route_table_datas) == 0:
                Logger.debug("Route table not found!")

                response = None
            else:
                route_table_data = route_table_datas[0]

                vpc_dao = VpcDao()
                vpc_data = vpc_dao.load(route_table_data.vpc_id)

                if not vpc_data:
                    raise AwsServiceException("VPC not found!")

                response = RouteTable()
                response.route_table_id = route_table_data.route_table_id
                response.vpc_id = vpc_data.vpc_id
                response.associated_subnet_ids = (
                    route_table_data.associated_subnet_ids
                )

                for t in route_table_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the route table!")

    def create_route_table(
        self, route_table_nm: str, vpc_nm: str, tags: list
    ) -> None:
        """
        Creates a route table for the specified VPC with a tag with key 'name' equal to route_table_nm.
        After you create a route table, you can add routes and associate the table with a subnet.
        """
        if not route_table_nm:
            raise AwsServiceException("Route table name is mandatory!")

        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        try:
            vpc_service = VpcService()
            vpc = vpc_service.load_vpc(vpc_nm)

            if not vpc:
                raise AwsServiceException("VPC not found!")

            route_table = self.load_route_table(route_table_nm)

            if route_table:
                raise AwsServiceException("Route table already created!")

            Logger.debug("Creating route table ...")

            route_table_data = RouteTableData()
            route_table_data.route_table_nm = route_table_nm
            route_table_data.vpc_id = vpc.vpc_id

            route_table_data.tags.append(TagData("name", route_table_nm))
            if tags:
                for tag in tags:
                    route_table_data.tags.append(TagData(tag.key, tag.value))

            route_table_dao = RouteTableDao()
            route_table_dao.create(route_table_data)

            Logger.debug("Route table successfully created!")
        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the route table!")

    def delete_route_table(
        self,
        route_table_nm: str,
    ) -> None:
        """
        Deletes the route table with a tag with key 'name' equal to route_table_nm.
        """
        if not route_table_nm:
            raise AwsServiceException("Route table name is mandatory!")

        try:
            route_table = self.load_route_table(route_table_nm)

            if route_table:
                route_table_data = RouteTableData
                route_table_data.route_table_id = route_table.route_table_id

                route_table_dao = RouteTableDao()
                route_table_dao.delete(route_table_data)

                Logger.debug("Route table deleted!")
            else:
                Logger.debug("Route table not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the route table!")

    def associate_route_table(
        self, route_table_nm: str, subnet_nm: str
    ) -> None:
        """
        Associates the route table to a subnet.
        """
        if not route_table_nm:
            raise AwsServiceException("Route table name is mandatory!")

        if not subnet_nm:
            raise AwsServiceException("Subnet name is mandatory!")

        try:
            subnet_service = SubnetService()
            subnet = subnet_service.load_subnet(subnet_nm)

            if not subnet:
                raise AwsServiceException("Subnet not found!")

            route_table = self.load_route_table(route_table_nm)

            if not route_table:
                raise AwsServiceException("Route table not found!")

            Logger.debug("Associating the subnet with the route table ...")

            route_table.associated_subnet_ids.append(subnet.subnet_id)

            route_table_dao = RouteTableDao()
            route_table_dao.associate(route_table)

            Logger.debug(
                "Subnet successfully associated with the route table!"
            )

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException(
                "Error associating the subnet with the route table!"
            )

    def load_route(
        self,
        route_table_nm: str,
        internet_gateway_nm: str,
        cidr: str,
    ) -> Route:
        """
        Loads a route in a route table.
        Returns a Route object.
        """
        if not route_table_nm:
            raise AwsServiceException("Route table name is mandatory!")

        if not internet_gateway_nm:
            raise AwsServiceException("Internet gateway name is mandatory!")

        try:
            route_table = self.load_route_table(route_table_nm)

            if not route_table:
                raise AwsServiceException("Route table not found!")

            internet_gateway_service = InternetGatewayService()
            internet_gateway = internet_gateway_service.load_internet_gateway(
                internet_gateway_nm
            )

            if not internet_gateway:
                raise AwsServiceException("Internet gateway not found!")

            route_dao = RouteDao()
            route_datas = route_dao.load_all(route_table.route_table_id)

            route_data = None
            for rt in route_datas:
                if (
                    rt.internet_gateway_id
                    == internet_gateway.internet_gateway_id
                    and rt.destination_cidr == cidr
                ):
                    route_data = rt
                    break

            return route_data

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the route!")
