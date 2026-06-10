"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.route_table import RouteTableDao
from com.maxmin.aws.ec2.dao.domain.route_table import RouteTableData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class RouteTableDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.route_table_dao = RouteTableDao()

    @mock_aws
    def test_create_route_table(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        route_table_tag_datas = []
        route_table_tag_datas.append(TagData("class", "webservices"))
        route_table_tag_datas.append(TagData("name", "myroutetable"))

        route_table_data = RouteTableData()
        route_table_data.vpc_id = vpc_id
        route_table_data.tags = route_table_tag_datas

        # run the test
        self.route_table_dao.create(route_table_data)

        response = self.test_utils.describe_route_tables("myroutetable")

        assert response[0].get("RouteTableId")
        assert response[0].get("VpcId") == vpc_id
        assert len(response[0].get("Routes")) == 1
        assert response[0].get("Routes")[0].get("Origin") == "CreateRouteTable"
        assert len(response[0].get("Associations")) == 0

        assert len(response[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", response[0].get("Tags"))
            == "myroutetable"
        )
        assert (
            self.test_utils.get_tag_value("class", response[0].get("Tags"))
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

        route_table_tag_datas = []
        route_table_tag_datas.append(TagData("class", "webservices"))
        route_table_tag_datas.append(TagData("name", "myroutetable"))

        route_table_data = RouteTableData()
        route_table_data.vpc_id = vpc_id
        route_table_data.tags = route_table_tag_datas

        # run the test
        self.route_table_dao.create(route_table_data)

        response = self.test_utils.describe_route_tables("myroutetable")

        assert len(response) == 2

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

        route_table_id = self.test_utils.create_route_table(
            vpc_id, route_table_tags
        ).get("RouteTableId")

        route_table_data = RouteTableData()
        route_table_data.route_table_id = route_table_id

        self.route_table_dao.delete(route_table_data)

        response = self.test_utils.describe_route_tables("myroutetable")

        assert len(response) == 0

    @mock_aws
    def test_delete_not_existing_route_table(self):
        route_table_data = RouteTableData()
        route_table_data.route_table_id = "1234"

        try:
            self.route_table_dao.delete(route_table_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the route table!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

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

        self.test_utils.create_route_table(vpc_id, route_table_tags2).get(
            "RouteTableId"
        )

        # run the test
        route_table_data = self.route_table_dao.load(route_table_id1)

        assert route_table_data.route_table_id == route_table_id1
        assert route_table_data.vpc_id == vpc_id
        assert len(route_table_data.associated_subnet_ids) == 1
        assert route_table_data.associated_subnet_ids[0] == subnet_id

        assert len(route_table_data.tags) == 2
        assert route_table_data.get_tag_value("name") == "myroutetable1"
        assert route_table_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_route_table_not_found(self):
        try:
            self.route_table_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the route table!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_route_tables_by_tag_name(self):
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
            subnet_id1, route_table_id1
        )

        subnet_tags2 = []
        subnet_tags2.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags2.append(self.test_utils.build_tag("name", "mysubnet2"))

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.20.0/25", vpc_id, subnet_tags2
        ).get("SubnetId")

        route_table_tags2 = []
        route_table_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        route_table_tags2.append(
            self.test_utils.build_tag("name", "myroutetable2")
        )

        route_table_id2 = self.test_utils.create_route_table(
            vpc_id, route_table_tags2
        ).get("RouteTableId")
        self.test_utils.associate_subnet_to_route_table(
            subnet_id2, route_table_id2
        )

        # run the test
        route_table_datas = self.route_table_dao.load_all("myroutetable1")

        assert len(route_table_datas) == 1

        assert route_table_datas[0].route_table_id == route_table_id1
        assert route_table_datas[0].vpc_id == vpc_id
        assert len(route_table_datas[0].associated_subnet_ids) == 1
        assert route_table_datas[0].associated_subnet_ids[0] == subnet_id1

        assert len(route_table_datas[0].tags) == 2
        assert route_table_datas[0].get_tag_value("name") == "myroutetable1"
        assert route_table_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_route_tables_by_tag_name_more_found(self):
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

        # run the test
        route_table_datas = self.route_table_dao.load_all("myroutetable")

        assert len(route_table_datas) == 2

    @mock_aws
    def test_load_all_route_tables_by_tag_name_not_found(self):
        # run the test
        route_table_datas = self.route_table_dao.load_all("myroutetable")

        assert len(route_table_datas) == 0
