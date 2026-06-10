"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils
from com.maxmin.aws.ec2.service.image import ImageService
from comtest.maxmin.aws.constants import AMI_ID


class ImageServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.image_service = ImageService()

    @mock_aws
    def test_create_image(self):
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

        image_tags = []
        image_tags.append(Tag("class", "webservices"))

        # run the test
        self.image_service.create_image(
            "myimage", "my test image", "myinstance", image_tags
        )

        images = self.test_utils.describe_images("myimage")

        assert images[0].get("ImageId")
        assert images[0].get("Name") == "myimage"
        assert images[0].get("Description") == "my test image"
        assert images[0].get("State") == "available"
        assert (
            images[0]
            .get("BlockDeviceMappings")[0]
            .get("Ebs")
            .get("SnapshotId")
        )

        assert len(images[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", images[0].get("Tags"))
            == "myimage"
        )
        assert (
            self.test_utils.get_tag_value("class", images[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_image_twice(self):
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

        image_tags = []
        image_tags.append(self.test_utils.build_tag("class", "webservices"))
        image_tags.append(self.test_utils.build_tag("name", "myimage"))

        self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image", image_tags
        )

        image_tags = []
        image_tags.append(Tag("class", "webservices"))

        try:
            # run the test
            self.image_service.create_image(
                "myimage", "my test image", "myinstance", image_tags
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Image already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_image(self):
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

        image_tags = []
        image_tags.append(self.test_utils.build_tag("class", "webservices"))
        image_tags.append(self.test_utils.build_tag("name", "myimage"))

        self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image", image_tags
        )

        # run the test
        self.image_service.delete_image("myimage")

        images = self.test_utils.describe_images("myimage")

        assert len(images) == 0

    @mock_aws
    def test_delete_not_existing_image(self):
        self.image_service.delete_image("myimage")

        # no error expected
        pass

    @mock_aws
    def test_load_image_by_tag_name(self):
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

        image_tags1 = []
        image_tags1.append(self.test_utils.build_tag("class", "webservices"))
        image_tags1.append(self.test_utils.build_tag("name", "myimage1"))

        image_id1 = self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image1", image_tags1
        ).get("ImageId")
        description1 = self.test_utils.describe_image(image_id1)
        snapshot_id1 = (
            description1.get("BlockDeviceMappings")[0]
            .get("Ebs")
            .get("SnapshotId")
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image2", image_tags2
        )

        # run the test
        image = self.image_service.load_image("myimage1")

        assert image.image_id == image_id1
        assert image.state == "available"
        assert image.description == "my test image1"
        assert image.snapshot_ids[0] == snapshot_id1

        assert len(image.tags) == 2
        assert image.get_tag_value("name") == "myimage1"
        assert image.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_image_by_tag_name_more_found(self):
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

        image_tags = []
        image_tags.append(self.test_utils.build_tag("class", "webservices"))
        image_tags.append(self.test_utils.build_tag("name", "myimage"))

        self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image1", image_tags
        )

        self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image2", image_tags
        )

        try:
            # run the test
            self.image_service.load_image("myimage")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one image!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_image_by_tag_name_not_found(self):
        image = self.image_service.load_image("myimage")

        assert not image

    @mock_aws
    def test_load_image_by_name(self):
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

        image_tags1 = []
        image_tags1.append(self.test_utils.build_tag("class", "webservices"))
        image_tags1.append(self.test_utils.build_tag("name", "myimage1"))

        image_id1 = self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image1", image_tags1
        ).get("ImageId")
        description1 = self.test_utils.describe_image(image_id1)
        snapshot_id1 = (
            description1.get("BlockDeviceMappings")[0]
            .get("Ebs")
            .get("SnapshotId")
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image2", image_tags2
        )

        # run the test
        image = self.image_service.load_image_by_name("MYIMAGENM1")

        assert image.image_id == image_id1
        assert image.state == "available"
        assert image.description == "my test image1"
        assert image.snapshot_ids[0] == snapshot_id1

        assert len(image.tags) == 2
        assert image.get_tag_value("name") == "myimage1"
        assert image.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_image_by_name_more_found(self):
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

        image_tags = []
        image_tags.append(self.test_utils.build_tag("class", "webservices"))
        image_tags.append(self.test_utils.build_tag("name", "myimage"))

        self.test_utils.create_image(
            "MYIMAGENM", instance_id, "my test image1", image_tags
        )

        self.test_utils.create_image(
            "MYIMAGENM", instance_id, "my test image2", image_tags
        )

        try:
            # run the test
            self.image_service.load_image_by_name("MYIMAGENM")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one image!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_image_by_name_not_found(self):
        image = self.image_service.load_image_by_name("MYIMAGENM")

        assert not image
