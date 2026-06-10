"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.domain.security_group import (
    SecurityGroupData,
    CidrRuleData,
    SecurityGroupRuleData,
    IpRangeData,
    UserIdGroupPairData,
)
from com.maxmin.aws.ec2.dao.security_group import (
    SecurityGroupDao,
    CidrRuleDao,
    SecurityGroupRuleDao,
)
from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.service.domain.security_group import (
    SecurityGroup,
    CidrRule,
    SecurityGroupRule,
)
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.service.vpc import VpcService


class SecurityGroupService(object):
    def load_security_group(
        self,
        security_group_nm: str,
    ) -> SecurityGroup:
        """
        Loads the security group with a tag with key 'name' equal to security_group_nm.
        Returns a SecurityGroup object.
        """
        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        try:
            security_group_dao = SecurityGroupDao()
            security_group_datas = security_group_dao.load_all(
                security_group_nm
            )

            if len(security_group_datas) > 1:
                raise AwsServiceException(
                    "Found more than one security group!"
                )
            elif len(security_group_datas) == 0:
                Logger.debug("Security group not found!")

                response = None
            else:
                security_group_data = security_group_datas[0]

                vpc_dao = VpcDao()
                vpc_data = vpc_dao.load(security_group_data.vpc_id)

                if not vpc_data:
                    raise AwsServiceException("VPC not found!")

                response = SecurityGroup()
                response.security_group_id = (
                    security_group_data.security_group_id
                )
                response.description = security_group_data.description
                response.vpc_id = vpc_data.vpc_id

                for t in security_group_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the security group!")

    def create_security_group(
        self,
        security_group_nm: str,
        description: str,
        vpc_nm: str,
        tags: list,
    ) -> None:
        """
        Creates a security group with a tag with key 'name' equal to security_group_nm and waits until it's available.
        """

        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not description:
            raise AwsServiceException(
                "Security group description is mandatory!"
            )

        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        try:
            vpc_service = VpcService()
            vpc = vpc_service.load_vpc(vpc_nm)

            if not vpc:
                raise AwsServiceException("VPC not found!")

            security_group = self.load_security_group(security_group_nm)

            if security_group:
                raise AwsServiceException("Security group already created!")

            Logger.debug("Creating Security group ...")

            security_group_data = SecurityGroupData()
            security_group_data.security_group_nm = security_group_nm
            security_group_data.description = description
            security_group_data.vpc_id = vpc.vpc_id

            security_group_data.tags.append(TagData("name", security_group_nm))
            if tags:
                for tag in tags:
                    security_group_data.tags.append(
                        TagData(tag.key, tag.value)
                    )

            security_group_dao = SecurityGroupDao()
            security_group_dao.create(security_group_data)

            Logger.debug("Security group successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the security group!")

    def delete_security_group(
        self,
        security_group_nm: str,
    ) -> None:
        """
        Deletes the security group with a tag with key 'name' equal to security_group_nm.
        """

        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        try:
            security_group = self.load_security_group(security_group_nm)

            if security_group:
                security_group_data = SecurityGroupData
                security_group_data.security_group_id = (
                    security_group.security_group_id
                )

                security_group_dao = SecurityGroupDao()
                security_group_dao.delete(security_group_data)

                Logger.debug("Security group deleted!")
            else:
                Logger.debug("Security group not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the security group!")

    def load_cidr_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_cidr: str,
    ) -> CidrRule:
        """
        Loads an inbound rule based on a CIDR interval (granted_cidr).
        Returns a CidrRule object.
        """
        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_cidr:
            raise AwsServiceException(
                "Rule granted CIDR interval is mandatory!"
            )

        try:
            security_group = self.load_security_group(security_group_nm)

            if not security_group:
                raise AwsServiceException("Security group not found!")

            cidr_rule_dao = CidrRuleDao()
            cidr_rule_datas = cidr_rule_dao.load_all(
                security_group.security_group_id
            )
            cidr_rule_data = self.__get_cidr_rule_data(
                cidr_rule_datas, from_port, to_port, protocol, granted_cidr
            )

            if cidr_rule_data:
                response = CidrRule()
                response.from_port = cidr_rule_data.from_port
                response.to_port = cidr_rule_data.to_port
                response.protocol = cidr_rule_data.protocol
                response.description = cidr_rule_data.ip_ranges[0].description
                response.granted_cidr = cidr_rule_data.ip_ranges[0].cidr_ip
            else:
                Logger.debug("Security group rule not found!")

                response = None

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the security group rule!")

    def create_cidr_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_cidr: str,
        description: str,
    ) -> None:
        """
        Creates an inbound rule based on a CIDR interval (granted_cidr).
        """
        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_cidr:
            raise AwsServiceException(
                "Rule granted CIDR interval is mandatory!"
            )

        if not description:
            raise AwsServiceException("Rule description is mandatory!")

        try:
            security_group = self.load_security_group(security_group_nm)

            if not security_group:
                raise AwsServiceException("Security group not found!")

            cidr_rule = self.load_cidr_rule(
                security_group_nm,
                from_port,
                to_port,
                protocol,
                granted_cidr,
            )

            if cidr_rule:
                raise AwsServiceException(
                    "Security group rule already created!"
                )

            Logger.debug("Creating security group rule ...")

            cidr_rule_data = CidrRuleData()
            cidr_rule_data.security_group_id = security_group.security_group_id
            cidr_rule_data.from_port = from_port
            cidr_rule_data.to_port = to_port
            cidr_rule_data.protocol = protocol

            ip_range_data = IpRangeData()
            ip_range_data.cidr_ip = granted_cidr
            ip_range_data.description = description

            cidr_rule_data.ip_ranges.append(ip_range_data)

            cidr_rule_dao = CidrRuleDao()
            cidr_rule_dao.create(cidr_rule_data)

            Logger.debug("Security group rule successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException(
                "Error creating the security group rule!"
            )

    def delete_cidr_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_cidr: str,
        description: str,
    ) -> None:
        """
        Deletes an inbound rule based on a CIDR interval (granted_cidr).
        """
        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_cidr:
            raise AwsServiceException(
                "Rule granted CIDR interval is mandatory!"
            )

        if not description:
            raise AwsServiceException("Rule description is mandatory!")

        try:
            security_group = self.load_security_group(security_group_nm)

            if not security_group:
                raise AwsServiceException("Security group not found!")

            cidr_rule = self.load_cidr_rule(
                security_group_nm,
                from_port,
                to_port,
                protocol,
                granted_cidr,
            )

            if cidr_rule:
                Logger.debug("Deleting security group rule ...")

                cidr_rule_data = CidrRuleData()
                cidr_rule_data.security_group_id = (
                    security_group.security_group_id
                )
                cidr_rule_data.from_port = cidr_rule.from_port
                cidr_rule_data.to_port = cidr_rule.to_port
                cidr_rule_data.protocol = cidr_rule.protocol

                ip_range_data = IpRangeData()
                ip_range_data.cidr_ip = cidr_rule.granted_cidr
                ip_range_data.description = cidr_rule.description

                cidr_rule_data.ip_ranges.append(ip_range_data)

                cidr_rule_dao = CidrRuleDao()
                cidr_rule_dao.delete(cidr_rule_data)

                Logger.debug("Security group rule successfully deleted!")
            else:
                Logger.debug("Security group rule not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException(
                "Error deleting the security group rule!"
            )

    def load_security_group_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_security_group_nm: str,
    ) -> SecurityGroupRule:
        """
        Loads an inbound rule based security group name (granted_security_group_nm).
        Returns a SecurityGroupRule object.
        """
        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_security_group_nm:
            raise AwsServiceException(
                "Granted security group name is mandatory!"
            )

        try:
            security_group = self.load_security_group(security_group_nm)

            if not security_group:
                Logger.debug("Security group not found!")
                return None

            granted_security_group = self.load_security_group(
                granted_security_group_nm
            )

            if not granted_security_group:
                Logger.debug("Granted security group not found!")
                return None

            security_group_rule_dao = SecurityGroupRuleDao()
            security_group_rule_datas = security_group_rule_dao.load_all(
                security_group.security_group_id
            )
            security_group_rule_data = self.__get_security_group_rule_data(
                security_group_rule_datas,
                from_port,
                to_port,
                protocol,
                granted_security_group.security_group_id,
            )

            if security_group_rule_data:
                response = SecurityGroupRule()
                response.from_port = security_group_rule_data.from_port
                response.to_port = security_group_rule_data.to_port
                response.protocol = security_group_rule_data.protocol
                response.granted_security_group_nm = granted_security_group_nm
                response.description = (
                    security_group_rule_data.user_id_group_pairs[0].description
                )
            else:
                Logger.debug("Security group rule not found!")

                response = None

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the security group rule!")

    def create_security_group_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_security_group_nm: str,
        description: str,
    ) -> None:
        """
        Creates an inbound rule based security group name (granted_security_group_nm).
        """

        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_security_group_nm:
            raise AwsServiceException(
                "Granted security group name is mandatory!"
            )

        if not description:
            raise AwsServiceException("Rule description is mandatory!")

        security_group = self.load_security_group(security_group_nm)

        if not security_group:
            raise AwsServiceException("Security group not found!")

        try:
            granted_security_group = self.load_security_group(
                granted_security_group_nm
            )

            if not granted_security_group:
                raise AwsServiceException("Granted security group not found!")

            security_group_rule = self.load_security_group_rule(
                security_group_nm,
                from_port,
                to_port,
                protocol,
                granted_security_group_nm,
            )

            if security_group_rule:
                raise AwsServiceException(
                    "Security group rule already created!"
                )

            Logger.debug("Creating security group rule ...")

            security_group_rule_data = SecurityGroupRuleData()
            security_group_rule_data.security_group_id = (
                security_group.security_group_id
            )
            security_group_rule_data.from_port = from_port
            security_group_rule_data.to_port = to_port
            security_group_rule_data.protocol = protocol

            user_id_group_pair_data = UserIdGroupPairData()
            user_id_group_pair_data.group_id = (
                granted_security_group.security_group_id
            )
            user_id_group_pair_data.description = description
            security_group_rule_data.user_id_group_pairs.append(
                user_id_group_pair_data
            )

            security_group_rule_dao = SecurityGroupRuleDao()
            security_group_rule_dao.create(security_group_rule_data)

            Logger.debug("Security group successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException(
                "Error creating the security group rule!"
            )

    def delete_security_group_rule(
        self,
        security_group_nm: str,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_security_group_nm: str,
        description: str,
    ) -> None:
        """
        Deletes an inbound rule based security group name (granted_security_group_nm).
        """

        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not from_port:
            raise AwsServiceException("From port rule is mandatory!")

        if not to_port:
            raise AwsServiceException("To port rule is mandatory!")

        if not protocol:
            raise AwsServiceException("Rule protocol is mandatory!")

        if not granted_security_group_nm:
            raise AwsServiceException(
                "Granted security group name is mandatory!"
            )

        if not description:
            raise AwsServiceException("Rule description is mandatory!")

        try:
            security_group = self.load_security_group(security_group_nm)

            if not security_group:
                raise AwsServiceException("Security group not found!")

            granted_security_group = self.load_security_group(
                granted_security_group_nm
            )

            if not granted_security_group:
                raise AwsServiceException("Granted security group not found!")

            security_group_rule = self.load_security_group_rule(
                security_group_nm,
                from_port,
                to_port,
                protocol,
                granted_security_group_nm,
            )

            if security_group_rule:
                Logger.debug("Deleting security group rule ...")

                security_group_rule_data = SecurityGroupRuleData()
                security_group_rule_data.security_group_id = (
                    security_group.security_group_id
                )
                security_group_rule_data.from_port = (
                    security_group_rule.from_port
                )
                security_group_rule_data.to_port = security_group_rule.to_port
                security_group_rule_data.protocol = (
                    security_group_rule.protocol
                )

                user_id_group_pair_data = UserIdGroupPairData()
                user_id_group_pair_data.group_id = (
                    granted_security_group.security_group_id
                )
                user_id_group_pair_data.description = (
                    security_group_rule.description
                )
                security_group_rule_data.user_id_group_pairs.append(
                    user_id_group_pair_data
                )

                security_group_rule_dao = SecurityGroupRuleDao()
                security_group_rule_dao.delete(security_group_rule_data)

                Logger.debug("Security group rule successfully deleted!")
            else:
                Logger.debug("Security group rule not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException(
                "Error deleting the security group rule!"
            )

    def __get_cidr_rule_data(
        self,
        cidr_rule_datas: list,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_cidr: str,
    ):
        cidr_rule_data = None
        for ru in cidr_rule_datas:
            if (
                ru.from_port == from_port
                and ru.to_port == to_port
                and ru.protocol == protocol
            ):
                for ra in ru.ip_ranges:
                    if ra.cidr_ip == granted_cidr:
                        cidr_rule_data = ru
                        break
        return cidr_rule_data

    def __get_security_group_rule_data(
        self,
        security_group_rule_datas: list,
        from_port: int,
        to_port: int,
        protocol: str,
        granted_security_group_id: str,
    ):
        security_group_rule_data = None
        for ru in security_group_rule_datas:
            if (
                ru.from_port == from_port
                and ru.to_port == to_port
                and ru.protocol == protocol
            ):
                for ug in ru.user_id_group_pairs:
                    if ug.group_id == granted_security_group_id:
                        security_group_rule_data = ru
                        break
        return security_group_rule_data
