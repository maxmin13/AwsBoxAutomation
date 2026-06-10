"""
Created on Mar 31, 2024

@author: vagrant
"""
import re

from com.maxmin.aws.exception import AwsServiceException, AwsDaoException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.dao.domain.record import RecordData
from com.maxmin.aws.route53.dao.hosted_zone import HostedZoneDao
from com.maxmin.aws.route53.dao.record import RecordDao
from com.maxmin.aws.route53.service.domain.hosted_zone import HostedZone
from com.maxmin.aws.route53.service.domain.record import Record


class HostedZoneService(object):
    def load_hosted_zone(self, registered_domain: str) -> HostedZone:
        """
        Loads a hosted zones by its name.
        Returns a HostedZone object.
        Keyword arguments:
            registered_domain -- the name of the domain. For public hosted zones, this is the name that you have registered with your DNS registrar.
        """

        if not registered_domain:
            raise AwsServiceException(
                "Hosted zone registered domain is mandatory!"
            )

        try:
            hosted_zone_dao = HostedZoneDao()
            hosted_zone_datas = hosted_zone_dao.load_all()

            # fully qualified domain pattern
            fqdn_pattern = re.compile(registered_domain + "[.]?")

            response = None
            for hosted_zone_data in hosted_zone_datas:
                if fqdn_pattern.match(hosted_zone_data.registered_domain):
                    response = HostedZone()
                    response.hosted_zone_id = hosted_zone_data.hosted_zone_id
                    response.registered_domain = (
                        hosted_zone_data.registered_domain
                    )
                    break

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the hosted zone!")

    def load_record(
        self, record_dns_nm: str, registered_domain: str
    ) -> Record:
        """
        Loads a type A record by its DNS name.
        Returns a Record object.
        Keyword arguments:
            registered_domain -- the name of the domain. For public hosted zones, this is the name that you have registered with your DNS registrar.
        """
        if not record_dns_nm:
            raise AwsServiceException("Record DNS name is mandatory!")

        if not registered_domain:
            raise AwsServiceException("Hosted zone DNS name is mandatory!")

        try:
            hosted_zone = self.load_hosted_zone(registered_domain)

            if not hosted_zone:
                raise AwsServiceException("Hosted zone not found!")

            record_dao = RecordDao()
            record_datas = record_dao.load_all(hosted_zone.hosted_zone_id)

            # fully qualified domain pattern
            fqdn_pattern = re.compile(record_dns_nm + "[.]?")

            response = None
            for record_data in record_datas:
                if "A" == record_data.type and fqdn_pattern.match(
                    record_data.dns_nm
                ):
                    response = Record()
                    response.dns_nm = record_data.dns_nm
                    response.ip_address = record_data.ip_address
                    break

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the record!")

    def create_record(
        self,
        record_dns_nm: str,
        record_ip_address: str,
        registered_domain: str,
    ) -> None:
        """
        Creates a type A record by its DNS name.
        Keyword arguments:
            registered_domain -- the name of the domain. For public hosted zones, this is the name that you have registered with your DNS registrar.
        """

        if not record_dns_nm:
            raise AwsServiceException("Record DNS name is mandatory")

        if not record_ip_address:
            raise AwsServiceException("Record IP address is mandatory!")

        if not registered_domain:
            raise AwsServiceException("Hosted zone DNS name is mandatory!")

        try:
            hosted_zone = self.load_hosted_zone(registered_domain)

            if not hosted_zone:
                raise AwsServiceException("Hosted zone not found!")

            record_dao = RecordDao()
            record_datas = record_dao.load_all(hosted_zone.hosted_zone_id)

            record_data = None
            for r in record_datas:
                if r.dns_nm == record_dns_nm:
                    record_data = r
                    break

            if record_data:
                raise AwsServiceException("Record already created!")

            Logger.debug("Creating DNS record ...")

            record_data = RecordData()
            record_data.ip_address = record_ip_address
            record_data.dns_nm = record_dns_nm
            record_data.hosted_zone_id = hosted_zone.hosted_zone_id

            record_dao.create(record_data)

            Logger.debug("DNS record successfully created!")

        except AwsDaoException as ex:
            Logger.error(str(ex))
        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the DNS record!")
