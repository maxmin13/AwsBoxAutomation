"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.dao.domain.vpc import VpcData
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class VpcDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.vpc_dao = VpcDao()

    @mock_aws
    def test_create_vpc(self):
        vpc_tag_datas = []
        vpc_tag_datas.append(TagData("class", "webservices"))
        vpc_tag_datas.append(TagData("name", "myvpc"))

        vpc_data = VpcData()
        vpc_data.cidr = "10.0.10.0/16"
        vpc_data.tags = vpc_tag_datas

        # run the test
        self.vpc_dao.create(vpc_data)

        vpcs = self.test_utils.describe_vpcs("myvpc")

        assert vpcs[0].get("VpcId")
        assert vpcs[0].get("State") == "available"
        assert vpcs[0].get("CidrBlock") == "10.0.10.0/16"

        assert len(vpcs[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", vpcs[0].get("Tags"))
            == "myvpc"
        )
        assert (
            self.test_utils.get_tag_value("class", vpcs[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_vpc_twice(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", vpc_tags)

        vpc_tag_datas = []
        vpc_tag_datas.append(TagData("class", "webservices"))
        vpc_tag_datas.append(TagData("name", "myvpc"))

        vpc_data = VpcData()
        vpc_data.cidr = "10.0.10.0/16"
        vpc_data.tags = vpc_tag_datas

        # run the test
        self.vpc_dao.create(vpc_data)

        vpcs = self.test_utils.describe_vpcs("myvpc")

        assert len(vpcs) == 2

    @mock_aws
    def test_delete_vpc(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        vpc_data = VpcData()
        vpc_data.vpc_id = vpc_id

        # run the test
        self.vpc_dao.delete(vpc_data)

        vpcs = self.test_utils.describe_vpcs("myvpc")

        assert len(vpcs) == 0

    @mock_aws
    def test_delete_not_existing_vpc(self):
        vpc_data = VpcData()
        vpc_data.vpc_id = "1234"

        try:
            # run the test
            self.vpc_dao.delete(vpc_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the VPC!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_vpc(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        self.test_utils.create_vpc("10.0.20.0/16", vpc_tags2)

        # run the test
        vpc_data = self.vpc_dao.load(vpc_id1)

        assert vpc_data.vpc_id == vpc_id1
        assert vpc_data.cidr == "10.0.10.0/16"
        assert vpc_data.state == "available"

        assert len(vpc_data.tags) == 2
        assert vpc_data.get_tag_value("name") == "myvpc1"
        assert vpc_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_vpcs_by_tag_name(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        self.test_utils.create_vpc("10.0.20.0/16", vpc_tags2)

        # run the test
        vpc_datas = self.vpc_dao.load_all("myvpc1")

        assert len(vpc_datas) == 1

        assert vpc_datas[0].vpc_id == vpc_id1
        assert vpc_datas[0].cidr == "10.0.10.0/16"
        assert vpc_datas[0].state == "available"

        assert len(vpc_datas[0].tags) == 2
        assert vpc_datas[0].get_tag_value("name") == "myvpc1"
        assert vpc_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_vpcs_by_tag_name_more_found(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", vpc_tags)

        self.test_utils.create_vpc("10.0.20.0/16", vpc_tags)

        # run the test
        vpc_datas = self.vpc_dao.load_all("myvpc")

        assert len(vpc_datas) == 2

    @mock_aws
    def test_load_all_vpcs_by_tag_name_not_found(self):
        vpc_datas = self.vpc_dao.load_all("myvpc")

        assert len(vpc_datas) == 0
