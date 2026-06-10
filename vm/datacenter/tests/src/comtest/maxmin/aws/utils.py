"""
Created on Mar 23, 2023

@author: vagrant
"""

import os
import stat

import boto3
from botocore.exceptions import ClientError
from com.maxmin.aws.constants import Ec2Constants
import re


class TestUtils:
    """
    Utilities methods to use in tests
    """

    __test__ = False

    def __init__(self):
        self.ec2 = boto3.client("ec2")
        self.route53 = boto3.client("route53")

    def create_vpc(self, cidr: str, tags: list) -> dict:
        tag_specifications = [{"ResourceType": "vpc", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_vpc(
            CidrBlock=cidr,
            TagSpecifications=tag_specifications,
        ).get("Vpc")

    def describe_vpc(self, vpc_id: str) -> dict:
        response = self.ec2.describe_vpcs(
            VpcIds=[
                vpc_id,
            ],
        ).get("Vpcs")

        if len(response) == 0:
            return None
        else:
            return response[0]

    def describe_vpcs(self, vpc_nm: str) -> dict:
        return self.ec2.describe_vpcs(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        vpc_nm,
                    ],
                },
            ]
        ).get("Vpcs")

    def create_subnet(
        self, az: str, cidr: str, vpc_id: str, tags: list
    ) -> dict:
        tag_specifications = [{"ResourceType": "subnet", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_subnet(
            TagSpecifications=tag_specifications,
            AvailabilityZone=az,
            CidrBlock=cidr,
            VpcId=vpc_id,
        ).get("Subnet")

    def describe_subnet(self, subnet_id: str) -> dict:
        response = self.ec2.describe_subnets(
            SubnetIds=[
                subnet_id,
            ],
        ).get("Subnets")

        if len(response) == 0:
            return None
        else:
            return response[0]

    def describe_subnets(self, subnet_nm: str) -> dict:
        return self.ec2.describe_subnets(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        subnet_nm,
                    ],
                },
            ]
        ).get("Subnets")

    def create_route_table(self, vpc_id: str, tags: list) -> dict:
        tag_specifications = [{"ResourceType": "route-table", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_route_table(
            TagSpecifications=tag_specifications,
            VpcId=vpc_id,
        ).get("RouteTable")

    def describe_route_table(self, route_table_id: str) -> dict:
        response = self.ec2.describe_route_tables(
            RouteTableIds=[
                route_table_id,
            ],
        ).get("RouteTables")

        if len(response) == 0:
            return None
        else:
            return response[0]

    def describe_route_tables(self, route_table_nm: str) -> dict:
        return self.ec2.describe_route_tables(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        route_table_nm,
                    ],
                },
            ]
        ).get("RouteTables")

    def create_route(
        self,
        route_table_id: str,
        internet_gateway_id: str,
        destination_cidr: str,
    ) -> None:
        self.ec2.create_route(
            DestinationCidrBlock=destination_cidr,
            GatewayId=internet_gateway_id,
            RouteTableId=route_table_id,
        )

    def describe_routes(self, route_table_id) -> dict:
        return (
            self.ec2.describe_route_tables(
                RouteTableIds=[
                    route_table_id,
                ],
            )
            .get("RouteTables")[0]
            .get("Routes")
        )

    def associate_subnet_to_route_table(
        self, subnet_id: str, route_table_id: str
    ) -> None:
        self.ec2.associate_route_table(
            RouteTableId=route_table_id, SubnetId=subnet_id
        )

    def create_internet_gateway(self, tags: list) -> dict:
        tag_specifications = [{"ResourceType": "internet-gateway", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_internet_gateway(
            TagSpecifications=tag_specifications
        ).get("InternetGateway")

    def describe_internet_gateway(self, internet_gateway_id: str) -> dict:
        try:
            response = self.ec2.describe_internet_gateways(
                InternetGatewayIds=[
                    internet_gateway_id,
                ],
            ).get("InternetGateways")

            return response[0]
        except ClientError:
            return None

    def describe_internet_gateways(self, internet_gateway_nm: str) -> dict:
        try:
            return self.ec2.describe_internet_gateways(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [
                            internet_gateway_nm,
                        ],
                    },
                ]
            ).get("InternetGateways")
        except ClientError:
            return []

    def attach_internet_gateway_to_vpc(
        self, internet_gateway_id, vpc_id
    ) -> None:
        self.ec2.attach_internet_gateway(
            InternetGatewayId=internet_gateway_id, VpcId=vpc_id
        )

    def create_security_group(
        self, security_group_nm: str, description, vpc_id, tags: list
    ) -> dict:
        tag_specifications = [{"ResourceType": "security-group", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_security_group(
            TagSpecifications=tag_specifications,
            Description=description,
            GroupName=security_group_nm,
            VpcId=vpc_id,
        )

    def describe_security_group(self, security_group_id: str) -> dict:
        response = self.ec2.describe_security_groups(
            GroupIds=[
                security_group_id,
            ],
        ).get("SecurityGroups")

        if len(response) == 0:
            return None
        else:
            return response[0]

    def describe_security_groups(self, security_group_nm: str) -> dict:
        return self.ec2.describe_security_groups(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        security_group_nm,
                    ],
                },
            ]
        ).get("SecurityGroups")

    def allow_access_from_cidr(
        self,
        security_group_id: str,
        from_port: int,
        to_port: int,
        protocol: str,
        source_cidr: str,
        description: str,
    ) -> None:
        self.ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": from_port,
                    "IpProtocol": protocol,
                    "IpRanges": [
                        {
                            "CidrIp": source_cidr,
                            "Description": description,
                        },
                    ],
                    "ToPort": to_port,
                },
            ],
        )

    def allow_access_from_security_group(
        self,
        security_group_id: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_security_group_id: str,
        description: str,
    ) -> None:
        self.ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": from_port,
                    "IpProtocol": protocol,
                    "UserIdGroupPairs": [
                        {
                            "Description": description,
                            "GroupId": granted_security_group_id,
                        },
                    ],
                    "ToPort": to_port,
                },
            ],
        )

    def create_instance(
        self,
        image_id: str,
        security_group_id: str,
        subnet_id: str,
        private_ip: str,
        user_data_b64: str,  # contains SSH key info
        tags: list,
    ) -> dict:
        ec2_constants = Ec2Constants()

        tag_specifications = [{"ResourceType": "instance", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.run_instances(
            BlockDeviceMappings=[
                {
                    "DeviceName": ec2_constants.device,
                    "Ebs": {
                        "VolumeSize": ec2_constants.volume_size,
                    },
                },
            ],
            ImageId=image_id,
            InstanceType=ec2_constants.instance_type,
            MaxCount=1,
            MinCount=1,
            Placement={
                "Tenancy": ec2_constants.tenancy,
            },
            UserData=user_data_b64,
            NetworkInterfaces=[
                {
                    "DeviceIndex": 0,
                    "SubnetId": subnet_id,
                    "Groups": [security_group_id],
                    "PrivateIpAddress": private_ip,
                    "AssociatePublicIpAddress": True,
                },
            ],
            TagSpecifications=tag_specifications,
        ).get("Instances")[0]

    def terminate_instance(self, instance_id: str) -> None:
        self.ec2.terminate_instances(
            InstanceIds=[
                instance_id,
            ],
        )

    def describe_instances(self, instance_nm: str) -> dict:
        response = self.ec2.describe_instances(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        instance_nm,
                    ],
                },
            ],
        ).get("Reservations")

        instances = []
        for reservation in response:
            for instance in reservation.get("Instances"):
                instances.append(instance)

        return instances

    def decribe_instance(self, instance_id: str) -> dict:
        return (
            self.ec2.describe_instances(
                InstanceIds=[
                    instance_id,
                ],
            )
            .get("Reservations")[0]
            .get("Instances")[0]
        )

    def create_image(
        self, image_nm: str, instance_id: str, description: str, tags: list
    ) -> dict:
        tag_specifications = [{"ResourceType": "image", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        return self.ec2.create_image(
            InstanceId=instance_id,
            Description=description,
            Name=image_nm,
            TagSpecifications=tag_specifications,
        )

    def describe_images(self, image_nm: str) -> dict:
        return self.ec2.describe_images(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        image_nm,
                    ],
                },
            ],
        ).get("Images")

    def describe_image(self, image_id: str) -> dict:
        return self.ec2.describe_images(
            ImageIds=[
                image_id,
            ],
        ).get(
            "Images"
        )[0]

    def decribe_snapshot(self, snapshot_id: str) -> dict:
        try:
            return self.ec2.describe_snapshots(
                SnapshotIds=[
                    snapshot_id,
                ]
            ).get(
                "Snapshots"
            )[0]
        except ClientError:
            return []

    def create_key_pair(
        self, key_pair_nm: str, tags: list, private_key_path: str
    ) -> dict:
        tag_specifications = [{"ResourceType": "key-pair", "Tags": []}]

        for tag in tags:
            tag_specifications[0]["Tags"].append(tag)

        response = self.ec2.create_key_pair(
            KeyName=key_pair_nm,
            KeyType="rsa",
            KeyFormat="pem",
            TagSpecifications=tag_specifications,
        )

        if private_key_path:
            private_key = response.get("KeyMaterial")
            private_key_file = f"{private_key_path}"
            private_key_file_handle = open(private_key_file, "w")
            private_key_file_handle.write(private_key)
            private_key_file_handle.close()

            # Setting the given file to be read by the owner.
            os.chmod(private_key_file, stat.S_IREAD)

        return response

    def delete_private_key_file(self, private_key_path) -> None:
        private_key_file = f"{private_key_path}"

        if os.path.isfile(private_key_file) is True:
            os.remove(private_key_file)

    def describe_key_pairs(self, key_pair_nm: str) -> dict:
        try:
            return self.ec2.describe_key_pairs(
                IncludePublicKey=True,
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [
                            key_pair_nm,
                        ],
                    },
                ],
            ).get("KeyPairs")
        except ClientError:
            return []

    def create_hosted_zone(self, hosted_zone_nm: str) -> dict:
        return self.route53.create_hosted_zone(
            Name=hosted_zone_nm, CallerReference=str(hash("maxmin"))
        ).get("HostedZone")

    def describe_hosted_zones(self) -> dict:
        return self.route53.list_hosted_zones_by_name().get("HostedZones")

    def create_record(
        self, dns_nm: str, ip_address: str, hosted_zone_id: str
    ) -> dict:
        return (
            self.route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "CREATE",
                            "ResourceRecordSet": {
                                "Name": dns_nm,
                                "Type": "A",
                                "TTL": 300,
                                "ResourceRecords": [{"Value": ip_address}],
                            },
                        }
                    ]
                },
            )
            .get("ChangeInfo")
            .get("Id")
        )

    def describe_records(self, hosted_zone_id: str) -> dict:
        return self.route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id
        ).get("ResourceRecordSets")

    def describe_record(self, dns_nm: str, hosted_zone_id: str) -> dict:
        response = self.route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id
        ).get("ResourceRecordSets")

        fqdn_pattern = re.compile(dns_nm + "[.]?")

        record = None
        for r in response:
            if fqdn_pattern.match(r.get("Name")):
                record = r
                break

        return record

    def build_tag(self, key: str, value: str) -> dict:
        return {"Key": key, "Value": value}

    def get_tag_value(self, key: str, tags: list) -> str:
        """
        Returns the value of of a tag by key
        """
        value = None
        for tag in tags:
            if tag.get("Key") == key:
                value = tag.get("Value")

        return value
