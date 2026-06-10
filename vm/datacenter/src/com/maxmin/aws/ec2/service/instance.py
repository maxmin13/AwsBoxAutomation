"""
Created on Mar 20, 2023

@author: vagrant
"""
import base64
import crypt

import jinja2

from com.maxmin.aws.ec2.dao.domain.instance import InstanceData
from com.maxmin.aws.ec2.dao.instance import InstanceDao
from com.maxmin.aws.ec2.dao.vpc import VpcDao
from com.maxmin.aws.ec2.service.domain.instance import Instance
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.service.security_group import SecurityGroupService
from com.maxmin.aws.ec2.service.subnet import SubnetService
from com.maxmin.aws.ec2.service.vpc import VpcService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.constants import ProjectFiles
from com.maxmin.aws.ec2.service.ssh import KeyPairService
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class InstanceService(object):
    def load_instance(
        self,
        instance_nm: str,
    ) -> Instance:
        """
        Loads the instance with a tag with key 'name' equal to instance_nm.
        Returns an Instance object.
        """
        if not instance_nm:
            raise AwsServiceException("Instance name is mandatory!")

        try:
            instance_dao = InstanceDao()
            instance_datas = instance_dao.load_all(instance_nm)

            active_instance_datas = []
            for instance_data in instance_datas:
                if (
                    instance_data.state == "pending"
                    or instance_data.state == "running"
                ):
                    active_instance_datas.append(instance_data)

            if len(active_instance_datas) > 1:
                raise AwsServiceException("Found more than one instance!")
            elif len(active_instance_datas) == 0:
                Logger.debug("Instance not found!")

                response = None
            else:
                instance_data = active_instance_datas[0]

                vpc_dao = VpcDao()
                vpc_data = vpc_dao.load(instance_data.vpc_id)

                if not vpc_data:
                    raise AwsServiceException("VPC not found!")

                response = Instance()
                response.instance_id = instance_data.instance_id
                response.state = instance_data.state
                response.az = instance_data.az
                response.private_ip = instance_data.private_ip
                response.public_ip = instance_data.public_ip
                response.instance_profile = instance_data.instance_profile
                response.subnet_id = instance_data.subnet_id
                response.image_id = instance_data.image_id
                response.vpc_id = vpc_data.vpc_id = instance_data.vpc_id
                response.security_group_ids = instance_data.security_group_ids

                for t in instance_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the instance!")

    def create_instance(
        self,
        instance_nm: str,
        private_ip: str,
        image_nm: str,
        security_group_nm: str,
        subnet_nm: str,
        vpc_nm: str,
        user_nm: str,
        user_pwd: str,
        host_nm: str,
        key_pair_nm: str,
        tags: list,
    ) -> None:
        """
        Creates an instance for the specified VPC with a tag with key 'name' equal to instance_nm.
        """
        if not instance_nm:
            raise AwsServiceException("Instance name is mandatory!")

        if not private_ip:
            raise AwsServiceException("Instance private IP is mandatory!")

        if not image_nm:
            raise AwsServiceException("Parent image name is mandatory!")

        if not security_group_nm:
            raise AwsServiceException("Security group name is mandatory!")

        if not subnet_nm:
            raise AwsServiceException("Subnet name is mandatory!")

        if not vpc_nm:
            raise AwsServiceException("VPC name is mandatory!")

        if not user_nm:
            raise AwsServiceException("Instance user name is mandatory!")

        if not user_pwd:
            raise AwsServiceException("Instance user password is mandatory!")

        if not host_nm:
            raise AwsServiceException("Instance host name is mandatory!")

        if not key_pair_nm:
            raise AwsServiceException("Key pair name is mandatory!")

        try:
            # breaks a circular reference with ImageService
            from com.maxmin.aws.ec2.service.image import ImageService

            image_service = ImageService()
            image = image_service.load_image_by_name(image_nm)

            if not image:
                raise AwsServiceException("Parent image not found!")

            security_group_service = SecurityGroupService()
            security_group = security_group_service.load_security_group(
                security_group_nm
            )

            if not security_group:
                raise AwsServiceException("Security group not found!")

            subnet_service = SubnetService()
            subnet = subnet_service.load_subnet(subnet_nm)

            if not subnet:
                raise AwsServiceException("Subnet not found!")

            vpc_service = VpcService()
            vpc = vpc_service.load_vpc(vpc_nm)

            if not vpc:
                raise AwsServiceException("VPC not found!")

            instance = self.load_instance(instance_nm)

            if instance and (
                instance.state == "pending" or instance.state == "running"
            ):
                raise AwsServiceException("Instance already created!")

            environment = jinja2.Environment()
            with open(ProjectFiles.CLOUDINIT_TEMPLATE, "r") as file:
                cloudinit_template = file.read()

            template = environment.from_string(cloudinit_template)

            salt = crypt.mksalt(method=crypt.METHOD_SHA512, rounds=4096)
            hashed_pwd = crypt.crypt(user_pwd, salt)

            keypair_service = KeyPairService()
            keypair = keypair_service.load_key_pair(key_pair_nm)

            if not keypair:
                raise AwsServiceException("Error loading the key pair!")

            cloudinit_data = {
                "username": user_nm,
                "hostname": host_nm,
                "hashed_password": hashed_pwd,
                "public_key": keypair.public_key,
            }

            cloudinit_config = template.render(cloudinit_data)
            cloudinit_data_b64 = base64.b64encode(
                bytes(str(cloudinit_config), "utf-8")
            )

            Logger.debug("Creating instance ...")

            instance_data = InstanceData()
            instance_data.image_id = image.image_id
            instance_data.security_group_ids.append(
                security_group.security_group_id
            )
            instance_data.subnet_id = subnet.subnet_id
            instance_data.private_ip = private_ip
            instance_data.cloud_init_data = cloudinit_data_b64

            instance_data.tags.append(TagData("name", instance_nm))
            if tags:
                for tag in tags:
                    instance_data.tags.append(TagData(tag.key, tag.value))

            instance_dao = InstanceDao()
            instance_dao.create(instance_data)

            Logger.debug("Instance successfully created!")
        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the instance!")

    def terminate_instance(
        self,
        instance_nm: str,
    ) -> None:
        """
        Deletes the instance with a tag with key 'name' equal to instance_nm.
        """
        if not instance_nm:
            raise AwsServiceException("Instance name is mandatory!")

        try:
            instance = self.load_instance(instance_nm)

            if instance and (
                instance.state == "pending" or instance.state == "running"
            ):
                instance_data = InstanceData
                instance_data.instance_id = instance.instance_id

                instance_dao = InstanceDao()
                instance_dao.delete(instance_data)

                Logger.debug("Instance deleted!")
            else:
                Logger.debug("Instance not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the instance!")
