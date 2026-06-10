"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.internet_gateway import InternetGatewayService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils


class InternetGatewayServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.internet_gateway_service = InternetGatewayService()

    @mock_aws
    def test_create_internet_gateway(self):
        vpc_tags = []
        vpc_tags.append(self.test_utils.build_tag("class", "webservices"))
        vpc_tags.append(self.test_utils.build_tag("name", "myvpc"))

        vpc_id = self.test_utils.create_vpc("10.0.10.0/16", vpc_tags).get(
            "VpcId"
        )

        internet_gateway_tags = []
        internet_gateway_tags.append(Tag("class", "webservices"))

        # run the test
        self.internet_gateway_service.create_internet_gateway(
            "myinternetgateway", "myvpc", internet_gateway_tags
        )

        internet_gateways = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert internet_gateways[0].get("InternetGatewayId")
        assert len(internet_gateways[0].get("Attachments")) == 1
        assert (
            internet_gateways[0].get("Attachments")[0].get("VpcId") == vpc_id
        )

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

        internet_gateway_tags = []
        internet_gateway_tags.append(Tag("class", "webservices"))

        try:
            self.internet_gateway_service.create_internet_gateway(
                "myinternetgateway", "myvpc", internet_gateway_tags
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Internet gateway already created!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_internet_gateway(self):
        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        self.test_utils.create_internet_gateway(internet_gateway_tags)

        # run the test
        self.internet_gateway_service.delete_internet_gateway(
            "myinternetgateway"
        )

        internet_gateways = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert len(internet_gateways) == 0

    @mock_aws
    def test_delete_internet_gateway_attached(self):
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

        # run the test
        self.internet_gateway_service.delete_internet_gateway(
            "myinternetgateway"
        )

        internet_gateways = self.test_utils.describe_internet_gateways(
            "myinternetgateway"
        )

        assert len(internet_gateways) == 0

    @mock_aws
    def test_delete_not_existing_internet_gateway(self):
        self.internet_gateway_service.delete_internet_gateway(
            "myinternetgateway"
        )

        # no error expected
        pass

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

        internet_gateway_tag2 = []
        internet_gateway_tag2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tag2.append(
            self.test_utils.build_tag("name", "myinternetgateway2")
        )

        internet_gateway_id2 = self.test_utils.create_internet_gateway(
            internet_gateway_tag2
        ).get("InternetGatewayId")
        self.test_utils.attach_internet_gateway_to_vpc(
            internet_gateway_id2, vpc_id
        )

        # run the test
        internet_gateway = self.internet_gateway_service.load_internet_gateway(
            "myinternetgateway1"
        )

        assert internet_gateway.internet_gateway_id == internet_gateway_id1
        assert len(internet_gateway.attached_vpc_ids) == 1
        assert internet_gateway.attached_vpc_ids[0] == vpc_id

        assert len(internet_gateway.tags) == 2
        assert internet_gateway.get_tag_value("name") == "myinternetgateway1"
        assert internet_gateway.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_internet_gateway_more_found(self):
        internet_gateway_tags = []
        internet_gateway_tags.append(
            self.test_utils.build_tag("class", "webservices")
        )
        internet_gateway_tags.append(
            self.test_utils.build_tag("name", "myinternetgateway")
        )

        self.test_utils.create_internet_gateway(internet_gateway_tags)

        self.test_utils.create_internet_gateway(internet_gateway_tags)

        try:
            # run the test
            self.internet_gateway_service.load_internet_gateway(
                "myinternetgateway"
            )

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one Internet gateway!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_internet_gateway_not_found(self):
        internet_gateway = self.internet_gateway_service.load_internet_gateway(
            "myinternetgateway"
        )

        assert not internet_gateway
