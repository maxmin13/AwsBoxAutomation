"""
Created on Apr 1, 2024

@author: vagrant
"""
import os
import unittest

from moto.core.decorator import mock_aws

from com.maxmin.aws.configuration.dao.datacenter import (
    DatacenterConfigDao,
    HostedZoneConfigDao,
)
from com.maxmin.aws.configuration.dao.domain.datacenter import (
    CidrRuleConfig,
    SgpRuleConfig,
)
from com.maxmin.aws.constants import ProjectDirectories


class ConfigurationDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.datacenter_config_file = os.path.join(
            ProjectDirectories.TEST_DIR, "config/test_datacenter.json"
        )
        self.hosted_zone_config_file = os.path.join(
            ProjectDirectories.TEST_DIR, "config/test_hostedzone.json"
        )
        self.datacenter_config_dao = DatacenterConfigDao()
        self.hosted_zone_config_dao = HostedZoneConfigDao()

    @mock_aws
    def test_load_datacenter_configuration(self):
        # run the test
        datacenter_config = self.datacenter_config_dao.load(
            self.datacenter_config_file
        )

        assert datacenter_config.vpc.description == "AWS VPC"
        assert datacenter_config.vpc.name == "aws-datacenter"
        assert datacenter_config.vpc.cidr == "10.0.0.0/16"
        assert datacenter_config.vpc.region == "eu-west-1"

        assert datacenter_config.vpc.tags[0].key == "Class"
        assert datacenter_config.vpc.tags[0].value == "webservices"

        assert datacenter_config.internet_gateway.name == "aws-gateway"

        assert datacenter_config.internet_gateway.tags[0].key == "Class"
        assert (
            datacenter_config.internet_gateway.tags[0].value == "webservices"
        )

        assert datacenter_config.route_table.name == "aws-routetable"

        assert datacenter_config.route_table.tags[0].key == "Class"
        assert datacenter_config.route_table.tags[0].value == "webservices"

        assert (
            datacenter_config.subnets[0].description
            == "AWS network shared by the instances."
        )
        assert datacenter_config.subnets[0].name == "admin-subnet"
        assert datacenter_config.subnets[0].az == "eu-west-1a"
        assert datacenter_config.subnets[0].cidr == "10.0.20.0/24"

        assert datacenter_config.subnets[0].tags[0].key == "Class"
        assert datacenter_config.subnets[0].tags[0].value == "webservices"

        assert (
            datacenter_config.security_groups[0].description
            == "Admin instance security group."
        )
        assert datacenter_config.security_groups[0].name == "admin-sgp"

        assert datacenter_config.security_groups[0].tags[0].key == "Class"
        assert (
            datacenter_config.security_groups[0].tags[0].value == "webservices"
        )

        assert isinstance(
            datacenter_config.security_groups[0].rules[0], CidrRuleConfig
        )

        assert datacenter_config.security_groups[0].rules[0].from_port == -1
        assert datacenter_config.security_groups[0].rules[0].to_port == -1
        assert datacenter_config.security_groups[0].rules[0].protocol == "icmp"
        assert (
            datacenter_config.security_groups[0].rules[0].cidr == "0.0.0.0/0"
        )
        assert (
            datacenter_config.security_groups[0].rules[0].description
            == "ping access"
        )

        assert isinstance(
            datacenter_config.security_groups[0].rules[1], SgpRuleConfig
        )

        assert datacenter_config.security_groups[0].rules[1].from_port == 80
        assert datacenter_config.security_groups[0].rules[1].to_port == 90
        assert datacenter_config.security_groups[0].rules[1].protocol == "http"
        assert (
            datacenter_config.security_groups[0].rules[1].sgp_name
            == "mysecuritygroup"
        )
        assert (
            datacenter_config.security_groups[0].rules[1].description
            == "HTTP access"
        )

        assert datacenter_config.instances[0].name == "admin-box"
        assert datacenter_config.instances[0].username == "awsadmin"
        assert datacenter_config.instances[0].password == "awsadminpwd"
        assert datacenter_config.instances[0].private_ip == "10.0.20.35"
        assert datacenter_config.instances[0].security_group == "admin-sgp"
        assert datacenter_config.instances[0].subnet == "admin-subnet"
        assert (
            datacenter_config.instances[0].parent_img
            == "amzn2-ami-kernel-5.10-hvm-2.0.20230719.0-x86_64-gp2"
        )
        assert datacenter_config.instances[0].target_img == "my-new-image"
        assert datacenter_config.instances[0].dns_domain == "admin.maxmin.it"
        assert datacenter_config.instances[0].host_name == "host.maxmin.it"

        assert datacenter_config.instances[0].tags[0].key == "Class"
        assert datacenter_config.instances[0].tags[0].value == "webservices"

    @mock_aws
    def test_load_hosted_zone_configuration(self):
        # run the test
        hosted_zone_config = self.hosted_zone_config_dao.load(
            self.hosted_zone_config_file
        )

        assert hosted_zone_config.description == "Route 53 hosted zone"
        assert hosted_zone_config.registered_domain == "maxmin.it"
