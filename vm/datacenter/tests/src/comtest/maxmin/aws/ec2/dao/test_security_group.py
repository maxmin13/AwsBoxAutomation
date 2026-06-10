"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.security_group import SecurityGroupData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.security_group import SecurityGroupDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class SecurityGroupDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.security_group_dao = SecurityGroupDao()

    @mock_aws
    def test_create_security_group(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        security_group_tag_datas = []
        security_group_tag_datas.append(TagData("class", "webservices"))
        security_group_tag_datas.append(TagData("name", "mysecuritygroup"))

        security_group_data = SecurityGroupData()
        security_group_data.security_group_nm = "MYSECURITYGROUP"
        security_group_data.description = "my security group"
        security_group_data.vpc_id = vpc_id
        security_group_data.tags = security_group_tag_datas

        # run the test
        self.security_group_dao.create(security_group_data)

        response = self.test_utils.describe_security_groups("mysecuritygroup")

        assert response[0].get("GroupId")
        assert response[0].get("GroupName") == "MYSECURITYGROUP"
        assert response[0].get("Description") == "my security group"
        assert response[0].get("VpcId") == vpc_id
        assert len(response[0].get("IpPermissions")) == 0
        assert len(response[0].get("IpPermissionsEgress")) == 1

        # verify it's the default egress rule
        assert (
            response[0]
            .get("IpPermissionsEgress")[0]
            .get("IpRanges")[0]
            .get("CidrIp")
            == "0.0.0.0/0"
        )

        assert len(response[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", response[0].get("Tags"))
            == "mysecuritygroup"
        )
        assert (
            self.test_utils.get_tag_value("class", response[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_security_group_twice_same_tag_name(self):
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
            "MYSECURIYGROUP1", "my security group", vpc_id, security_group_tags
        )

        security_group_tag_datas = []
        security_group_tag_datas.append(TagData("class", "webservices"))
        security_group_tag_datas.append(TagData("name", "mysecuritygroup"))

        security_group_data = SecurityGroupData()
        security_group_data.security_group_nm = "MYSECURIYGROUP2"
        security_group_data.description = "my security group"
        security_group_data.vpc_id = vpc_id
        security_group_data.tags = security_group_tag_datas

        # run the test
        self.security_group_dao.create(security_group_data)

        response = self.test_utils.describe_security_groups("mysecuritygroup")

        assert len(response) == 2

    @mock_aws
    def test_create_security_group_twice_same_name(self):
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
            self.test_utils.build_tag("name", "mysecuritygroup1")
        )

        self.test_utils.create_security_group(
            "MYSECURITYGROUP", "my security group", vpc_id, security_group_tags
        )

        security_group_tag_datas = []
        security_group_tag_datas.append(TagData("class", "webservices"))
        security_group_tag_datas.append(TagData("name", "mysecuritygroup2"))

        security_group_data = SecurityGroupData()
        security_group_data.security_group_nm = "MYSECURITYGROUP"
        security_group_data.description = "my security group"
        security_group_data.vpc_id = vpc_id
        security_group_data.tags = security_group_tag_datas

        try:
            # run the test
            self.security_group_dao.create(security_group_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the security group!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

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

        security_group_id = self.test_utils.create_security_group(
            "MYSECURITYGROUP", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        security_group_data = SecurityGroupData()
        security_group_data.security_group_id = security_group_id

        # run the test
        self.security_group_dao.delete(security_group_data)

        response = self.test_utils.describe_security_groups("mysecuritygroup")

        assert len(response) == 0

    @mock_aws
    def test_delete_not_existing_security_group(self):
        security_group_data = SecurityGroupData()
        security_group_data.security_group_id = "1234"

        try:
            # run the test
            self.security_group_dao.delete(security_group_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the security group!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_security_group(self):
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
            "MYSECURITYGROUP", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        # run the test
        security_group_data = self.security_group_dao.load(security_group_id)

        assert security_group_data.security_group_id == security_group_id
        assert security_group_data.security_group_nm == "MYSECURITYGROUP"
        assert security_group_data.description == "my security group"
        assert security_group_data.vpc_id == vpc_id

        assert len(security_group_data.tags) == 2
        assert security_group_data.get_tag_value("name") == "mysecuritygroup"
        assert security_group_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_security_group_not_found(self):
        try:
            self.security_group_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the security group!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_security_groups_by_tag_name(self):
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

        self.test_utils.create_security_group(
            "MYSECURITYGROUP1",
            "my security group1",
            vpc_id,
            security_group_tags1,
        )

        security_group_tags2 = []
        security_group_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags2.append(
            self.test_utils.build_tag("name", "mysecuritygroup2")
        )

        security_group_id2 = self.test_utils.create_security_group(
            "MYSECURITYGROUP2",
            "my security group2",
            vpc_id,
            security_group_tags2,
        ).get("GroupId")

        # run the test
        security_group_datas = self.security_group_dao.load_all(
            "mysecuritygroup2"
        )

        assert len(security_group_datas) == 1

        assert security_group_datas[0].security_group_id == security_group_id2
        assert security_group_datas[0].security_group_nm == "MYSECURITYGROUP2"
        assert security_group_datas[0].description == "my security group2"
        assert security_group_datas[0].vpc_id == vpc_id

        assert len(security_group_datas[0].tags) == 2
        assert (
            security_group_datas[0].get_tag_value("name") == "mysecuritygroup2"
        )
        assert security_group_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_security_groups_by_tag_name_more_found(self):
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

        security_group_id1 = self.test_utils.create_security_group(
            "MYSECURITYGROUP1",
            "my security group1",
            vpc_id,
            security_group_tags,
        ).get("GroupId")

        security_group_id2 = self.test_utils.create_security_group(
            "MYSECURITYGROUP2",
            "my security group2",
            vpc_id,
            security_group_tags,
        ).get("GroupId")

        # run the test
        security_group_datas = self.security_group_dao.load_all(
            "mysecuritygroup"
        )

        assert len(security_group_datas) == 2

        assert security_group_datas[0].security_group_id == security_group_id1
        assert security_group_datas[1].security_group_id == security_group_id2

    @mock_aws
    def test_load_all_security_groups_by_tag_name_not_found(self):
        # run the test
        security_group_datas = self.security_group_dao.load_all(
            "mysecuritygroup"
        )

        assert len(security_group_datas) == 0
