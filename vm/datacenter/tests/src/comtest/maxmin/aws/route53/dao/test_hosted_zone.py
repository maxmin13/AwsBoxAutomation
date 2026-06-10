"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from moto import mock_aws

from com.maxmin.aws.route53.dao.hosted_zone import HostedZoneDao
from comtest.maxmin.aws.utils import TestUtils


class HostedZoneDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.hosted_zone_dao = HostedZoneDao()

    @mock_aws
    def test_load_all_hosted_zones(self):
        hosted_zone_id1 = self.test_utils.create_hosted_zone("maxmin.it.").get(
            "Id"
        )
        hosted_zone_id2 = self.test_utils.create_hosted_zone(
            "maxmin.com."
        ).get("Id")

        # run the test
        hosted_zone_datas = self.hosted_zone_dao.load_all()

        assert len(hosted_zone_datas) == 2

        assert hosted_zone_datas[0].hosted_zone_id == hosted_zone_id2
        assert hosted_zone_datas[0].registered_domain == "maxmin.com."

        assert hosted_zone_datas[1].hosted_zone_id == hosted_zone_id1
        assert hosted_zone_datas[1].registered_domain == "maxmin.it."
