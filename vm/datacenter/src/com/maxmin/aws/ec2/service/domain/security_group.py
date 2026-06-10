"""
Created on Mar 7, 2024

@author: vagrant
"""
from com.maxmin.aws.base.domain.base import BaseTag


class SecurityGroup(BaseTag):

    """
    Class that represents an AWS security group (firewall).
    """

    def __init__(self):
        super().__init__()
        self.security_group_id = None
        self.description = None
        self.vpc_id = None


class SecurityGroupRule:

    """
    Class that represents an AWS security group rule that allows access from a security group.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.granted_security_group_nm = (
            None  # the security group from which inbound traffic is allowed.
        )
        self.description = None


class CidrRule:

    """
    Class that represents an AWS security group rule that allows access from a specific CIDR interval.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.granted_cidr = None
        self.description = None
