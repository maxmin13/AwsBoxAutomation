"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.security_group import (
    SecurityGroupRuleData,
    UserIdGroupPairData,
)
from com.maxmin.aws.ec2.dao.security_group import SecurityGroupRuleDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class SecurityGroupRuleDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.security_group_rule_dao = SecurityGroupRuleDao()

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

        security_group_rule_data = SecurityGroupRuleData()
        security_group_rule_data.security_group_id = security_group_id
        security_group_rule_data.from_port = 80
        security_group_rule_data.to_port = 90
        security_group_rule_data.protocol = "tcp"

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
            "access security group1",
            vpc_id,
            access_security_group_tags1,
        ).get("GroupId")
        user_id_group_pair_data1 = UserIdGroupPairData()
        user_id_group_pair_data1.group_id = access_security_group_id1
        user_id_group_pair_data1.description = "HTTP access home"

        security_group_rule_data.user_id_group_pairs.append(
            user_id_group_pair_data1
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
            "access security group2",
            vpc_id,
            access_security_group_tags2,
        ).get("GroupId")
        user_id_group_pair_data2 = UserIdGroupPairData()
        user_id_group_pair_data2.group_id = access_security_group_id2
        user_id_group_pair_data2.description = "HTTP access office"

        security_group_rule_data.user_id_group_pairs.append(
            user_id_group_pair_data2
        )

        # run the test
        self.security_group_rule_dao.create(security_group_rule_data)

        response = self.test_utils.describe_security_group(security_group_id)

        assert response.get("GroupId") == security_group_id

        assert len(response.get("IpPermissions")) == 1
        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90

        assert (
            len(response.get("IpPermissions")[0].get("UserIdGroupPairs")) == 2
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("GroupId")
            == access_security_group_id1
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[0]
            .get("Description")
            == "HTTP access home"
        )

        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[1]
            .get("GroupId")
            == access_security_group_id2
        )
        assert (
            response.get("IpPermissions")[0]
            .get("UserIdGroupPairs")[1]
            .get("Description")
            == "HTTP access office"
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

        security_group_rule_data = SecurityGroupRuleData()
        security_group_rule_data.security_group_id = security_group_id
        security_group_rule_data.from_port = 80
        security_group_rule_data.to_port = 90
        security_group_rule_data.protocol = "tcp"

        user_id_group_pair_data = UserIdGroupPairData()
        user_id_group_pair_data.group_id = access_security_group_id
        user_id_group_pair_data.description = "HTTP access home"

        security_group_rule_data.user_id_group_pairs.append(
            user_id_group_pair_data
        )

        try:
            # run the test
            self.security_group_rule_dao.create(security_group_rule_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the security group rule!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

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

        security_group_rule_data = SecurityGroupRuleData()
        security_group_rule_data.security_group_id = security_group_id
        security_group_rule_data.from_port = 80
        security_group_rule_data.to_port = 90
        security_group_rule_data.protocol = "tcp"

        user_id_group_pair_data = UserIdGroupPairData()
        user_id_group_pair_data.group_id = access_security_group_id
        user_id_group_pair_data.description = "HTTP access home"

        security_group_rule_data.user_id_group_pairs.append(
            user_id_group_pair_data
        )

        # run the tests
        self.security_group_rule_dao.delete(security_group_rule_data)

        response = self.test_utils.describe_security_group(security_group_id)

        assert len(response.get("IpPermissions")) == 0

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

        security_group_rule_data = SecurityGroupRuleData()
        security_group_rule_data.security_group_id = security_group_id
        security_group_rule_data.from_port = 80
        security_group_rule_data.to_port = 90
        security_group_rule_data.protocol = "tcp"

        user_id_group_pair_data = UserIdGroupPairData()
        user_id_group_pair_data.group_id = "1234"
        user_id_group_pair_data.description = "HTTP access home"

        security_group_rule_data.user_id_group_pairs.append(
            user_id_group_pair_data
        )

        try:
            # run the tests
            self.security_group_rule_dao.delete(security_group_rule_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the security group rule!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_security_group_rules(self):
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
        security_group_rules = self.security_group_rule_dao.load_all(
            security_group_id
        )

        assert len(security_group_rules) == 1

        assert security_group_rules[0].security_group_id == security_group_id
        assert security_group_rules[0].from_port == 80
        assert security_group_rules[0].to_port == 90
        assert security_group_rules[0].protocol == "tcp"

        assert len(security_group_rules[0].user_id_group_pairs) == 1

        assert (
            security_group_rules[0].user_id_group_pairs[0].group_id
            == access_security_group_id
        )
        assert (
            security_group_rules[0].user_id_group_pairs[0].description
            == "HTTP access home"
        )

    @mock_aws
    def test_load_all_security_group_rules_not_found(self):
        try:
            # run test
            self.security_group_rule_dao.load_all("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the security group rules!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")
