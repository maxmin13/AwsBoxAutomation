"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.security_group import (
    SecurityGroupData,
    CidrRuleData,
    SecurityGroupRuleData,
)


class SecurityGroupDao(Ec2Dao):
    def load(self, security_group_id: str) -> SecurityGroupData:
        """
        Loads a security group by its unique identifier.
        Returns a SecurityGroupData object.
        """
        try:
            response = self.ec2.describe_security_groups(
                GroupIds=[
                    security_group_id,
                ],
            ).get("SecurityGroups")[0]

            return SecurityGroupData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the security group!")

    def load_all(self, security_group_nm: str) -> list:
        """
        Loads the security groups with a tag with key 'name' equals security_group_nm.
        Returns a list of SecurityGroupData objects.
        """
        try:
            response = self.ec2.describe_security_groups(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [security_group_nm],
                    },
                ],
            ).get("SecurityGroups")

            security_group_datas = []

            for security_group in response:
                security_group_datas.append(
                    SecurityGroupData.build(security_group)
                )

            return security_group_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the security groups!")

    def create(self, security_group_data: SecurityGroupData) -> None:
        """
        Creates a security group and waits until it's available.
        """
        try:
            tag_specifications = [
                {"ResourceType": "security-group", "Tags": []}
            ]

            for tag_data in security_group_data.tags:
                tag_specifications[0]["Tags"].append(tag_data.to_dictionary())

            identifier = self.ec2.create_security_group(
                TagSpecifications=tag_specifications,
                Description=security_group_data.description,
                GroupName=security_group_data.security_group_nm,
                VpcId=security_group_data.vpc_id,
            ).get("GroupId")

            waiter = self.ec2.get_waiter("security_group_exists")
            waiter.wait(GroupIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the security group!")

    def delete(self, security_group_data: SecurityGroupData) -> None:
        """
        Deletes the security group.
        """
        try:
            self.ec2.delete_security_group(
                GroupId=security_group_data.security_group_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the security group!")


class CidrRuleDao(Ec2Dao):
    def load_all(self, security_group_id: str) -> list:
        """
        Loads all the inbound rules in a security group based on CIDR intervals.
        Returns a list of CidrRuleData objects.
        """
        try:
            response = (
                self.ec2.describe_security_groups(
                    GroupIds=[
                        security_group_id,
                    ],
                )
                .get("SecurityGroups")[0]
                .get("IpPermissions")
            )

            rules = []

            for rule in response:
                rules.append(CidrRuleData.build(rule, security_group_id))

            return rules

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the security group rules!")

    def create(self, cidr_rule_data: CidrRuleData) -> None:
        """
        Creates an inbound rule based on CIDR interval.
        """

        ip_range_datas = []
        for ip_range_data in cidr_rule_data.ip_ranges:
            ip_range_datas.append(ip_range_data.to_dictionary())

        try:
            self.ec2.authorize_security_group_ingress(
                GroupId=cidr_rule_data.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": cidr_rule_data.from_port,
                        "ToPort": cidr_rule_data.to_port,
                        "IpProtocol": cidr_rule_data.protocol,
                        "IpRanges": ip_range_datas,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the security group rule!")

    def delete(self, cidr_rule_data: CidrRuleData) -> None:
        """
        Deletes an inbound rule based on CIDR interval.
        """

        ip_range_datas = []
        for ip_range_data in cidr_rule_data.ip_ranges:
            ip_range_datas.append(ip_range_data.to_dictionary())

        try:
            self.ec2.revoke_security_group_ingress(
                GroupId=cidr_rule_data.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": cidr_rule_data.from_port,
                        "ToPort": cidr_rule_data.to_port,
                        "IpProtocol": cidr_rule_data.protocol,
                        "IpRanges": ip_range_datas,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the security group rule!")


class SecurityGroupRuleDao(Ec2Dao):
    def load_all(self, security_group_id: str) -> list:
        """
        Loads all the inbound rules in a security group based on security group identifiers.
        Returns a list of SecurityGroupRuleData objects.
        """
        try:
            response = (
                self.ec2.describe_security_groups(
                    GroupIds=[
                        security_group_id,
                    ],
                )
                .get("SecurityGroups")[0]
                .get("IpPermissions")
            )

            rules = []

            for rule in response:
                rules.append(
                    SecurityGroupRuleData.build(rule, security_group_id)
                )

            return rules
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the security group rules!")

    def create(self, security_group_rule_data: SecurityGroupRuleData) -> None:
        """
        Creates an inbound rule based security group identifiers.
        """

        user_id_group_pair_datas = []
        for (
            user_id_group_pair_data
        ) in security_group_rule_data.user_id_group_pairs:
            user_id_group_pair_datas.append(
                user_id_group_pair_data.to_dictionary()
            )

        try:
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_rule_data.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": security_group_rule_data.from_port,
                        "ToPort": security_group_rule_data.to_port,
                        "IpProtocol": security_group_rule_data.protocol,
                        "UserIdGroupPairs": user_id_group_pair_datas,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the security group rule!")

    def delete(self, security_group_rule_data: SecurityGroupRuleData) -> None:
        """
        Deletes an inbound rule based security group identifiers.
        """

        user_id_group_pair_datas = []
        for (
            user_id_group_pair_data
        ) in security_group_rule_data.user_id_group_pairs:
            user_id_group_pair_datas.append(
                user_id_group_pair_data.to_dictionary()
            )

        try:
            self.ec2.revoke_security_group_ingress(
                GroupId=security_group_rule_data.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": security_group_rule_data.from_port,
                        "ToPort": security_group_rule_data.to_port,
                        "IpProtocol": security_group_rule_data.protocol,
                        "UserIdGroupPairs": user_id_group_pair_datas,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the security group rule!")
