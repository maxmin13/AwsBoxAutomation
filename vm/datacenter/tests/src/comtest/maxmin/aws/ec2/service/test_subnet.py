"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from pytest import fail

from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils
from moto import mock_aws
from com.maxmin.aws.ec2.service.subnet import SubnetService
from com.maxmin.aws.ec2.service.domain.tag import Tag


class SubnetServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.subnet_service = SubnetService()

    @mock_aws
    def test_create_subnet(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        subnet_tags = []
        subnet_tags.append(Tag("class", "webservices"))

        # run the test
        self.subnet_service.create_subnet(
            "mysubnet", "eu-west-1a", "10.0.10.0/25", "myvpc", subnet_tags
        )

        subnets = self.test_utils.describe_subnets("mysubnet")

        assert subnets[0].get("State") == "available"
        assert subnets[0].get("CidrBlock") == "10.0.10.0/25"
        assert subnets[0].get("AvailabilityZone") == "eu-west-1a"
        assert subnets[0].get("VpcId") == vpc_id

        assert len(subnets[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", subnets[0].get("Tags"))
            == "mysubnet"
        )
        assert (
            self.test_utils.get_tag_value("class", subnets[0].get("Tags"))
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

        subnet_tags = []
        subnet_tags.append(Tag("class", "webservices"))

        try:
            self.subnet_service.create_subnet(
                "mysubnet",
                "eu-west-1a",
                "10.0.10.128/25",
                "myvpc",
                subnet_tags,
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Subnet already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

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

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags
        )

        # run the test
        self.subnet_service.delete_subnet("mysubnet")

        subnets = self.test_utils.describe_subnets("mysubnet")

        assert len(subnets) == 0

    @mock_aws
    def test_delete_not_existing_subnet(self):
        self.subnet_service.delete_subnet("mysubnet")

        # no error expected
        pass

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

        subnet_tag2 = []
        subnet_tag2.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tag2.append(self.test_utils.build_tag("name", "mysubnet2"))

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.20.0/25", vpc_id, subnet_tag2
        )

        # run the test
        subnet = self.subnet_service.load_subnet("mysubnet1")

        assert subnet.subnet_id == subnet_id1
        assert subnet.cidr == "10.0.10.0/25"
        assert subnet.az == "eu-west-1a"
        assert subnet.vpc_id == vpc_id

        assert len(subnet.tags) == 2
        assert subnet.get_tag_value("name") == "mysubnet1"
        assert subnet.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_subnet_more_found(self):
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

        self.test_utils.create_subnet(
            "eu-west-1a", "10.0.20.0/25", vpc_id, subnet_tags
        )

        try:
            # run the test
            self.subnet_service.load_subnet("mysubnet")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one subnet!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_subnet_not_found(self):
        subnet = self.subnet_service.load_subnet("mysubnet")

        assert not subnet
