"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.route53.dao.domain.record import RecordData
from com.maxmin.aws.route53.dao.record import RecordDao
from comtest.maxmin.aws.utils import TestUtils


class RecordDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.record_dao = RecordDao()

    @mock_aws
    def test_load_all_records(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        self.test_utils.create_record(
            "test.maxmin.it.", "10.0.10.10", hosted_zone_id
        )

        record1 = self.test_utils.describe_record(
            "test.maxmin.it.", hosted_zone_id
        )

        self.test_utils.create_record(
            "sells.maxmin.it", "10.0.10.30", hosted_zone_id
        )

        record2 = self.test_utils.describe_record(
            "sells.maxmin.it.", hosted_zone_id
        )

        # run the test
        record_datas = self.record_dao.load_all(hosted_zone_id)

        assert record_datas[0].type == "NS"
        assert record_datas[0].dns_nm == "maxmin.it."
        assert record_datas[0].hosted_zone_id == hosted_zone_id

        assert record_datas[1].type == "SOA"
        assert record_datas[1].dns_nm == "maxmin.it."
        assert record_datas[1].hosted_zone_id == hosted_zone_id

        assert record_datas[2].type == "A"
        assert record_datas[2].dns_nm == "sells.maxmin.it."
        assert record_datas[2].hosted_zone_id == hosted_zone_id
        assert record_datas[2].ip_address == record2.get("ResourceRecords")[
            0
        ].get("Value")

        assert record_datas[3].type == "A"
        assert record_datas[3].dns_nm == "test.maxmin.it."
        assert record_datas[3].hosted_zone_id == hosted_zone_id
        assert record_datas[3].ip_address == record1.get("ResourceRecords")[
            0
        ].get("Value")

    @mock_aws
    def test_create_record(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        record_data = RecordData
        record_data.dns_nm = "test.maxmin.it"
        record_data.ip_address = "10.0.10.10"
        record_data.hosted_zone_id = hosted_zone_id

        # run the test
        self.record_dao.create(record_data)

        record = self.test_utils.describe_record(
            "test.maxmin.it", hosted_zone_id
        )

        assert record.get("Name") == "test.maxmin.it."
        assert record.get("ResourceRecords")[0].get("Value") == "10.0.10.10"

        record_data = RecordData
        record_data.dns_nm = "sells.maxmin.it"
        record_data.ip_address = "10.0.10.20"
        record_data.hosted_zone_id = hosted_zone_id

        # run the test
        self.record_dao.create(record_data)

        record = self.test_utils.describe_record(
            "sells.maxmin.it.", hosted_zone_id
        )

        assert record.get("Name") == "sells.maxmin.it."
        assert record.get("ResourceRecords")[0].get("Value") == "10.0.10.20"

    @mock_aws
    def test_create_record_twice(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        self.test_utils.create_record(
            "test.maxmin.it.", "10.0.10.10", hosted_zone_id
        )

        record_data = RecordData
        record_data.dns_nm = "test.maxmin.it"
        record_data.ip_address = "10.0.10.10"
        record_data.hosted_zone_id = hosted_zone_id

        try:
            self.record_dao.create(record_data)

            fail("An exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the record!"
        except Exception:
            fail("An AwsDaoException should have been raised!")

    @mock_aws
    def test_delete_record(self):
        hosted_zone_id = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )

        self.test_utils.create_record(
            "test.maxmin.it", "10.0.10.30", hosted_zone_id
        )

        record_data = RecordData
        record_data.dns_nm = "test.maxmin.it"
        record_data.ip_address = "10.0.10.30"
        record_data.hosted_zone_id = hosted_zone_id

        # run the test
        self.record_dao.delete(record_data)

        record = self.test_utils.describe_record(
            "test.maxmin.it", hosted_zone_id
        )

        assert not record

        self.test_utils.create_record(
            "sells.maxmin.it", "10.0.10.30", hosted_zone_id
        )

        record_data = RecordData
        record_data.dns_nm = "test.maxmin.it"
        record_data.ip_address = "10.0.10.30"
        record_data.hosted_zone_id = hosted_zone_id

        # run the test
        self.record_dao.delete(record_data)

        record = self.test_utils.describe_record(
            "sells.maxmin.it", hosted_zone_id
        )

        assert record
