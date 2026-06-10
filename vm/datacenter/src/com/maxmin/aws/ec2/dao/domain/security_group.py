"""
Created on Mar 7, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class SecurityGroupData(BaseData, BaseTag):

    """
    Class that represents an AWS security group (firewall).
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.security_group_id = None
        self.security_group_nm = None
        self.description = None
        self.vpc_id = None

    @classmethod
    def build(cls, security_group: dict) -> Self:
        """
        Builds a security group object from its dictionary.
        """
        s = SecurityGroupData()
        s.security_group_id = security_group.get("GroupId")
        s.security_group_nm = security_group.get("GroupName")
        s.vpc_id = security_group.get("VpcId")
        s.description = security_group.get("Description")

        tags = security_group.get("Tags")

        if tags:
            for tag in tags:
                s.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return s


class SecurityGroupRuleData(BaseData):

    """
    Class that represents an AWS security group rule based on security group id.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.security_group_id = None
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.user_id_group_pairs = (
            []
        )  # the security groups from which inbound traffic is allowed.

    @classmethod
    def build(cls, security_group_rule: dict, security_group_id: str) -> Self:
        """
        Builds a security group rule object from its dictionary.
        """
        sgp_rule = SecurityGroupRuleData()

        sgp_rule.security_group_id = security_group_id
        sgp_rule.from_port = security_group_rule.get("FromPort")
        sgp_rule.to_port = security_group_rule.get("ToPort")
        sgp_rule.protocol = security_group_rule.get("IpProtocol")

        for user_id_group_pair in security_group_rule.get("UserIdGroupPairs"):
            ugp = UserIdGroupPairData.build(user_id_group_pair)
            sgp_rule.user_id_group_pairs.append(ugp)

        return sgp_rule


class CidrRuleData(BaseData):

    """
    Class that represents an AWS security group rule based on CIDR intervals.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.security_group_id = None
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.ip_ranges = (
            []
        )  # the CIDR blocks from which inbound traffic is allowed.

    @classmethod
    def build(cls, cidr_rule: dict, security_group_id: str) -> Self:
        """
        Builds a security group rule object from its dictionary.
        """
        cr = CidrRuleData()

        cr.security_group_id = security_group_id
        cr.from_port = cidr_rule.get("FromPort")
        cr.to_port = cidr_rule.get("ToPort")
        cr.protocol = cidr_rule.get("IpProtocol")

        for ip_range in cidr_rule.get("IpRanges"):
            ir = IpRangeData.build(ip_range)
            cr.ip_ranges.append(ir)

        return cr


class IpRangeData(BaseData):
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.cidr_ip = None
        self.description = None

    @classmethod
    def build(cls, ip_range: dict) -> Self:
        ir = IpRangeData()
        ir.description = ip_range.get("Description")
        ir.cidr_ip = ip_range.get("CidrIp")

        return ir


class UserIdGroupPairData(BaseData):
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.group_id = None
        self.description = None

    @classmethod
    def build(cls, user_id_group: dict) -> Self:
        ug = UserIdGroupPairData()
        ug.description = user_id_group.get("Description")
        ug.group_id = user_id_group.get("GroupId")

        return ug
