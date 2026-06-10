from com.maxmin.aws.base.domain.base import BaseData
from typing import Self


class RecordData(BaseData):
    def __init__(self):
        super().__init__()
        self.hosted_zone_id = None
        self.dns_nm = None
        self.ip_address = None
        self.type = None

    @classmethod
    def build(cls, record: dict, hosted_zone_id: str) -> Self:
        """
        Builds a RecordData object from its dictionary.
        """
        r = RecordData()
        r.hosted_zone_id = hosted_zone_id
        r.dns_nm = record.get("Name")
        r.ip_address = record.get("ResourceRecords")[0].get("Value")
        r.type = record.get("Type")

        return r
