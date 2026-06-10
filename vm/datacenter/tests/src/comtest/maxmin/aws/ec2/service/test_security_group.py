"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.security_group import SecurityGroupService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils


class SecurityGroupServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.security_group_service = SecurityGroupService()

    @mock_aws
    def test_create_security_group(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags = []
        security_group_tags.append(Tag("class", "webservices"))

        # run the test
        self.security_group_service.create_security_group(
            "mysecuritygroup",
            "my security group",
            "myvpc",
            security_group_tags,
        )

        security_groups = self.test_utils.describe_security_groups(
            "mysecuritygroup"
        )

        assert security_groups[0].get("GroupId")
        assert security_groups[0].get("GroupName") == "mysecuritygroup"
        assert security_groups[0].get("Description") == "my security group"
        assert security_groups[0].get("VpcId") == vpc_id
        assert len(security_groups[0].get("IpPermissions")) == 0
        assert len(security_groups[0].get("IpPermissionsEgress")) == 1

        # verify it's the default egress rule
        assert (
            security_groups[0]
            .get("IpPermissionsEgress")[0]
            .get("IpRanges")[0]
            .get("CidrIp")
            == "0.0.0.0/0"
        )

        assert len(security_groups[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value(
                "name", security_groups[0].get("Tags")
            )
            == "mysecuritygroup"
        )
        assert (
            self.test_utils.get_tag_value(
                "class", security_groups[0].get("Tags")
            )
            == "webservices"
        )

    @mock_aws
    def test_create_security_group_twice(self):
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
            "MYSECURITYGROUP", "my security group", vpc_id, security_group_tags
        )

        security_group_tags = []
        security_group_tags.append(Tag("class", "webservices"))

        try:
            # run the test
            self.security_group_service.create_security_group(
                "mysecuritygroup",
                "my security group",
                "myvpc",
                security_group_tags,
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Security group already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_security_group(self):
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
            "MYSECURITYGROUP", "my security group", vpc_id, security_group_tags
        )

        # run the test
        self.security_group_service.delete_security_group("mysecuritygroup")

        security_groups = self.test_utils.describe_security_groups(
            "mysecuritygroup"
        )

        assert len(security_groups) == 0

    @mock_aws
    def test_delete_not_existing_security_group(self):
        self.security_group_service.delete_security_group("mysecuritygroup")

        # no error expected
        pass

    @mock_aws
    def test_load_security_group(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tags1 = []
        security_group_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags1.append(
            self.test_utils.build_tag("name", "mysecuritygroup1")
        )

        security_group_id1 = self.test_utils.create_security_group(
            "MYSECURITYGROUP1",
            "my security group",
            vpc_id,
            security_group_tags1,
        ).get("GroupId")

        security_group_tags2 = []
        security_group_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags2.append(
            self.test_utils.build_tag("name", "mysecuritygroup2")
        )

        self.test_utils.create_security_group(
            "MYSECURITYGROUP2",
            "my security group",
            vpc_id,
            security_group_tags2,
        )

        # run the test
        security_group = self.security_group_service.load_security_group(
            "mysecuritygroup1"
        )

        assert security_group.security_group_id == security_group_id1
        assert security_group.description == "my security group"
        assert security_group.vpc_id == vpc_id

        assert len(security_group.tags) == 2
        assert security_group.get_tag_value("name") == "mysecuritygroup1"
        assert security_group.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_security_group_more_found(self):
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
            "MYSECURITYGROUP1",
            "my security group1",
            vpc_id,
            security_group_tags,
        )

        self.test_utils.create_security_group(
            "MYSECURITYGROUP2",
            "my security group2",
            vpc_id,
            security_group_tags,
        )

        try:
            # run the test
            self.security_group_service.load_security_group("mysecuritygroup")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one security group!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_security_group_not_found(self):
        security_group = self.security_group_service.load_security_group(
            "mysecuritygroup"
        )

        assert not security_group
