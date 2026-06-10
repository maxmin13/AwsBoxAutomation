"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.dao.domain.internet_gateway import InternetGatewayData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.internet_gateway import InternetGatewayDao
from com.maxmin.aws.exception import AwsDaoException
from comtest.maxmin.aws.utils import TestUtils


class InternetGatewayDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.internet_gateway_dao = InternetGatewayDao()

    @mock_aws
    def test_create_internet_gateway(self):
        internet_gateway_tag_datas = []
        internet_gateway_tag_datas.append(TagData("class", "webservices"))
        internet_gateway_tag_datas.append(TagData("name", "myinternetgateway"))

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.tags = internet_gateway_tag_datas

        # run the test
        self.internet_gateway_dao.create(internet_gateway_data)

        internet_gateways = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert internet_gateways[0].get("InternetGatewayId")
        assert len(internet_gateways[0].get("Attachments")) == 0

        assert len(internet_gateways[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value(
                "name", internet_gateways[0].get("Tags")
            )
            == "myinternetgateway"
        )
        assert (
            self.test_utils.get_tag_value(
                "class", internet_gateways[0].get("Tags")
            )
            == "webservices"
        )

    @mock_aws
    def test_create_internet_gateway_twice(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        self.test_utils.create_vpc("10.0.10.0/16", vpc_tags)

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        self.test_utils.create_internet_gateway(internet_gateway_tags)

        internet_gateway_tag_datas = []
        internet_gateway_tag_datas.append(TagData("class", "webservices"))
        internet_gateway_tag_datas.append(TagData("name", "myinternetgateway"))

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.tags = internet_gateway_tag_datas

        # run the test
        self.internet_gateway_dao.create(internet_gateway_data)

        response = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert len(response) == 2

    @mock_aws
    def test_delete_internet_gateway(self):
        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.internet_gateway_id = internet_gateway_id

        # run the test
        self.internet_gateway_dao.delete(internet_gateway_data)

        response = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert len(response) == 0

    @mock_aws
    def test_delete_internet_gateway_attached_to_vpc(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id, vpc_id
        )

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.internet_gateway_id = internet_gateway_id

        try:
            self.internet_gateway_dao.delete(internet_gateway_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the Internet gateway!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_delete_not_existing_internet_gateway(self):
        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.internet_gateway_id = "1234"

        try:
            self.internet_gateway_dao.delete(internet_gateway_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the Internet gateway!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_internet_gateway(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        internet_gateway_tags1 = []
        internet_gateway_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags1.append(
            self.test_utils.build_tag("name", "myinternetgateway1")
        )

        internet_gateway_id1 = self.test_utils.create_internet_gateway(
            internet_gateway_tags1
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id1, vpc_id
        )

        internet_gateway_tags2 = []
        internet_gateway_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags2.append(
            self.test_utils.build_tag("name", "myinternetgateway2")
        )

        internet_gateway_id2 = self.test_utils.create_internet_gateway(
            internet_gateway_tags2
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id2, vpc_id
        )

        # run the test
        internet_gateway_data = self.internet_gateway_dao.load(
            internet_gateway_id1
        )

        assert (
            internet_gateway_data.internet_gateway_id == internet_gateway_id1
        )
        assert len(internet_gateway_data.attached_vpc_ids) == 1
        assert internet_gateway_data.attached_vpc_ids[0] == vpc_id

        assert len(internet_gateway_data.tags) == 2
        assert (
            internet_gateway_data.get_tag_value("name") == "myinternetgateway1"
        )
        assert internet_gateway_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_internet_gateway_not_found(self):
        try:
            self.internet_gateway_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the Internet gateway!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_internet_gateways_by_tag_name(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        vpc_id2 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags2).get(
            "VpcId"
        )

        internet_gateway_tags1 = []
        internet_gateway_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags1.append(
            self.test_utils.build_tag("name", "myinternetgateway1")
        )

        internet_gateway_id1 = self.test_utils.create_internet_gateway(
            internet_gateway_tags1
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id1, vpc_id1
        )

        internet_gateway_tags2 = []
        internet_gateway_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags2.append(
            self.test_utils.build_tag("name", "myinternetgateway2")
        )

        internet_gateway_id2 = self.test_utils.create_internet_gateway(
            internet_gateway_tags2
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id2, vpc_id2
        )

        # run the test
        internet_gateway_datas = self.internet_gateway_dao.load_all(
            "myinternetgateway2"
        )

        assert len(internet_gateway_datas) == 1

        assert (
            internet_gateway_datas[0].internet_gateway_id
            == internet_gateway_id2
        )
        assert len(internet_gateway_datas[0].attached_vpc_ids) == 1
        assert internet_gateway_datas[0].attached_vpc_ids[0] == vpc_id2

        assert len(internet_gateway_datas[0].tags) == 2
        assert (
            internet_gateway_datas[0].get_tag_value("name")
            == "myinternetgateway2"
        )
        assert (
            internet_gateway_datas[0].get_tag_value("class") == "webservices"
        )

    @mock_aws
    def test_load_all_internet_gateways_by_tag_name_more_found(self):
        vpc_tags1 = []
        vpc_tags1.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags1.append(self.test_utils.build_tag("name", "myvpc1"))

        vpc_id1 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags1).get(
            "VpcId"
        )

        vpc_tags2 = []
        vpc_tags2.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags2.append(self.test_utils.build_tag("name", "myvpc2"))

        vpc_id2 = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags2).get(
            "VpcId"
        )

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id1 = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id1, vpc_id1
        )

        internet_gateway_id2 = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id2, vpc_id2
        )

        # run the test
        internet_gateway_datas = self.internet_gateway_dao.load_all(
            "myinternetgateway"
        )

        assert len(internet_gateway_datas) == 2

        assert (
            internet_gateway_datas[0].internet_gateway_id
            == internet_gateway_id1
        )
        assert (
            internet_gateway_datas[1].internet_gateway_id
            == internet_gateway_id2
        )

    @mock_aws
    def test_load_all_internet_gateways_by_tag_name_not_found(self):
        # run the test
        internet_gateway_datas = self.internet_gateway_dao.load_all(
            "myinternetgateway"
        )

        assert len(internet_gateway_datas) == 0

    @mock_aws
    def test_attach_internet_gateway(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.internet_gateway_id = internet_gateway_id
        internet_gateway_data.attached_vpc_ids.append(vpc_id)

        # run the test
        self.internet_gateway_dao.attach(internet_gateway_data)

        response = self.test_utils.describe_internet_gateway(
            internet_gateway_id
        )

        assert response.get("InternetGatewayId") == internet_gateway_id
        assert len(response.get("Attachments")) == 1
        assert response.get("Attachments")[0].get("VpcId") == vpc_id

    @mock_aws
    def test_detach_internet_gateway(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        internet_gateway_id = self.test_utils.create_internet_gateway(
            internet_gateway_tags
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id, vpc_id
        )

        internet_gateway_data = InternetGatewayData()
        internet_gateway_data.internet_gateway_id = internet_gateway_id
        internet_gateway_data.attached_vpc_ids.append(vpc_id)

        # run the test
        self.internet_gateway_dao.detach(internet_gateway_data)

        response = self.test_utils.describe_internet_gateway(
            internet_gateway_id
        )

        assert response.get("InternetGatewayId") == internet_gateway_id
        assert len(response.get("Attachments")) == 0
