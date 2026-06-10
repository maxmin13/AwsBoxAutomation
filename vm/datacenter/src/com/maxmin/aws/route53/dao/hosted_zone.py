"""
Created on Apr 10, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Route53Dao
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.dao.domain.hosted_zone import HostedZoneData


class HostedZoneDao(Route53Dao):
    def load_all(self) -> list:
        """
        Loads all the hosted zones that were created by the current Amazon Web Services account.
        Returns a list of HostedZoneData.
        """
        try:
            response = self.route53.list_hosted_zones_by_name().get(
                "HostedZones"
            )

            hosted_zone_datas = []

            for zone in response:
                hosted_zone_datas.append(HostedZoneData.build(zone))

            return hosted_zone_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the records!")
