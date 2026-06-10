"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.route_table import RouteTableData, RouteData


class RouteTableDao(Ec2Dao):
    def load(self, route_table_id: str) -> RouteTableData:
        """
        Loads a route table by its unique identifier.
        Returns a RouteTableData object.
        """
        try:
            response = self.ec2.describe_route_tables(
                RouteTableIds=[
                    route_table_id,
                ],
            ).get("RouteTables")[0]

            return RouteTableData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the route table!")

    def load_all(self, route_table_nm) -> list:
        """
        Loads all route tables with a tag with key 'name' equal to route_table_nm.
        Returns a list of RouteTableData objects.
        """
        try:
            response = self.ec2.describe_route_tables(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [route_table_nm],
                    },
                ],
            ).get("RouteTables")

            route_table_datas = []

            for route_table in response:
                route_table_datas.append(RouteTableData.build(route_table))

            return route_table_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the route tables!")

    def create(self, route_table_data: RouteTableData) -> None:
        """
        Creates a route table.
        """
        try:
            tag_specifications = [{"ResourceType": "route-table", "Tags": []}]

            for tag in route_table_data.tags:
                tag_specifications[0]["Tags"].append(tag.to_dictionary())

            self.ec2.create_route_table(
                TagSpecifications=tag_specifications,
                VpcId=route_table_data.vpc_id,
            )

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the route table!")

    def delete(self, route_table_data: RouteTableData) -> None:
        """
        Deletes the route table.
        """
        try:
            self.ec2.delete_route_table(
                RouteTableId=route_table_data.route_table_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the route table!")

    def associate(self, route_table_data: RouteTableData) -> None:
        """
        Associates a list of subnets with a route table.
        """
        try:
            for subnet_id in route_table_data.associated_subnet_ids:
                self.ec2.associate_route_table(
                    RouteTableId=route_table_data.route_table_id,
                    SubnetId=subnet_id,
                )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException(
                "Error associating the subnet to the route table!"
            )


class RouteDao(Ec2Dao):
    def load_all(self, route_table_id: str) -> list:
        """
        Loads all routes belonging to a route table.
        Returns a list of RouteData objects.
        """
        try:
            response = self.ec2.describe_route_tables(
                RouteTableIds=[
                    route_table_id,
                ],
            ).get("RouteTables")[0]

            routes = []

            for route in response.get("Routes"):
                routes.append(RouteData.build(route, route_table_id))

            return routes
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the routes!")

    def create(self, route_data: RouteData) -> None:
        """
        Creates a new route in the route table.
        """
        try:
            self.ec2.create_route(
                DestinationCidrBlock=route_data.destination_cidr,
                GatewayId=route_data.internet_gateway_id,
                RouteTableId=route_data.route_table_id,
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the route!")
