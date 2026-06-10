from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.base.domain.base import BaseData, BaseTag
from typing import Self


class VpcData(BaseData, BaseTag):
    def __init__(self):
        super().__init__()
        self.vpc_id = None
        self.state = None
        self.cidr = None
        self.is_default = False

    @classmethod
    def build(cls, vpc: dict) -> Self:
        """
        Builds a VPC object from its dictionary.
        """
        v = VpcData()
        v.vpc_id = vpc.get("VpcId")
        v.state = vpc.get("State")
        v.cidr = vpc.get("CidrBlock")
        v.is_default = vpc.get("IsDefault")  # boolean

        tags = vpc.get("Tags")

        if tags:
            for tag in tags:
                v.tags.append(TagData(tag.get("Key"), tag.get("Value")))

        return v
