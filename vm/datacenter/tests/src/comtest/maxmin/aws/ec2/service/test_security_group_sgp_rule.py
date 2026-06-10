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


class SecurityGroupSgpRuleServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.security_group_service = SecurityGroupService()

    @mock_aws
    def test_create_security_group_rule(self):
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

        # security group that has to be granted access
        access_security_group_tags = []
        access_security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags.append(
            self.test_utils.build_tag("name", "accesssecuritygroup")
        )

        access_security_group_id = self.test_utils.create_security_group(
            "accesssecuritygroup",
            "access security group",
            vpc_id,
            access_security_group_tags,
        ).get("GroupId")

        # run the test
        self.security_group_service.create_security_group_rule(
            "mysecuritygroup",
            80,
            90,
            "tcp",
            "accesssecuritygroup",
            "HTTP access home",
        )

        response = self.test_utils.describe_security_group(security_group_id)

        assert response.get("GroupId") == security_group_id

        assert len(response.get("IpPermissions")) == 1
        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90

        assert (
            len(response.get("IpPermissions")[0].get("UserIdGroupPairs")) == 1
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("GroupId")
            == access_security_group_id
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("Description")
            == "HTTP access home"
        )

    @mock_aws
    def test_create_security_group_rule_twice(self):
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

        # security group that has to be granted access
        access_security_group_tags = []
        access_security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags.append(
            self.test_utils.build_tag("name", "accesssecuritygroup")
        )

        access_security_group_id = self.test_utils.create_security_group(
            "accesssecuritygroup",
            "access security group",
            vpc_id,
            access_security_group_tags,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            access_security_group_id,
            "HTTP access home",
        )

        try:
            # run the test
            self.security_group_service.create_security_group_rule(
                "mysecuritygroup",
                80,
                90,
                "tcp",
                "accesssecuritygroup",
                "HTTP access home",
            )

            fail("ERROR: an exception should have been thrown!")

        except AwsServiceException as e:
            assert str(e) == "Security group rule already created!"
        except Exception:
            fail("ERROR: an AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_security_group_rule(self):
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

        # security group that has to be granted access
        access_security_group_tags1 = []
        access_security_group_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags1.append(
            self.test_utils.build_tag("name", "accesssecuritygroup1")
        )

        access_security_group_id1 = self.test_utils.create_security_group(
            "accesssecuritygroup1",
            "access security group 1",
            vpc_id,
            access_security_group_tags1,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            access_security_group_id1,
            "HTTP access home",
        )

        # security group that has to be granted access
        access_security_group_tags2 = []
        access_security_group_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags2.append(
            self.test_utils.build_tag("name", "accesssecuritygroup2")
        )

        access_security_group_id2 = self.test_utils.create_security_group(
            "accesssecuritygroup2",
            "access security group 2",
            vpc_id,
            access_security_group_tags2,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            access_security_group_id2,
            "HTTP access office",
        )

        # run the test
        self.security_group_service.delete_security_group_rule(
            "mysecuritygroup",
            80,
            90,
            "tcp",
            "accesssecuritygroup1",
            "HTTP access home",
        )

        response = self.test_utils.describe_security_group(security_group_id)

        assert len(response.get("IpPermissions")) == 1

        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90

        assert (
            len(response.get("IpPermissions")[0].get("UserIdGroupPairs")) == 1
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("GroupId")
            == access_security_group_id2
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("Description")
            == "HTTP access office"
        )

    @mock_aws
    def test_delete_not_existing_security_group_rule(self):
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

        # security group that has to be granted access
        access_security_group_tags = []
        access_security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags.append(
            self.test_utils.build_tag("name", "accesssecuritygroup")
        )

        access_security_group_id = self.test_utils.create_security_group(
            "accesssecuritygroup",
            "access security group",
            vpc_id,
            access_security_group_tags,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            access_security_group_id,
            "HTTP access home",
        )

        # run the test
        self.security_group_service.delete_security_group_rule(
            "mysecuritygroup",
            40,
            50,
            "tcp",
            "accesssecuritygroup",
            "HTTP access home",
        )

        pass

    @mock_aws
    def test_load_security_group_rule(self):
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

        # security group that has to be granted access
        access_security_group_tags = []
        access_security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags.append(
            self.test_utils.build_tag("name", "accesssecuritygroup")
        )

        granted_security_group_id = self.test_utils.create_security_group(
            "accesssecuritygroup",
            "access security group",
            vpc_id,
            access_security_group_tags,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            granted_security_group_id,
            "HTTP home",
        )
        self.test_utils.allow_access_from_security_group(
            security_group_id,
            100,
            110,
            "tcp",
            granted_security_group_id,
            "HTTP access office 1",
        )
        self.test_utils.allow_access_from_security_group(
            security_group_id,
            120,
            130,
            "tcp",
            granted_security_group_id,
            "HTTP access office 2",
        )

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup", 80, 90, "tcp", "accesssecuritygroup"
        )

        assert response.from_port == 80
        assert response.to_port == 90
        assert response.protocol == "tcp"
        assert response.granted_security_group_nm == "accesssecuritygroup"
        assert response.description == "HTTP home"

    @mock_aws
    def test_load_security_group_rule_not_found(self):
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

        # security group that has to be granted access
        access_security_group_tags = []
        access_security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        access_security_group_tags.append(
            self.test_utils.build_tag("name", "accesssecuritygroup")
        )

        granted_security_group_id = self.test_utils.create_security_group(
            "accesssecuritygroup",
            "access security group",
            vpc_id,
            access_security_group_tags,
        ).get("GroupId")

        self.test_utils.allow_access_from_security_group(
            security_group_id,
            80,
            90,
            "tcp",
            granted_security_group_id,
            "HTTP home",
        )

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup111", 80, 90, "tcp", "accesssecuritygroup"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup", 80, 90, "tcp", "accesssecuritygroup111"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup", 70, 90, "tcp", "accesssecuritygroup"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup", 80, 100, "tcp", "accesssecuritygroup"
        )

        assert not response

        # run the test
        response = self.security_group_service.load_security_group_rule(
            "mysecuritygroup", 80, 90, "ftp", "accesssecuritygroup"
        )

        assert not response
