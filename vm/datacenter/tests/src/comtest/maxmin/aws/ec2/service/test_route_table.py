"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.route_table import RouteTableService

from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils


class RouteTableServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.route_table_service = RouteTableService()

    @mock_aws
    def test_create_route_table(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        route_table_tags = []
        route_table_tags.append(Tag("class", "webservices"))

        # run the test
        self.route_table_service.create_route_table(
            "myroutetable", "myvpc", route_table_tags
        )

        route_tables = self.test_utils.describe_route_tables("myroutetable")

        assert route_tables[0].get("RouteTableId")
        assert route_tables[0].get("VpcId") == vpc_id
        assert len(route_tables[0].get("Routes")) == 1
        assert (
            route_tables[0].get("Routes")[0].get("Origin")
            == "CreateRouteTable"
        )
        assert len(route_tables[0].get("Associations")) == 0

        assert len(route_tables[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", route_tables[0].get("Tags"))
            == "myroutetable"
        )
        assert (
            self.test_utils.get_tag_value("class", route_tables[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_route_table_twice(self):
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

        self.test_utils.create_route_table(vpc_id, route_table_tags)

        route_table_tags = []
        route_table_tags.append(Tag("class", "webservices"))

        try:
            self.route_table_service.create_route_table(
                "myroutetable", "myvpc", route_table_tags
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Route table already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_route_table(self):
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

        self.test_utils.create_route_table(vpc_id, route_table_tags)

        # run the test
        self.route_table_service.delete_route_table("myroutetable")

        route_tables = self.test_utils.describe_route_tables("myroutetable")

        assert len(route_tables) == 0

    @mock_aws
    def test_delete_not_existing_route_table(self):
        self.route_table_service.delete_route_table("myroutetable")

        # no error expected
        pass

    @mock_aws
    def test_load_route_table(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tags = []
        subnet_tags.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags.append(self.test_utils.build_tag("name", "mysubnet"))

        subnet_id = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags
        ).get("SubnetId")

        route_table_tags1 = []
        route_table_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags1.append(
            self.test_utils.build_tag("name", "myroutetable1")
        )

        route_table_id1 = self.test_utils.create_route_table(
            vpc_id, route_table_tags1
        ).get("RouteTableId")
        self.test_utils.associate_subnet_to_route_table(
            subnet_id, route_table_id1
        )

        route_table_tags2 = []
        route_table_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags2.append(
            self.test_utils.build_tag("name", "myroutetable2")
        )

        # run the test
        route_table = self.route_table_service.load_route_table(
            "myroutetable1"
        )

        assert route_table.route_table_id == route_table_id1
        assert route_table.vpc_id == vpc_id
        assert len(route_table.associated_subnet_ids) == 1
        assert route_table.associated_subnet_ids[0] == subnet_id

        assert len(route_table.tags) == 2
        assert route_table.get_tag_value("name") == "myroutetable1"
        assert route_table.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_route_table_more_found(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tags1 = []
        subnet_tags1.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags1.append(self.test_utils.build_tag("name", "mysubnet1"))

        subnet_id1 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags1
        ).get("SubnetId")

        route_table_tags = []
        route_table_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags.append(
            self.test_utils.build_tag("name", "myroutetable")
        )

        route_table_id1 = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")
        self.test_utils.associate_subnet_to_route_table(
            subnet_id1, route_table_id1
        )

        subnet_tags2 = []
        subnet_tags2.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags2.append(self.test_utils.build_tag("name", "mysubnet2"))

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.20.0/25", vpc_id, subnet_tags2
        ).get("SubnetId")

        route_table_id2 = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")
        self.test_utils.associate_subnet_to_route_table(
            subnet_id2, route_table_id2
        )

        try:
            # run the test
            self.route_table_service.load_route_table("myroutetable")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one route table!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_route_table_not_found(self):
        route_table = self.route_table_service.load_route_table("myroutetable")

        assert not route_table

    @mock_aws
    def test_associate_route_table(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tags = []
        subnet_tags.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags.append(self.test_utils.build_tag("name", "mysubnet"))

        subnet_id = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags
        ).get("SubnetId")

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

        # run the test
        self.route_table_service.associate_route_table(
            "myroutetable", "mysubnet"
        )

        response = self.test_utils.describe_route_table(route_table_id)

        assert len(response.get("Associations")) == 1
        assert response.get("Associations")[0].get("SubnetId") == subnet_id

    @mock_aws
    def test_load_route(self):
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

        # run the test
        route = self.route_table_service.load_route(
            "myroutetable", "myinternetgateway", "10.0.20.0/24"
        )

        assert route.origin == "CreateRoute"
        assert route.destination_cidr == "10.0.20.0/24"
        assert route.internet_gateway_id == internet_gateway_id
        assert route.state == "active"
