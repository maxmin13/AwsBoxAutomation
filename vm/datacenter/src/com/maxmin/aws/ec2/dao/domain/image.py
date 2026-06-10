"""
Created on Mar 6, 2024

@author: vagrant
"""
from typing import Self

from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class ImageData(BaseData, BaseTag):
    """
    Image (AMI) available in AWS.
    """

    def __init__(self):
        super().__init__()
        self.image_id = None
        self.image_nm = None
        self.state = None
        self.description = None
        self.snapshot_ids = []

    @classmethod
    def build(cls, image: dict) -> Self:
        """
        Builds an instance object from its dictionary.
        """

        i = ImageData()
        i.image_id = image.get("ImageId")
        i.image_nm = image.get("Name")
        i.state = image.get("State")
        i.description = image.get("Description")

        for device in image.get("BlockDeviceMappings"):
            i.snapshot_ids.append(device.get("Ebs").get("SnapshotId"))

        tags = image.get("Tags")

        if tags:
            for tag in tags:
                i.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return i
