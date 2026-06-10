"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.instance import InstanceData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.instance import InstanceDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils
from comtest.maxmin.aws.constants import AMI_ID


class InstanceDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.instance_dao = InstanceDao()

    @mock_aws
    def test_create_instance(self):
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

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "MYSECURIYGROUP", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        instance_tag_datas = []
        instance_tag_datas.append(TagData("class", "webservices"))
        instance_tag_datas.append(TagData("name", "myinstance"))

        instance_data = InstanceData()

        instance_data.image_id = AMI_ID
        instance_data.security_group_ids.append(security_group_id)
        instance_data.subnet_id = subnet_id
        instance_data.private_ip = "10.0.10.10"
        instance_data.cloud_init_data = "ENCODED CLOUD INIT DATA"
        instance_data.tags = instance_tag_datas

        # run the test
        self.instance_dao.create(instance_data)

        instances = self.test_utils.describe_instances("myinstance")

        assert instances[0].get("VpcId") == vpc_id
        assert instances[0].get("PrivateIpAddress") == "10.0.10.10"
        assert instances[0].get("State").get("Name") == "running"
        assert instances[0].get("SubnetId") == subnet_id
        assert (
            instances[0].get("Placement").get("AvailabilityZone")
            == "eu-west-1a"
        )
        assert (
            instances[0]
            .get("NetworkInterfaces")[0]
            .get("Groups")[0]
            .get("GroupName")
            == "MYSECURIYGROUP"
        )

        assert len(instances[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", instances[0].get("Tags"))
            == "myinstance"
        )
        assert (
            self.test_utils.get_tag_value("class", instances[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_instance_twice(self):
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

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "MYSECURIYGROUP1", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        instance_tags = []
        instance_tags.append(self.test_utils.build_tag("class", "webservices"))
        instance_tags.append(self.test_utils.build_tag("name", "myinstance"))

        self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        )

        instance_tag_datas = []
        instance_tag_datas.append(TagData("class", "webservices"))
        instance_tag_datas.append(TagData("name", "myinstance"))

        instance_data = InstanceData()

        instance_data.image_id = AMI_ID
        instance_data.security_group_ids.append(security_group_id)
        instance_data.subnet_id = subnet_id
        instance_data.private_ip = "10.0.10.20"
        instance_data.cloud_init_data = "ENCODED CLOUD INIT DATA"
        instance_data.tags = instance_tag_datas

        # run the test
        self.instance_dao.create(instance_data)

        instances = self.test_utils.describe_instances("myinstance")

        assert len(instances) == 2

    @mock_aws
    def test_delete_instance(self):
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

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "MYSECURIYGROUP1", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        instance_tags = []
        instance_tags.append(self.test_utils.build_tag("class", "webservices"))
        instance_tags.append(self.test_utils.build_tag("name", "myinstance"))

        instance_id = self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        ).get("InstanceId")

        instance_tag_datas = []
        instance_tag_datas.append(TagData("class", "webservices"))
        instance_tag_datas.append(TagData("name", "myinstance"))

        instance_data = InstanceData()
        instance_data.instance_id = instance_id

        # run the test
        self.instance_dao.delete(instance_data)

        response = self.test_utils.describe_instances("myinstance")

        assert len(response) == 1

        assert response[0].get("State").get("Name") == "terminated"

    @mock_aws
    def test_delete_not_existing_instance(self):
        instance_data = InstanceData()
        instance_data.instance_id = "1234"

        try:
            self.instance_dao.delete(instance_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the instance!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_instance(self):
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

        security_group_tags = []
        security_group_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags.append(
            self.test_utils.build_tag("name", "mysecuritygroup")
        )

        security_group_id = self.test_utils.create_security_group(
            "MYSECURIYGROUP1", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        instance_tags1 = []
        instance_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        instance_tags1.append(self.test_utils.build_tag("name", "myinstance1"))

        instance_id1 = self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags1,
        ).get("InstanceId")

        instance_tags2 = []
        instance_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        instance_tags2.append(self.test_utils.build_tag("name", "myinstance1"))

        self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.30",
            "ENCODED CLOUD INIT DATA",
            instance_tags2,
        )

        # run the test
        instance_data = self.instance_dao.load(instance_id1)

        assert instance_data.instance_id == instance_id1
        assert instance_data.state == "running"
        assert instance_data.az == "eu-west-1a"
        assert instance_data.private_ip == "10.0.10.10"
        assert instance_data.public_ip
        assert instance_data.instance_profile is None
        assert instance_data.subnet_id == subnet_id
        assert instance_data.image_id == AMI_ID
        assert instance_data.vpc_id == vpc_id
        assert instance_data.security_group_ids[0] == security_group_id
        assert instance_data.cloud_init_data is None

        assert len(instance_data.tags) == 2
        assert instance_data.get_tag_value("name") == "myinstance1"
        assert instance_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_instance_not_found(self):
        try:
            self.instance_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the instance!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_instances_by_tag_name(self):
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

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.128/25", vpc_id, subnet_tags2
        ).get("SubnetId")

        security_group_tags1 = []
        security_group_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags1.append(
            self.test_utils.build_tag("name", "mysecuritygroup1")
        )

        security_group_id1 = self.test_utils.create_security_group(
            "MYSECURIYGROUP1",
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

        security_group_id2 = self.test_utils.create_security_group(
            "MYSECURIYGROUP2",
            "my security group",
            vpc_id,
            security_group_tags2,
        ).get("GroupId")

        instance_tags1 = []
        instance_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        instance_tags1.append(self.test_utils.build_tag("name", "myinstance1"))

        instance_id1 = self.test_utils.create_instance(
            AMI_ID,
            security_group_id1,
            subnet_id1,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags1,
        ).get("InstanceId")

        instance_tags2 = []
        instance_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        instance_tags2.append(self.test_utils.build_tag("name", "myinstance2"))

        self.test_utils.create_instance(
            AMI_ID,
            security_group_id2,
            subnet_id2,
            "10.0.10.130",
            "ENCODED CLOUD INIT DATA",
            instance_tags2,
        )

        # run the test
        instance_datas = self.instance_dao.load_all("myinstance1")

        assert len(instance_datas) == 1

        assert instance_datas[0].instance_id == instance_id1
        assert instance_datas[0].state == "running"
        assert instance_datas[0].az == "eu-west-1a"
        assert instance_datas[0].private_ip == "10.0.10.10"
        assert instance_datas[0].public_ip
        assert instance_datas[0].instance_profile is None
        assert instance_datas[0].subnet_id == subnet_id1
        assert instance_datas[0].image_id == AMI_ID
        assert instance_datas[0].vpc_id == vpc_id
        assert instance_datas[0].security_group_ids[0] == security_group_id1
        assert instance_datas[0].cloud_init_data is None

        assert len(instance_datas[0].tags) == 2
        assert instance_datas[0].get_tag_value("name") == "myinstance1"
        assert instance_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_instances_by_tag_name_more_found(self):
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

        subnet_id2 = self.test_utils.create_subnet(
            "eu-west-1a", "10.0.10.128/25", vpc_id, subnet_tags2
        ).get("SubnetId")

        security_group_tags1 = []
        security_group_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        security_group_tags1.append(
            self.test_utils.build_tag("name", "mysecuritygroup1")
        )

        security_group_id1 = self.test_utils.create_security_group(
            "MYSECURIYGROUP1",
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

        security_group_id2 = self.test_utils.create_security_group(
            "MYSECURIYGROUP2",
            "my security group",
            vpc_id,
            security_group_tags2,
        ).get("GroupId")

        instance_tags = []
        instance_tags.append(self.test_utils.build_tag("class", "webservices"))
        instance_tags.append(self.test_utils.build_tag("name", "myinstance"))

        instance_id1 = self.test_utils.create_instance(
            AMI_ID,
            security_group_id1,
            subnet_id1,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        ).get("InstanceId")

        instance_id2 = self.test_utils.create_instance(
            AMI_ID,
            security_group_id2,
            subnet_id2,
            "10.0.10.130",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        ).get("InstanceId")

        # run the test
        instance_datas = self.instance_dao.load_all("myinstance")

        assert len(instance_datas) == 2

        assert instance_datas[0].instance_id == instance_id1
        assert instance_datas[0].state == "running"
        assert instance_datas[0].az == "eu-west-1a"
        assert instance_datas[0].private_ip == "10.0.10.10"
        assert instance_datas[0].public_ip
        assert instance_datas[0].instance_profile is None
        assert instance_datas[0].subnet_id == subnet_id1
        assert instance_datas[0].image_id == AMI_ID
        assert instance_datas[0].vpc_id == vpc_id
        assert instance_datas[0].security_group_ids[0] == security_group_id1
        assert instance_datas[0].cloud_init_data is None

        assert len(instance_datas[0].tags) == 2
        assert instance_datas[0].get_tag_value("name") == "myinstance"
        assert instance_datas[0].get_tag_value("class") == "webservices"

        assert instance_datas[1].instance_id == instance_id2
        assert instance_datas[1].state == "running"
        assert instance_datas[1].az == "eu-west-1a"
        assert instance_datas[1].private_ip == "10.0.10.130"
        assert instance_datas[1].public_ip
        assert instance_datas[1].instance_profile is None
        assert instance_datas[1].subnet_id == subnet_id2
        assert instance_datas[1].image_id == AMI_ID
        assert instance_datas[1].vpc_id == vpc_id
        assert instance_datas[1].security_group_ids[0] == security_group_id2
        assert instance_datas[1].cloud_init_data is None

        assert len(instance_datas[1].tags) == 2
        assert instance_datas[1].get_tag_value("name") == "myinstance"
        assert instance_datas[1].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_instances_by_tag_name_not_found(self):
        # run the test
        instance_datas = self.instance_dao.load_all("myinstance")

        assert len(instance_datas) == 0
