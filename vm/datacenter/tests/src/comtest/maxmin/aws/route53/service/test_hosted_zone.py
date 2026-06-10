"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from com.maxmin.aws.route53.service.hosted_zone import HostedZoneService
from comtest.maxmin.aws.utils import TestUtils


class HostedZoneServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.hosted_zone_service = HostedZoneService()

    @mock_aws
    def test_create_record(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        # run the test
        self.hosted_zone_service.create_record(
            "test.maxmin.it", "10.0.10.10", "maxmin.it"
        )

        record = self.test_utils.describe_record(
            "test.maxmin.it", hosted_zone_id
        )

        assert record.get("Name") == "test.maxmin.it."
        assert record.get("ResourceRecords")[0].get("Value") == "10.0.10.10"

    @mock_aws
    def test_create_twice_record(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        self.test_utils.create_record(
            "test.maxmin.it.", "10.0.10.10", hosted_zone_id
        )

        # run the test
        self.hosted_zone_service.create_record(
            "test.maxmin.it", "10.0.10.10", "maxmin.it"
        )

        # no error expected

    @mock_aws
    def test_load_hosted_zone(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it").get(
            "Id"
        )
        self.test_utils.create_hosted_zone("maxmin.com")

        # run the test
        hosted_zone = self.hosted_zone_service.load_hosted_zone("maxmin.ie")

        assert not hosted_zone

        # run the test
        hosted_zone = self.hosted_zone_service.load_hosted_zone("maxmin.it")

        assert hosted_zone.hosted_zone_id == hosted_zone_id

        # run the test
        hosted_zone = self.hosted_zone_service.load_hosted_zone("maxmin.it.")

        assert hosted_zone.hosted_zone_id == hosted_zone_id

    @mock_aws
    def test_load_record(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it").get(
            "Id"
        )

        self.test_utils.create_record(
            "test.maxmin.it", "10.0.10.10", hosted_zone_id
        )

        self.test_utils.create_record(
            "sells.maxmin.it", "10.0.10.20", hosted_zone_id
        )

        # run the test
        record = self.hosted_zone_service.load_record(
            "sells.maxmin.it", "maxmin.it"
        )

        assert record.dns_nm == "sells.maxmin.it."
        assert record.ip_address == "10.0.10.20"

        # run the test
        record = self.hosted_zone_service.load_record(
            "test.maxmin.it.", "maxmin.it"
        )

        assert record.dns_nm == "test.maxmin.it."
        assert record.ip_address == "10.0.10.10"
