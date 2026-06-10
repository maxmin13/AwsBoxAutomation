"""
Created on Mar 13, 2023

@author: vagrant
"""
import json
from json.decoder import JSONDecodeError
from pathlib import Path

from com.maxmin.aws.configuration.dao.domain.datacenter import (
    HostedZoneConfig,
    DatacenterConfig,
    VpcConfig,
    SubnetConfig,
    SecurityGroupConfig,
    SgpRuleConfig,
    CidrRuleConfig,
    InstanceConfig,
    TagConfig,
    InternetGatewayConfig,
)
from com.maxmin.aws.exception import AwsException


class HostedZoneConfigDao(object):
    """
    Loads a JSON file into a configuration object.
    """

    def load(self, hosted_zone_config_file: str) -> HostedZoneConfig:
        try:
            config_file_path = Path(hosted_zone_config_file)
            content = config_file_path.read_text("UTF8")
        except FileNotFoundError:
            raise AwsException("Error reading configuration file!")

        try:
            hosted_zone = json.loads(content).get("HostedZone")
        except JSONDecodeError:
            raise AwsException("Invalid JSON file!")

        response = HostedZoneConfig()
        response.description = hosted_zone.get("Description")
        response.registered_domain = hosted_zone.get("RegisteredDomain")

        return response


class DatacenterConfigDao(object):
    """
    Loads a JSON file into a configuration object.
    """

    def load(self, datacenter_config_file: str) -> DatacenterConfig:
        try:
            config_file_path = Path(datacenter_config_file)
            content = config_file_path.read_text("UTF8")
        except FileNotFoundError:
            raise AwsException("Error reading configuration file!")
        try:
            datacenter = json.loads(content).get("Datacenter")
        except JSONDecodeError:
            raise AwsException("Invalid JSON file!")

        response = DatacenterConfig()

        #
        # Parse VPC
        #
        vpc = datacenter.get("VPC")

        vpc_config = VpcConfig()
        vpc_config.name = vpc.get("Name")
        vpc_config.description = vpc.get("Description")
        vpc_config.cidr = vpc.get("Cidr")
        vpc_config.region = vpc.get("Region")

        vpc_tags = vpc.get("Tags")
        if vpc_tags:
            for tag in vpc_tags:
                vpc_tag_config = TagConfig()
                vpc_tag_config.key = tag.get("Key")
                vpc_tag_config.value = tag.get("Value")
                vpc_config.tags.append(vpc_tag_config)

        response.vpc = vpc_config

        #
        # Parse Internet gateway
        #
        internet_gateway = datacenter.get("InternetGateway")

        internet_gateway_config = InternetGatewayConfig()
        internet_gateway_config.name = internet_gateway.get("Name")

        internet_gateway_tags = internet_gateway.get("Tags")
        if internet_gateway_tags:
            for tag in internet_gateway_tags:
                internet_gateway_tag_config = TagConfig()
                internet_gateway_tag_config.key = tag.get("Key")
                internet_gateway_tag_config.value = tag.get("Value")
                internet_gateway_config.tags.append(
                    internet_gateway_tag_config
                )

        response.internet_gateway = internet_gateway_config

        #
        # Parse route table
        #
        route_table = datacenter.get("RouteTable")

        route_table_config = InternetGatewayConfig()
        route_table_config.name = route_table.get("Name")

        route_table_tags = route_table.get("Tags")
        if route_table_tags:
            for tag in route_table_tags:
                route_table_tag_config = TagConfig()
                route_table_tag_config.key = tag.get("Key")
                route_table_tag_config.value = tag.get("Value")
                route_table_config.tags.append(route_table_tag_config)

        response.route_table = route_table_config

        #
        # Parse subnets
        #
        for subnet in datacenter.get("Subnets"):
            subnet_config = SubnetConfig()
            subnet_config.name = subnet.get("Name")
            subnet_config.description = subnet.get("Description")
            subnet_config.az = subnet.get("Az")
            subnet_config.cidr = subnet.get("Cidr")
            response.subnets.append(subnet_config)

            subnet_tags = subnet.get("Tags")
            for tag in subnet_tags:
                tag_config = TagConfig()
                tag_config.key = tag.get("Key")
                tag_config.value = tag.get("Value")
                subnet_config.tags.append(tag_config)

        #
        # Parse security group
        #
        for security_group in datacenter.get("SecurityGroups"):
            security_group_config = SecurityGroupConfig()
            security_group_config.name = security_group.get("Name")
            security_group_config.description = security_group.get(
                "Description"
            )
            response.security_groups.append(security_group_config)

            security_group_tags = security_group.get("Tags")
            for tag in security_group_tags:
                tag_config = TagConfig()
                tag_config.key = tag.get("Key")
                tag_config.value = tag.get("Value")
                security_group_config.tags.append(tag_config)

            rules = security_group.get("Rules")

            for rule in rules:
                if "SgpName" in rule:
                    rule_config = SgpRuleConfig()
                    rule_config.from_port = rule.get("FromPort")
                    rule_config.to_port = rule.get("ToPort")
                    rule_config.protocol = rule.get("Protocol")
                    rule_config.sgp_name = rule.get("SgpName")
                    rule_config.description = rule.get("Description")

                else:
                    rule_config = CidrRuleConfig()
                    rule_config.from_port = rule.get("FromPort")
                    rule_config.to_port = rule.get("ToPort")
                    rule_config.protocol = rule.get("Protocol")
                    rule_config.cidr = rule.get("Cidr")
                    rule_config.description = rule.get("Description")

                security_group_config.rules.append(rule_config)

        #
        # Parse instances
        #
        for instance in datacenter.get("Instances"):
            instance_config = InstanceConfig()
            instance_config.name = instance.get("Name")
            instance_config.username = instance.get("UserName")
            instance_config.password = instance.get("UserPassword")
            instance_config.private_ip = instance.get("PrivateIp")
            instance_config.security_group = instance.get("SecurityGroup")
            instance_config.subnet = instance.get("Subnet")
            instance_config.parent_img = instance.get("ParentImage")
            instance_config.target_img = instance.get("TargetImage")
            instance_config.dns_domain = instance.get("DnsDomain")
            instance_config.host_name = instance.get("HostName")

            instance_tags = instance.get("Tags")
            for tag in instance_tags:
                tag_config = TagConfig()
                tag_config.key = tag.get("Key")
                tag_config.value = tag.get("Value")
                instance_config.tags.append(tag_config)

            response.instances.append(instance_config)

            return response
