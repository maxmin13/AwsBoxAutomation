"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.subnet import SubnetDao
from com.maxmin.aws.ec2.dao.domain.subnet import SubnetData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class SubnetDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.subnet_dao = SubnetDao()

    @mock_aws
    def test_create_subnet(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tag_datas = []
        subnet_tag_datas.append(TagData("class", "webservices"))
        subnet_tag_datas.append(TagData("name", "mysubnet"))

        subnet_data = SubnetData()
        subnet_data.az = "eu-west-1a"
        subnet_data.cidr = "10.0.10.0/25"
        subnet_data.vpc_id = vpc_id
        subnet_data.tags = subnet_tag_datas

        # run the test
        self.subnet_dao.create(subnet_data)

        response = self.test_utils.describe_subnets("mysubnet")

        assert response[0].get("State") == "available"
        assert response[0].get("CidrBlock") == "10.0.10.0/25"
        assert response[0].get("AvailabilityZone") == "eu-west-1a"
        assert response[0].get("VpcId") == vpc_id

        assert len(response[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", response[0].get("Tags"))
            == "mysubnet"
        )
        assert (
            self.test_utils.get_tag_value("class", response[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_subnet_twice(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tags = []
        subnet_tags.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags.append(self.test_utils.build_tag("name", "mysubnet"))

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags
        )

        subnet_tag_datas = []
        subnet_tag_datas.append(TagData("class", "webservices"))
        subnet_tag_datas.append(TagData("name", "mysubnet"))

        subnet_data = SubnetData()
        subnet_data.az = "eu-west-1a"
        subnet_data.cidr = "10.0.10.0/25"
        subnet_data.vpc_id = vpc_id
        subnet_data.tags = subnet_tag_datas

        try:
            # it fails because of the same IP address
            self.subnet_dao.create(subnet_data)

            fail("An exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the subnet!"
        except Exception:
            fail("An AwsDaoException should have been raised!")

    @mock_aws
    def test_delete_subnet(self):
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

        subnet_data = SubnetData()
        subnet_data.subnet_id = subnet_id

        self.subnet_dao.delete(subnet_data)

        response = self.test_utils.describe_subnets("mysubnet")

        assert len(response) == 0

    @mock_aws
    def test_delete_not_existing_subnet(self):
        subnet_data = SubnetData()
        subnet_data.subnet_id = "1234"

        try:
            self.subnet_dao.delete(subnet_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the subnet!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_subnet(self):
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

        subnet_tags2 = []
        subnet_tags2.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags2.append(self.test_utils.build_tag("name", "mysubnet2"))

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.20.0/25", vpc_id, subnet_tags2
        )

        # run the test
        subnet_data = self.subnet_dao.load(subnet_id1)

        assert subnet_data.subnet_id == subnet_id1
        assert subnet_data.cidr == "10.0.10.0/25"
        assert subnet_data.az == "eu-west-1a"
        assert subnet_data.vpc_id == vpc_id
        assert subnet_data.is_default is False

        assert len(subnet_data.tags) == 2
        assert subnet_data.get_tag_value("name") == "mysubnet1"
        assert subnet_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_subnet_not_found(self):
        try:
            self.subnet_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the subnet!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_subnets_by_tag_name(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        vpc_id2 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags2).get(
            "VpcId"
        )

        subnet_tags1 = []
        subnet_tags1.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags1.append(self.test_utils.build_tag("name", "mysubnet1"))

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id1, subnet_tags1
        )

        subnet_tags2 = []
        subnet_tags2.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags2.append(self.test_utils.build_tag("name", "mysubnet2"))

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.128/25", vpc_id2, subnet_tags2
        ).get("SubnetId")

        # run the test
        subnet_datas = self.subnet_dao.load_all("mysubnet2")

        assert len(subnet_datas) == 1

        assert subnet_datas[0].subnet_id == subnet_id2
        assert subnet_datas[0].cidr == "10.0.10.128/25"
        assert subnet_datas[0].az == "eu-west-1a"
        assert subnet_datas[0].vpc_id == vpc_id2

        assert len(subnet_datas[0].tags) == 2
        assert subnet_datas[0].get_tag_value("name") == "mysubnet2"
        assert subnet_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_subnets_by_tag_name_more_found(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        vpc_id2 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags2).get(
            "VpcId"
        )

        subnet_tags = []
        subnet_tags.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags.append(self.test_utils.build_tag("name", "mysubnet"))

        subnet_id1 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id1, subnet_tags
        ).get("SubnetId")

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.128/25", vpc_id2, subnet_tags
        ).get("SubnetId")

        # run the test
        subnet_datas = self.subnet_dao.load_all("mysubnet")

        assert len(subnet_datas) == 2

        assert subnet_datas[0].subnet_id == subnet_id1
        assert subnet_datas[1].subnet_id == subnet_id2

    @mock_aws
    def test_load_all_subnets_by_tag_name_not_found(self):
        # run the test
        subnet_datas = self.subnet_dao.load_all("mysubnet")

        assert len(subnet_datas) == 0
