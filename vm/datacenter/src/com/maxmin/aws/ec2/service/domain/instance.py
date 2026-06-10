"""
Created on Mar 6, 2024

@author: vagrant
"""

from com.maxmin.aws.base.domain.base import BaseTag


class Instance(BaseTag):
    """
    Instance available in AWS.
    """

    def __init__(self):
        super().__init__()

        self.instance_id = None
        self.state = None
        self.az = None
        self.private_ip = None
        self.public_ip = None
        self.instance_profile = None
        self.subnet_id = None
        self.image_id = None
        self.vpc_id = None
        self.cloud_init_data = None
        self.security_group_ids = []
