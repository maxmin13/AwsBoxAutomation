import os
import sys

from com.maxmin.aws.configuration.dao.datacenter import (
    DatacenterConfigDao,
    HostedZoneConfigDao,
)
from com.maxmin.aws.configuration.dao.domain.datacenter import CidrRuleConfig
from com.maxmin.aws.ec2.service.instance import InstanceService
from com.maxmin.aws.ec2.service.internet_gateway import InternetGatewayService
from com.maxmin.aws.ec2.service.route_table import RouteTableService
from com.maxmin.aws.ec2.service.security_group import SecurityGroupService
from com.maxmin.aws.ec2.service.ssh import KeyPairService
from com.maxmin.aws.ec2.service.subnet import SubnetService
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.dao.domain.record import RecordData
from com.maxmin.aws.route53.dao.record import RecordDao
from com.maxmin.aws.route53.service.hosted_zone import HostedZoneService

'''
The program uses AWS boto3 library to make AWS requests.
You must have both AWS credentials and an AWS Region set in order to make requests.
See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html.

export the AWS access key id
export the AWS secret access key
export the AWS region
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
    Logger.info(f"Datacenter configuration file {datacenter_config_file}")
    Logger.info(f"Hosted zone configuration file {hosted_zone_config_file}")

    # load datacenter configuration file

    datacenter_config_dao = DatacenterConfigDao()
    datacenter_config = datacenter_config_dao.load(datacenter_config_file)

    # load hosted zone configuration file

    hosted_zone_config_dao = HostedZoneConfigDao()
    hostedzone_config = hosted_zone_config_dao.load(hosted_zone_config_file)

    Logger.info("Deleting AWS data center ...")

    #
    # DNS hosted zone
    #

    instance_configs = datacenter_config.instances
    instance_service = InstanceService()
    hosted_zone_service = HostedZoneService()
    record_dao = RecordDao()

    if hostedzone_config.registered_domain:
        hosted_zone = hosted_zone_service.load_hosted_zone(
            hostedzone_config.registered_domain
        )
        if hosted_zone:
            for instance_config in instance_configs:
                instance = instance_service.load_instance(instance_config.name)
                if instance:
                    dns_record = hosted_zone_service.load_record(
                        instance_config.dns_domain,
                        hosted_zone.registered_domain,
                    )
                    if dns_record:
                        Logger.info("Deleting AWS instance DNS record ...")
                        record_data = RecordData()
                        record_data.ip_address = instance.public_ip
                        record_data.dns_nm = instance_config.dns_domain
                        record_data.hosted_zone_id = hosted_zone.hosted_zone_id
                        record_dao.delete(record_data)
                        Logger.info("AWS instance DNS record deleted!")
                    else:
                        Logger.warn("AWS instance DNS record already deleted!")

    #
    # instances
    #

    keypair_service = KeyPairService()

    for instance_config in instance_configs:
        instance = instance_service.load_instance(instance_config.name)

        if instance:
            Logger.info("Deleting AWS instance ...")
            instance_service.terminate_instance(instance_config.name)
            Logger.info("AWS instance deleted!")
        else:
            Logger.warn("AWS instance already deleted!")

        for instance_config in instance_configs:
            # key pair with the same name of the instance
            keypair = keypair_service.load_key_pair(instance_config.name)

            if keypair:
                keypair_service.delete_key_pair(instance_config.name)
                Logger.info("AWS instance key pair deleted!")
            else:
                Logger.warn("AWS instance key pair already deleted!")

    #
    # security groups
    #

    security_group_configs = datacenter_config.security_groups
    security_group_service = SecurityGroupService()

    for security_group_config in security_group_configs:
        security_group = security_group_service.load_security_group(
            security_group_config.name
        )
        if security_group:
            for rule_config in security_group_config.rules:
                if isinstance(rule_config, CidrRuleConfig):
                    cidr_rule = security_group_service.load_cidr_rule(
                        security_group_config.name,
                        rule_config.from_port,
                        rule_config.to_port,
                        rule_config.protocol,
                        rule_config.cidr,
                    )

                    if cidr_rule:
                        security_group_service.delete_cidr_rule(
                            security_group_config.name,
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )
                        Logger.info("Cidr rule deleted!")
                    else:
                        Logger.warn("Cidr rule already deleted!")
                else:
                    sgp_rule = security_group_service.load_security_group_rule(
                        security_group_config.name,
                        rule_config.from_port,
                        rule_config.to_port,
                        rule_config.protocol,
                        rule_config.sgp_name,
                    )

                    if sgp_rule:
                        security_group_service.delete_security_group_rule(
                            security_group_config.name,
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.sgp_name,
                            rule_config.description,
                        )
                        Logger.info("Sgp rule deleted!")
                    else:
                        Logger.warn("Sgp rule already deleted!")

    for security_group_config in security_group_configs:
        security_group = security_group_service.load_security_group(
            security_group_config.name
        )

        if security_group:
            security_group_service.delete_security_group(
                security_group_config.name
            )

            Logger.info("Security group deleted!")

        else:
            Logger.warn("Security group already deleted!")

    #
    # Internet gateway
    #

    internet_gateway_config = datacenter_config.internet_gateway
    internet_gateway_service = InternetGatewayService()
    internet_gateway = internet_gateway_service.load_internet_gateway(
        datacenter_config.internet_gateway.name
    )

    if internet_gateway:
        internet_gateway_service.delete_internet_gateway(
            internet_gateway_config.name
        )

        Logger.info("Internet gateway deleted!")
    else:
        Logger.warn("Internet gateway already deleted")

    #
    # subnets
    #

    subnet_configs = datacenter_config.subnets
    subnet_service = SubnetService()

    for subnet_config in subnet_configs:
        subnet = subnet_service.load_subnet(subnet_config.name)

        if subnet:
            subnet_service.delete_subnet(subnet_config.name)
            Logger.info("Subnet deleted!")
        else:
            Logger.warn("Subnet already deleted")

    #
    # route table
    #

    route_table_config = datacenter_config.route_table
    route_table_service = RouteTableService()
    route_table = route_table_service.load_route_table(
        datacenter_config.route_table.name
    )

    if route_table:
        route_table_service.delete_route_table(route_table_config.name)
        Logger.info("Route table deleted!")
    else:
        Logger.warn("Route table already deleted")

    #
    # VPC
    #

    vpc_config = datacenter_config.vpc
    vpc_service = VpcService()
    vpc = vpc_service.load_vpc(vpc_config.name)

    if vpc:
        vpc_service.delete_vpc(datacenter_config.vpc.name)
        Logger.info("VPC deleted!")
    else:
        Logger.warn("VPC already deleted")
