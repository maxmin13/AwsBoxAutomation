"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.image import ImageData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.image import ImageDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils
from comtest.maxmin.aws.constants import AMI_ID


class ImageDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.image_dao = ImageDao()

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

        instance_id = self.test_utils.create_instance(
            AMI_ID,
            security_group_id,
            subnet_id,
            "10.0.10.10",
            "ENCODED CLOUD INIT DATA",
            instance_tags,
        ).get("InstanceId")

        image_tag_datas = []
        image_tag_datas.append(TagData("class", "webservices"))
        image_tag_datas.append(TagData("name", "myimage"))

        image_data = ImageData()

        image_data.image_nm = "MYIMAGENM"
        image_data.description = "My test image"
        image_data.instance_id = instance_id
        image_data.tags = image_tag_datas

        # run the test
        self.image_dao.create(image_data)

        images = self.test_utils.describe_images("myimage")

        assert images[0].get("ImageId")
        assert images[0].get("Name") == "MYIMAGENM"
        assert images[0].get("Description") == "My test image"
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
    def test_create_image_twice_same_tag_name(self):
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

        image_tag_datas = []
        image_tag_datas.append(TagData("class", "webservices"))
        image_tag_datas.append(TagData("name", "myimage"))

        image_data = ImageData()

        image_data.image_nm = "MYIMAGENM2"
        image_data.description = "my test image"
        image_data.instance_id = instance_id
        image_data.tags = image_tag_datas

        # run the test
        self.image_dao.create(image_data)

        images = self.test_utils.describe_images("myimage")

        assert len(images) == 2

    @mock_aws
    def test_create_image_twice_same_name(self):
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
        image_tags.append(self.test_utils.build_tag("name", "myimage1"))

        self.test_utils.create_image(
            "MYIMAGENM", instance_id, "my test image", image_tags
        )

        image_tag_datas = []
        image_tag_datas.append(TagData("class", "webservices"))
        image_tag_datas.append(TagData("name", "myimage2"))

        image_data = ImageData()

        image_data.image_nm = "MYIMAGENM"
        image_data.description = "my test image"
        image_data.instance_id = instance_id
        image_data.tags = image_tag_datas

        # run the test
        self.image_dao.create(image_data)

        images1 = self.test_utils.describe_images("myimage1")

        assert len(images1) == 1
        assert images1[0].get("Name") == "MYIMAGENM"
        assert (
            self.test_utils.get_tag_value("name", images1[0].get("Tags"))
            == "myimage1"
        )

        images2 = self.test_utils.describe_images("myimage2")

        assert len(images2) == 1
        assert images2[0].get("Name") == "MYIMAGENM"
        assert (
            self.test_utils.get_tag_value("name", images2[0].get("Tags"))
            == "myimage2"
        )

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

        image_id = self.test_utils.create_image(
            "MYIMAGENM", instance_id, "my test image", image_tags
        ).get("ImageId")

        image_data = ImageData()
        image_data.image_id = image_id

        # run the test
        self.image_dao.delete(image_data)

        images = self.test_utils.describe_images("myimage")

        assert len(images) == 0

    @mock_aws
    def test_delete_not_existing_image(self):
        image_data = ImageData()
        image_data.image_id = "1234"

        try:
            # run the test
            self.image_dao.delete(image_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the image!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_image(self):
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
            "MYIMAGENM1", instance_id, "my test image 1", image_tags1
        ).get("ImageId")
        image1 = self.test_utils.describe_image(image_id1)
        snapshot_id1 = (
            image1.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image 2", image_tags2
        )

        # run the test
        image_data = self.image_dao.load(image_id1)

        assert image_data.image_id == image_id1
        assert image_data.image_nm == "MYIMAGENM1"
        assert image_data.state == "available"
        assert image_data.description == "my test image 1"
        assert image_data.snapshot_ids[0] == snapshot_id1

        assert len(image_data.tags) == 2
        assert image_data.get_tag_value("name") == "myimage1"
        assert image_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_images_by_name(self):
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

        self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image 1", image_tags1
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        image_id2 = self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image 2", image_tags2
        ).get("ImageId")
        image2 = self.test_utils.describe_image(image_id2)
        snapshot_id2 = (
            image2.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        # run the test
        image_datas = self.image_dao.load_by_name("MYIMAGENM2")

        assert len(image_datas) == 1

        assert image_datas[0].image_id == image_id2
        assert image_datas[0].image_nm == "MYIMAGENM2"
        assert image_datas[0].state == "available"
        assert image_datas[0].description == "my test image 2"
        assert image_datas[0].snapshot_ids[0] == snapshot_id2

        assert len(image_datas[0].tags) == 2
        assert image_datas[0].get_tag_value("name") == "myimage2"
        assert image_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_images_by_name_more_found(self):
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
            "MYIMAGENM", instance_id, "my test image 1", image_tags1
        ).get("ImageId")
        image1 = self.test_utils.describe_image(image_id1)
        snapshot_id1 = (
            image1.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        image_id2 = self.test_utils.create_image(
            "MYIMAGENM", instance_id, "my test image 2", image_tags2
        ).get("ImageId")
        image2 = self.test_utils.describe_image(image_id2)
        snapshot_id2 = (
            image2.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        # run the test
        image_datas = self.image_dao.load_by_name("MYIMAGENM")

        assert len(image_datas) == 2

        assert image_datas[0].image_id == image_id1
        assert image_datas[0].image_nm == "MYIMAGENM"
        assert image_datas[0].state == "available"
        assert image_datas[0].description == "my test image 1"
        assert image_datas[0].snapshot_ids[0] == snapshot_id1

        assert len(image_datas[0].tags) == 2
        assert image_datas[0].get_tag_value("name") == "myimage1"
        assert image_datas[0].get_tag_value("class") == "webservices"

        assert image_datas[1].image_id == image_id2
        assert image_datas[1].image_nm == "MYIMAGENM"
        assert image_datas[1].state == "available"
        assert image_datas[1].description == "my test image 2"
        assert image_datas[1].snapshot_ids[0] == snapshot_id2

        assert len(image_datas[1].tags) == 2
        assert image_datas[1].get_tag_value("name") == "myimage2"
        assert image_datas[1].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_images_by_name_not_found(self):
        image_datas = self.image_dao.load_by_name("MYIMAGENM")

        assert len(image_datas) == 0

    @mock_aws
    def test_load_all_images_by_tag_name(self):
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

        self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image 1", image_tags1
        )

        image_tags2 = []
        image_tags2.append(self.test_utils.build_tag("class", "webservices"))
        image_tags2.append(self.test_utils.build_tag("name", "myimage2"))

        image_id2 = self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image 2", image_tags2
        ).get("ImageId")
        image2 = self.test_utils.describe_image(image_id2)
        snapshot_id2 = (
            image2.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        # run the test
        image_datas = self.image_dao.load_all("myimage2")

        assert len(image_datas) == 1

        assert image_datas[0].image_id == image_id2
        assert image_datas[0].image_nm == "MYIMAGENM2"
        assert image_datas[0].state == "available"
        assert image_datas[0].description == "my test image 2"
        assert image_datas[0].snapshot_ids[0] == snapshot_id2

        assert len(image_datas[0].tags) == 2
        assert image_datas[0].get_tag_value("name") == "myimage2"
        assert image_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_images_by_tag_name_more_found(self):
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

        image_id1 = self.test_utils.create_image(
            "MYIMAGENM1", instance_id, "my test image 1", image_tags
        ).get("ImageId")
        image1 = self.test_utils.describe_image(image_id1)
        snapshot_id1 = (
            image1.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        image_id2 = self.test_utils.create_image(
            "MYIMAGENM2", instance_id, "my test image 2", image_tags
        ).get("ImageId")
        image2 = self.test_utils.describe_image(image_id2)
        snapshot_id2 = (
            image2.get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
        )

        # run the test
        image_datas = self.image_dao.load_all("myimage")

        assert len(image_datas) == 2

        assert image_datas[0].image_id == image_id1
        assert image_datas[0].image_nm == "MYIMAGENM1"
        assert image_datas[0].state == "available"
        assert image_datas[0].description == "my test image 1"
        assert image_datas[0].snapshot_ids[0] == snapshot_id1

        assert len(image_datas[0].tags) == 2
        assert image_datas[0].get_tag_value("name") == "myimage"
        assert image_datas[0].get_tag_value("class") == "webservices"

        assert image_datas[1].image_id == image_id2
        assert image_datas[1].image_nm == "MYIMAGENM2"
        assert image_datas[1].state == "available"
        assert image_datas[1].description == "my test image 2"
        assert image_datas[1].snapshot_ids[0] == snapshot_id2

        assert len(image_datas[1].tags) == 2
        assert image_datas[1].get_tag_value("name") == "myimage"
        assert image_datas[1].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_images_by_tag_name_not_found(self):
        image_datas = self.image_dao.load_all("myimage")

        assert len(image_datas) == 0
