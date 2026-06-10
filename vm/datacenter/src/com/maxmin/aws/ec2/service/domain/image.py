"""
Created on Mar 6, 2024

@author: vagrant
"""

from com.maxmin.aws.base.domain.base import BaseTag


class Image(BaseTag):
    """
    Image (AMI) available in AWS.
    """

    def __init__(self):
        super().__init__()
        self.image_id = None
        self.state = None
        self.description = None
        self.snapshot_ids = []
