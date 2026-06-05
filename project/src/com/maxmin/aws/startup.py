import os
import sys

from com.maxmin.aws.configuration.dao.datacenter import (
    DatacenterConfigDao,
    HostedZoneConfigDao,
)
from com.maxmin.aws.configuration.dao.domain.datacenter import CidrRuleConfig
from com.maxmin.aws.ec2.dao.domain.route_table import RouteData
from com.maxmin.aws.ec2.dao.route_table import RouteDao
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.instance import InstanceService
from com.maxmin.aws.ec2.service.internet_gateway import InternetGatewayService
from com.maxmin.aws.ec2.service.route_table import RouteTableService
from com.maxmin.aws.ec2.service.security_group import SecurityGroupService
from com.maxmin.aws.ec2.service.ssh import KeyPairService
from com.maxmin.aws.ec2.service.subnet import SubnetService
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.service.hosted_zone import HostedZoneService
from com.maxmin.aws.constants import ProjectDirectories

'''
The program uses AWS boto3 library to make AWS requests.
You must have both AWS credentials and an AWS Region set in order to make requests.
See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html.

export AWS_ACCESS_KEY_ID=xxxxxx
export AWS_SECRET_ACCESS_KEY=yyyyyy
export AWS_DEFAULT_REGION=zzzzzz
'''

if __name__ == "__main__":
    
    # AWS IAM user credentials

    if not os.getenv("AWS_ACCESS_KEY_ID"):
        raise AwsException("environment variable AWS_ACCESS_KEY_ID not set!")

    if not os.getenv("AWS_SECRET_ACCESS_KEY"):
        raise AwsException("environment variable AWS_SECRET_ACCESS_KEY not set!")

    if not os.getenv("AWS_DEFAULT_REGION"):
        raise AwsException("environment variable AWS_DEFAULT_REGION not set!")
    
    # repository root (prefer repo-relative paths over DATACENTER_DIR env var)
    datacenter_dir = ProjectDirectories.REPO_ROOT

    datacenter_config_file = sys.argv[1]
    hosted_zone_config_file = sys.argv[2]

    if not datacenter_config_file:
        raise AwsException("Datacenter configuration file not passed!")

    if not hosted_zone_config_file:
        raise AwsException("Hosted zone configuration file not passed!")

    Logger.info(f"Datacenter directory {datacenter_dir}")
    Logger.info(f"Private key directory {ProjectDirectories.ACCESS_DIR}")
    Logger.info(f"Datacenter configuration file {datacenter_config_file}")
    Logger.info(f"Hosted zone configuration file {hosted_zone_config_file}")

    # load datacenter configuration file

    datacenter_config_dao = DatacenterConfigDao()
    datacenter_config = datacenter_config_dao.load(datacenter_config_file)

    # load hosted zone configuration file

    hosted_zone_config_dao = HostedZoneConfigDao()
    hostedzone_config = hosted_zone_config_dao.load(hosted_zone_config_file)

    Logger.info("Creating AWS data center ...")

    #
    # VPC
    #

    vpc_config = datacenter_config.vpc
    vpc_service = VpcService()
    vpc = vpc_service.load_vpc(vpc_config.name)

    if not vpc:
        vpc_tags = []
        for tag in vpc_config.tags:
            vpc_tags.append(Tag(tag.key, tag.value))

        vpc_service.create_vpc(
            datacenter_config.vpc.name, datacenter_config.vpc.cidr, vpc_tags
        )

        Logger.info("VPC created!")

        vpc = vpc_service.load_vpc(vpc_config.name)
    else:
        Logger.warn("VPC already created!")

    #
    # Internet gateway
    #

    internet_gateway_config = datacenter_config.internet_gateway
    internet_gateway_service = InternetGatewayService()
    internet_gateway = internet_gateway_service.load_internet_gateway(
        datacenter_config.internet_gateway.name
    )

    if not internet_gateway:
        internet_gateway_tags = []
        for tag in internet_gateway_config.tags:
            internet_gateway_tags.append(Tag(tag.key, tag.value))

        internet_gateway_service.create_internet_gateway(
            internet_gateway_config.name,
            vpc_config.name,
            internet_gateway_tags,
        )

        Logger.info("Internet gateway created!")

        internet_gateway = internet_gateway_service.load_internet_gateway(
            datacenter_config.internet_gateway.name
        )
    else:
        Logger.warn("Internet gateway already created!")

    #
    # route table
    #

    route_table_config = datacenter_config.route_table
    route_table_service = RouteTableService()
    route_table = route_table_service.load_route_table(
        datacenter_config.route_table.name
    )

    if not route_table:
        route_table_tags = []
        for tag in route_table_config.tags:
            route_table_tags.append(Tag(tag.key, tag.value))

        route_table_service.create_route_table(
            route_table_config.name, vpc_config.name, route_table_tags
        )

        Logger.info("Route table created!")

        route_table = route_table_service.load_route_table(
            datacenter_config.route_table.name
        )
    else:
        Logger.warn("Route table already created!")

    route = route_table_service.load_route(
        route_table_config.name, internet_gateway_config.name, "0.0.0.0/0"
    )

    if not route:
        route_dao = RouteDao()
        route_data = RouteData()
        route_data.route_table_id = route_table.route_table_id
        route_data.internet_gateway_id = internet_gateway.internet_gateway_id
        route_data.destination_cidr = "0.0.0.0/0"
        route_dao.create(route_data)

        Logger.info("Route to the Internet gateway created!")
    else:
        Logger.warn("Route to the Internet gateway already created!")

    #
    # subnets
    #

    subnet_configs = datacenter_config.subnets
    subnet_service = SubnetService()

    for subnet_config in subnet_configs:
        subnet = subnet_service.load_subnet(subnet_config.name)

        if not subnet:
            subnet_tags = []
            for tag in subnet_config.tags:
                subnet_tags.append(Tag(tag.key, tag.value))

            subnet_service.create_subnet(
                subnet_config.name,
                subnet_config.az,
                subnet_config.cidr,
                vpc_config.name,
                subnet_tags,
            )

            Logger.info("Subnet created!")

            subnet = subnet_service.load_subnet(subnet_config.name)

            route_table_service.associate_route_table(
                route_table_config.name, subnet_config.name
            )
        else:
            Logger.warn("Subnet already created!")

    #
    # security groups
    #

    security_group_configs = datacenter_config.security_groups
    security_group_service = SecurityGroupService()

    for security_group_config in security_group_configs:
        security_group = security_group_service.load_security_group(
            security_group_config.name
        )

        if not security_group:
            security_group_tags = []
            for tag in security_group_config.tags:
                security_group_tags.append(Tag(tag.key, tag.value))

            security_group_service.create_security_group(
                security_group_config.name,
                security_group_config.description,
                vpc_config.name,
                security_group_tags,
            )

            Logger.info("Security group created!")

            security_group = security_group_service.load_security_group(
                security_group_config.name
            )

        else:
            Logger.warn("Security group already created!")

    for security_group_config in security_group_configs:
        for rule_config in security_group_config.rules:
            if isinstance(rule_config, CidrRuleConfig):
                cidr_rule = security_group_service.load_cidr_rule(
                    security_group_config.name,
                    rule_config.from_port,
                    rule_config.to_port,
                    rule_config.protocol,
                    rule_config.cidr,
                )

                if not cidr_rule:
                    security_group_service.create_cidr_rule(
                        security_group_config.name,
                        rule_config.from_port,
                        rule_config.to_port,
                        rule_config.protocol,
                        rule_config.cidr,
                        rule_config.description,
                    )
                    Logger.info("Cidr rule created!")
                else:
                    Logger.warn("Cidr rule already created!")
            else:
                sgp_rule = security_group_service.load_security_group_rule(
                    security_group_config.name,
                    rule_config.from_port,
                    rule_config.to_port,
                    rule_config.protocol,
                    rule_config.sgp_name,
                )

                if not sgp_rule:
                    security_group_service.create_security_group_rule(
                        security_group_config.name,
                        rule_config.from_port,
                        rule_config.to_port,
                        rule_config.protocol,
                        rule_config.sgp_name,
                        rule_config.description,
                    )
                    Logger.info("Sgp rule created!")
                else:
                    Logger.warn("Sgp rule already created!")

    #
    # instances
    #

    instance_configs = datacenter_config.instances
    instance_service = InstanceService()
    keypair_service = KeyPairService()

    for instance_config in instance_configs:
        # key pair with the same name of the instance
        keypair = keypair_service.load_key_pair(instance_config.name)

        if not keypair:
            keypair_service.create_key_pair(instance_config.name, None)
            Logger.info("Instance key pair created!")
        else:
            Logger.warn("Instance key pair already created!")

    for instance_config in instance_configs:
        instance = instance_service.load_instance(instance_config.name)

        if not instance:
            instance_tags = []
            for tag in instance_config.tags:
                instance_tags.append(Tag(tag.key, tag.value))

            Logger.info("Creating AWS instance ...")

            instance_service.create_instance(
                instance_config.name,
                instance_config.private_ip,
                instance_config.parent_img,
                security_group_config.name,
                subnet_config.name,
                vpc_config.name,
                instance_config.username,
                instance_config.password,
                instance_config.host_name,
                instance_config.name,
                instance_tags,
            )

            Logger.info("AWS instance created!")

            instance = instance_service.load_instance(instance_config.name)

        else:
            Logger.warn("AWS instance already created!")

    #
    # DNS hosted zone
    #

    hosted_zone_service = HostedZoneService()

    if hostedzone_config.registered_domain:
        hosted_zone = hosted_zone_service.load_hosted_zone(
            hostedzone_config.registered_domain
        )
        if hosted_zone:
            for instance_config in instance_configs:
                instance = instance_service.load_instance(instance_config.name)
                dns_record = hosted_zone_service.load_record(
                    instance_config.dns_domain, hosted_zone.registered_domain
                )
                if not dns_record:
                    Logger.info("Creating AWS instance DNS record ...")
                    hosted_zone_service.create_record(
                        instance_config.dns_domain,
                        instance.public_ip,
                        hosted_zone.registered_domain,
                    )

                    Logger.info("AWS instance DNS record created!")
                else:
                    Logger.warn("AWS instance DNS record already created!")
        else:
            Logger.info("AWS hosted zone not found!")

        hosted_zone = hosted_zone_service.load_hosted_zone(
            hostedzone_config.registered_domain
        )
        if hosted_zone:
            for instance_config in instance_configs:
                instance = instance_service.load_instance(instance_config.name)
                dns_record = hosted_zone_service.load_record(
                    instance_config.dns_domain, hosted_zone.registered_domain
                )
                if dns_record:
                    Logger.info(
                        "AWS Instance "
                        + instance_config.name
                        + " "
                        + instance.public_ip
                        + " "
                        + dns_record.dns_nm
                    )
                else:
                    Logger.info(
                        "AWS Instance "
                        + instance_config.name
                        + " "
                        + instance.public_ip
                    )
        else:
            Logger.info(
                "AWS Instance "
                + instance_config.name
                + " "
                + instance.public_ip
            )
