"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger

from com.maxmin.aws.ec2.service.domain.tag import Tag
from comtest.maxmin.aws.utils import TestUtils


class VpcServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.vpc_service = VpcService()

    @mock_aws
    def test_create_vpc(self):
        tags = []
        tags.append(Tag("class", "webservices"))

        # run the test
        self.vpc_service.create_vpc("myvpc", "10.0.10.0/16", tags)

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
        tags = []
        tags.append(self.test_utils.build_tag("class", "webservices"))
        tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", tags)

        tags = []
        tags.append(Tag("class", "webservices"))

        try:
            # run the test
            self.vpc_service.create_vpc("myvpc", "10.0.10.0/16", tags)

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "VPC already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_vpc(self):
        tags = []
        tags.append(self.test_utils.build_tag("class", "webservices"))
        tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", tags)

        # run the test
        self.vpc_service.delete_vpc("myvpc")

        vpcs = self.test_utils.describe_vpcs("myvpc")

        assert len(vpcs) == 0

    @mock_aws
    def test_delete_not_existing_vpc(self):
        self.vpc_service.delete_vpc("myvpc")

        # no error expected
        pass

    @mock_aws
    def test_load_vpc(self):
        tags = []
        tags.append(self.test_utils.build_tag("class", "webservices"))
        tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", tags).get("VpcId")

        # run the test
        vpc = self.vpc_service.load_vpc("myvpc")

        assert vpc.vpc_id == vpc_id
        assert vpc.cidr == "10.0.10.0/16"
        assert vpc.state == "available"

        assert len(vpc.tags) == 2
        assert vpc.get_tag_value("name") == "myvpc"
        assert vpc.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_vpc_more_found(self):
        tags = []
        tags.append(self.test_utils.build_tag("class", "webservices"))
        tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", tags)
        self.test_utils.create_vpc("10.0.10.0/16", tags)

        try:
            # run the test
            self.vpc_service.load_vpc("myvpc")

            fail("ERROR: an exception should have been thrown!")

        except AwsServiceException as e:
            assert str(e) == "Found more than one VPC!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_vpc_not_found(self):
        vpc = self.vpc_service.load_vpc("myvpc")

        assert not vpc
