"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.instance import InstanceService
from comtest.maxmin.aws.constants import AMI_NAME, AMI_ID


class InstanceServiceServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.instance_service = InstanceService()

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

        self.test_utils.create_security_group(
            "MYSECURIYGROUP", "my security group", vpc_id, security_group_tags
        )

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

        instance_tags = []
        instance_tags.append(Tag("class", "webservices"))

        # run the test
        self.instance_service.create_instance(
            "myinstance",
            "10.0.10.10",
            AMI_NAME,
            "mysecuritygroup",
            "mysubnet",
            "myvpc",
            "myuser",
            "myuserpwd",
            "test.maxmin.it",
            "mykeypair",
            instance_tags,
        )

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
            "MYSECURIYGROUP", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

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

        instance_tags = []
        instance_tags.append(Tag("class", "webservices"))

        try:
            # run the test
            self.instance_service.create_instance(
                "myinstance",
                "10.0.10.10",
                AMI_NAME,
                "mysecuritygroup",
                "mysubnet",
                "myvpc",
                "myuser",
                "myuserpwd",
                "test.maxmin.it",
                "mykeypair",
                instance_tags,
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Instance already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    """
    the test doesn't work with moto library, after an instance is deleted, it disappears and it is not found in 'terminated' state.

    @mock_aws
    def test_create_instance_twice_terminated(self):

        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get("VpcId")

        subnet_tags = []
        subnet_tags.append(self.test_utils.build_tag("class", "webservices"))
        subnet_tags.append(self.test_utils.build_tag("name", "mysubnet"))

        subnet_id = self.test_utils.create_subnet("eu-west-1a", "10.0.10.0/25", vpc_id, subnet_tags).get("SubnetId")

        security_group_tags = []
        security_group_tags.append(self.test_utils.build_tag("class", "webservices"))
        security_group_tags.append(self.test_utils.build_tag("name", "mysecuritygroup"))

        security_group_id = self.test_utils.create_security_group("MYSECURIYGROUP", "my security group", vpc_id, security_group_tags).get("GroupId")

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

        instance_tags = []
        instance_tags.append(self.test_utils.build_tag("class", "webservices"))
        instance_tags.append(self.test_utils.build_tag("name", "myinstance"))

        instance_id = self.test_utils.create_instance(AMI_ID, security_group_id, subnet_id, "10.0.10.10", "ENCODED CLOUD INIT DATA", instance_tags).get("InstanceId")
        self.test_utils.terminate_instance(instance_id)

        instance_tags = []
        instance_tags.append(Tag("class", "webservices"))

        # run the test
        self.instance_service.create_instance("myinstance", "10.0.10.10", AMI_NAME, "mysecuritygroup", "mysubnet", "myvpc",
                                              "myuser", "myuserpwd", "test.maxmin.it", "mykeypair", instance_tags)


        instances = self.test_utils.describe_instances("myinstance")

        assert len(instances) == 2
        assert instances[0].get("State").get("Name") == "terminated"
        assert instances[1].get("State").get("Name") == "running"
    """

    @mock_aws
    def test_terminate_instance(self):
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

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

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

        # run the test
        self.instance_service.terminate_instance("myinstance")

        instances = self.test_utils.describe_instances("myinstance")

        assert len(instances) == 1
        assert instances[0].get("State").get("Name") == "terminated"

    @mock_aws
    def test_delete_not_existing_instance(self):
        self.instance_service.terminate_instance("myinstance")

        # no error expected
        pass

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
            "MYSECURIYGROUP", "my security group", vpc_id, security_group_tags
        ).get("GroupId")

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

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
        instance_tags2.append(self.test_utils.build_tag("name", "myinstance2"))

        self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.20",
            "ENCODED CLOUD INIT DATA",
            instance_tags2,
        )

        # run the test
        instance = self.instance_service.load_instance("myinstance1")

        assert instance.instance_id == instance_id1
        assert instance.state == "running"
        assert instance.az == "eu-west-1a"
        assert instance.private_ip == "10.0.10.10"
        assert instance.public_ip
        assert instance.instance_profile is None
        assert instance.subnet_id == subnet_id
        assert instance.image_id == AMI_ID
        assert instance.vpc_id == vpc_id
        assert instance.security_group_ids[0] == security_group_id
        assert instance.cloud_init_data is None

        assert len(instance.tags) == 2
        assert instance.get_tag_value("name") == "myinstance1"
        assert instance.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_instance_more_found(self):
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

        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIRNM", key_pair_tags, None)

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

        self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.20",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        )

        try:
            # run the test
            self.instance_service.load_instance("myinstance")

            fail("ERROR: an exception should have been thrown!")

        except AwsServiceException as e:
            assert str(e) == "Found more than one instance!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_instance_not_found(self):
        instance = self.instance_service.load_instance("myinstance")

        assert not instance
