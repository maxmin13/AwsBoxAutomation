"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail


from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils
from com.maxmin.aws.ec2.dao.route_table import RouteDao
from com.maxmin.aws.ec2.dao.domain.route_table import RouteData


class RouteDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.route_dao = RouteDao()

    @mock_aws
    def test_create_route(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        route_table_tags = []
        route_table_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags.append(
            self.test_utils.build_tag("name", "myroutetable")
        )

        route_table_id = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")

        route_data = RouteData()
        route_data.route_table_id = route_table_id
        route_data.internet_gateway_id = internet_gateway_id
        route_data.destination_cidr = "0.0.0.0/0"

        # Run the test
        self.route_dao.create(route_data)

        response = self.test_utils.describe_route_tables("myroutetable")

        assert response[0].get("RouteTableId") == route_table_id
        assert len(response[0].get("Routes")) == 2
        assert response[0].get("Routes")[0].get("Origin") == "CreateRouteTable"

        assert response[0].get("Routes")[1].get("Origin") == "CreateRoute"
        assert (
            response[0].get("Routes")[1].get("DestinationCidrBlock")
            == "0.0.0.0/0"
        )
        assert (
            response[0].get("Routes")[1].get("GatewayId")
            == internet_gateway_id
        )
        assert response[0].get("Routes")[1].get("State") == "active"

    @mock_aws
    def test_create_route_twice(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        route_table_tags = []
        route_table_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags.append(
            self.test_utils.build_tag("name", "myroutetable")
        )

        route_table_id = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")

        self.test_utils.create_route(
            route_table_id, internet_gateway_id, "0.0.0.0/0"
        )

        route_data = RouteData()
        route_data.route_table_id = route_table_id
        route_data.internet_gateway_id = internet_gateway_id
        route_data.destination_cidr = "0.0.0.0/0"

        try:
            # Run the test: it fails because of the same destination cidr
            self.route_dao.create(route_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the route!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_routes(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        route_table_tags = []
        route_table_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags.append(
            self.test_utils.build_tag("name", "myroutetable")
        )

        route_table_id = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")

        self.test_utils.create_route(
            route_table_id, internet_gateway_id, "10.0.10.0/24"
        )

        self.test_utils.create_route(
            route_table_id, internet_gateway_id, "10.0.20.0/24"
        )

        # Run the test
        routes = self.route_dao.load_all(route_table_id)

        assert len(routes) == 3

        assert routes[0].origin == "CreateRouteTable"

        assert routes[1].origin == "CreateRoute"
        assert routes[1].destination_cidr == "10.0.10.0/24"
        assert routes[1].internet_gateway_id == internet_gateway_id
        assert routes[1].state == "active"

        assert routes[2].origin == "CreateRoute"
        assert routes[2].destination_cidr == "10.0.20.0/24"
        assert routes[2].internet_gateway_id == internet_gateway_id
        assert routes[2].state == "active"

    @mock_aws
    def test_load_all_routes_not_found(self):
        try:
            self.route_dao.load_all("1234")

        except AwsDaoException as e:
            assert str(e) == "Error loading the routes!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")
