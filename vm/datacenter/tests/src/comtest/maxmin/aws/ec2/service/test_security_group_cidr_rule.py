"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from pytest import fail

from com.maxmin.aws.exception import AwsServiceException
from moto import mock_aws
from com.maxmin.aws.ec2.service.security_group import SecurityGroupService
from comtest.maxmin.aws.utils import TestUtils


class SecurityGroupCidrRuleServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.security_group_service = SecurityGroupService()

    @mock_aws
    def test_create_cidr_rule(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        # run the test
        self.security_group_service.create_cidr_rule(
            "mysecuritygroup",
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )

        response = self.test_utils.describe_security_group(security_group_id)

        assert response.get("GroupId") == security_group_id

        assert len(response.get("IpPermissions")) == 1
        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90
        assert len(response.get("IpPermissions")[0].get("IpRanges")) == 1

        assert (
            response.get("IpPermissions")[0].get("IpRanges")[0].get("CidrIp")
            == "10.0.10.0/24"
        )
        assert (
            response.get("IpPermissions")[0]
            .get("IpRanges")[0]
            .get("Description")
            == "HTTP access home"
        )

    @mock_aws
    def test_create_cidr_rule_twice(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )

        try:
            # run the test
            self.security_group_service.create_cidr_rule(
                "mysecuritygroup",
                80,
                90,
                "tcp",
                "10.0.10.0/24",
                "HTTP access home",
            )

            fail("ERROR: an exception should have been thrown!")

        except AwsServiceException as e:
            assert str(e) == "Security group rule already created!"
        except Exception:
            fail("ERROR: an AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_cidr_rule(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "10.10.10.10/24",
            "HTTP access office 1",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "20.20.20.20/24",
            "HTTP access office 2",
        )

        # run the test
        self.security_group_service.delete_cidr_rule(
            "mysecuritygroup",
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )

        response = self.test_utils.describe_security_group(security_group_id)

        assert response.get("GroupId") == security_group_id

        assert len(response.get("IpPermissions")) == 1

        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90

        assert len(response.get("IpPermissions")[0].get("IpRanges")) == 2

        assert (
            response.get("IpPermissions")[0].get("IpRanges")[0].get("CidrIp")
            == "10.10.10.10/24"
        )
        assert (
            response.get("IpPermissions")[0]
            .get("IpRanges")[0]
            .get("Description")
            == "HTTP access office 1"
        )

        assert (
            response.get("IpPermissions")[0].get("IpRanges")[1].get("CidrIp")
            == "20.20.20.20/24"
        )
        assert (
            response.get("IpPermissions")[0]
            .get("IpRanges")[1]
            .get("Description")
            == "HTTP access office 2"
        )

    @mock_aws
    def test_delete_not_existing_cidr_rule(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        )

        # run the test
        self.security_group_service.delete_cidr_rule(
            "mysecuritygroup",
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )

        pass

    @mock_aws
    def test_load_cidr_rule(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            100,
            110,
            "tcp",
            "10.0.20.0/24",
            "HTTP access office 1",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            100,
            110,
            "tcp",
            "10.0.30.0/24",
            "HTTP access office 2",
        )

        # run the test
        response = self.security_group_service.load_cidr_rule(
            "mysecuritygroup", 80, 90, "tcp", "10.0.10.0/24"
        )

        assert response.from_port == 80
        assert response.to_port == 90
        assert response.protocol == "tcp"
        assert response.granted_cidr == "10.0.10.0/24"
        assert response.description == "HTTP access home"

    @mock_aws
    def test_load_cidr_rule_not_found(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        self.test_utils.allow_access_from_cidr(
            security_group_id,
            80,
            90,
            "tcp",
            "10.0.10.0/24",
            "HTTP access home",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            100,
            110,
            "tcp",
            "10.0.20.0/24",
            "HTTP access office 1",
        )
        self.test_utils.allow_access_from_cidr(
            security_group_id,
            100,
            110,
            "tcp",
            "10.0.30.0/24",
            "HTTP access office 2",
        )

        try:
            # run the test
            self.security_group_service.load_cidr_rule(
                "mysecuritygroup111", 80, 90, "tcp", "10.0.10.0/24"
            )

            fail("ERROR: an exception should have been thrown!")

        except AwsServiceException as e:
            assert str(e) == "Security group not found!"
        except Exception:
            fail("ERROR: an AwsServiceException should have been raised!")

        # run the test
        response = self.security_group_service.load_cidr_rule(
            "mysecuritygroup", 80, 90, "tcp", "10.10.10.10/24"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_cidr_rule(
            "mysecuritygroup", 70, 90, "tcp", "10.0.10.0/24"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_cidr_rule(
            "mysecuritygroup", 80, 100, "tcp", "10.0.10.0/24"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_cidr_rule(
            "mysecuritygroup", 80, 90, "ftp", "10.0.10.0/24"
        )

        assert not response
