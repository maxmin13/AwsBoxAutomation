from com.maxmin.aws.base.domain.base import BaseData
from typing import Self


class HostedZoneData(BaseData):
    def __init__(self):
        super().__init__()
        self.hosted_zone_id = None
        self.registered_domain = None

    @classmethod
    def build(cls, hosted_zone: dict) -> Self:
        """
        Builds a HostedZoneData object from its dictionary.
        """
        h = HostedZoneData()
        h.hosted_zone_id = hosted_zone.get("Id")
        h.registered_domain = hosted_zone.get("Name")

        return h
