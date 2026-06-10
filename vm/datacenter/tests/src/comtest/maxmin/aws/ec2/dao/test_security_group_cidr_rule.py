"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.security_group import (
    CidrRuleData,
    IpRangeData,
)
from com.maxmin.aws.ec2.dao.security_group import CidrRuleDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class CidrRuleDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.cidr_rule_dao = CidrRuleDao()

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

        cidr_rule_data = CidrRuleData()
        cidr_rule_data.security_group_id = security_group_id
        cidr_rule_data.from_port = 80
        cidr_rule_data.to_port = 90
        cidr_rule_data.protocol = "tcp"

        ip_range_data1 = IpRangeData()
        ip_range_data1.cidr_ip = "10.0.10.0/24"
        ip_range_data1.description = "HTTP access home"

        cidr_rule_data.ip_ranges.append(ip_range_data1)

        ip_range_data2 = IpRangeData()
        ip_range_data2.cidr_ip = "10.0.20.0/24"
        ip_range_data2.description = "HTTP access office"

        cidr_rule_data.ip_ranges.append(ip_range_data2)

        # run the test
        self.cidr_rule_dao.create(cidr_rule_data)

        response = self.test_utils.describe_security_group(security_group_id)

        assert response.get("GroupId") == security_group_id

        assert len(response.get("IpPermissions")) == 1
        assert response.get("IpPermissions")[0].get("FromPort") == 80
        assert response.get("IpPermissions")[0].get("ToPort") == 90
        assert len(response.get("IpPermissions")[0].get("IpRanges")) == 2

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

        assert (
            response.get("IpPermissions")[0].get("IpRanges")[1].get("CidrIp")
            == "10.0.20.0/24"
        )
        assert (
            response.get("IpPermissions")[0]
            .get("IpRanges")[1]
            .get("Description")
            == "HTTP access office"
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

        cidr_rule_data = CidrRuleData()
        cidr_rule_data.security_group_id = security_group_id
        cidr_rule_data.from_port = 80
        cidr_rule_data.to_port = 90
        cidr_rule_data.protocol = "tcp"

        ip_range_data = IpRangeData()
        ip_range_data.cidr_ip = "10.0.10.0/24"
        ip_range_data.description = "HTTP access home"

        cidr_rule_data.ip_ranges.append(ip_range_data)

        try:
            # run the test
            self.cidr_rule_dao.create(cidr_rule_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the security group rule!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

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

        cidr_rule_data = CidrRuleData()
        cidr_rule_data.security_group_id = security_group_id
        cidr_rule_data.from_port = 80
        cidr_rule_data.to_port = 90
        cidr_rule_data.protocol = "tcp"

        ip_range_data = IpRangeData()
        ip_range_data.cidr_ip = "10.0.10.0/24"
        ip_range_data.description = "HTTP access home"

        cidr_rule_data.ip_ranges.append(ip_range_data)

        # run the test
        self.cidr_rule_dao.delete(cidr_rule_data)

        response = self.test_utils.describe_security_group(security_group_id)

        assert len(response.get("IpPermissions")) == 0

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

        security_group_id = self.test_utils.create_security_group(
            "mysecuritygroup", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        cidr_rule_data = CidrRuleData()
        cidr_rule_data.security_group_id = security_group_id
        cidr_rule_data.from_port = 80
        cidr_rule_data.to_port = 90
        cidr_rule_data.protocol = "tcp"

        ip_range_data = IpRangeData()
        ip_range_data.cidr_ip = "10.0.10.0/24"
        ip_range_data.description = "HTTP access home"

        cidr_rule_data.ip_ranges.append(ip_range_data)

        try:
            # run the test
            self.cidr_rule_dao.delete(cidr_rule_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the security group rule!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_cidr_rules(self):
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
        cidr_rule_datas = self.cidr_rule_dao.load_all(security_group_id)

        assert len(cidr_rule_datas) == 2

        # first rule allows access to one range of IPs addresses.
        assert cidr_rule_datas[0].security_group_id == security_group_id
        assert cidr_rule_datas[0].from_port == 80
        assert cidr_rule_datas[0].to_port == 90
        assert cidr_rule_datas[0].protocol == "tcp"

        assert len(cidr_rule_datas[0].ip_ranges) == 1

        assert cidr_rule_datas[0].ip_ranges[0].cidr_ip == "10.0.10.0/24"
        assert (
            cidr_rule_datas[0].ip_ranges[0].description == "HTTP access home"
        )

        # second rule allows access to two ranges of IPs addresses.
        assert cidr_rule_datas[1].security_group_id == security_group_id
        assert cidr_rule_datas[1].from_port == 100
        assert cidr_rule_datas[1].to_port == 110
        assert cidr_rule_datas[1].protocol == "tcp"

        assert len(cidr_rule_datas[1].ip_ranges) == 2

        assert cidr_rule_datas[1].ip_ranges[0].cidr_ip == "10.0.20.0/24"
        assert (
            cidr_rule_datas[1].ip_ranges[0].description
            == "HTTP access office 1"
        )

        assert cidr_rule_datas[1].ip_ranges[1].cidr_ip == "10.0.30.0/24"
        assert (
            cidr_rule_datas[1].ip_ranges[1].description
            == "HTTP access office 2"
        )

    @mock_aws
    def test_load_all_cidr_rules_not_found(self):
        try:
            # run the test
            self.cidr_rule_dao.load_all("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the security group rules!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")
