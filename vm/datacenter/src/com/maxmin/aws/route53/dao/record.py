"""
Created on Apr 9, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Route53Dao
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.dao.domain.record import RecordData


class RecordDao(Route53Dao):
    def load_all(self, hosted_zone_id: str) -> list:
        """
        Loads all the DNS records in a hosted zone.
        Returns a list of RecordData objects
        """
        try:
            response = self.route53.list_resource_record_sets(
                HostedZoneId=hosted_zone_id
            ).get("ResourceRecordSets")

            records = []

            for record in response:
                r = RecordData.build(record, hosted_zone_id)
                records.append(r)

            return records
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the records!")

    def create(self, record_data: RecordData) -> None:
        """
        Creates a route53 DNS type A record and waits until it s ready.
        """
        try:
            response = (
                self.route53.change_resource_record_sets(
                    HostedZoneId=record_data.hosted_zone_id,
                    ChangeBatch={
                        "Changes": [
                            {
                                "Action": "CREATE",
                                "ResourceRecordSet": {
                                    "Name": record_data.dns_nm,
                                    "Type": "A",
                                    "TTL": 300,
                                    "ResourceRecords": [
                                        {"Value": record_data.ip_address}
                                    ],
                                },
                            }
                        ]
                    },
                )
                .get("ChangeInfo")
                .get("Id")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the record!")

        waiter = self.route53.get_waiter("resource_record_sets_changed")
        waiter.wait(Id=response)

    def delete(self, record_data: RecordData) -> None:
        """
        Deletes a route53 DNS type A record.
        """
        try:
            self.route53.change_resource_record_sets(
                HostedZoneId=record_data.hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "DELETE",
                            "ResourceRecordSet": {
                                "Name": record_data.dns_nm,
                                "Type": "A",
                                "TTL": 300,
                                "ResourceRecords": [
                                    {"Value": record_data.ip_address}
                                ],
                            },
                        }
                    ]
                },
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the record!")
