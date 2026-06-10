"""
Created on Mar 26, 2023

@author: vagrant
"""
from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.constants import Ec2Constants
from com.maxmin.aws.ec2.dao.domain.instance import InstanceData
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class InstanceDao(Ec2Dao):
    """
    Handles an EC2 instance in AWS.
    """

    def load(self, instance_id: str) -> InstanceData:
        """
        Loads an instance by its unique identifier.
        Returns a InstanceData object.
        """
        try:
            response = (
                self.ec2.describe_instances(
                    InstanceIds=[
                        instance_id,
                    ],
                )
                .get("Reservations")[0]
                .get("Instances")[0]
            )

            return InstanceData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the instance!")

    def load_all(self, instance_nm: str) -> list:
        """
        Loads all instances with a tag with key 'name' equal to instance_nm.
        Returns a list of RouteTableData objects.
        """
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [instance_nm],
                    },
                ],
            ).get("Reservations")

            instances = []
            for reservation in response:
                for instance in reservation.get("Instances"):
                    i = InstanceData.build(instance)
                    instances.append(i)

            return instances
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the instances!")

    def create(self, instance_data: InstanceData) -> None:
        """
        Creates/runs an instance and waits until it's available.
        The instance is assigned a public IP address (not static/elastic).
        Keyword arguments:
            instance_data.cloud_init_data -- cloud-init directives with user data
        """

        ec2_constants = Ec2Constants()
        tag_specifications = [{"ResourceType": "instance", "Tags": []}]

        for tag in instance_data.tags:
            tag_specifications[0]["Tags"].append(tag.to_dictionary())

        security_groups_ids = []
        for security_group_id in instance_data.security_group_ids:
            security_groups_ids.append(security_group_id)

        try:
            identifier = (
                self.ec2.run_instances(
                    BlockDeviceMappings=[
                        {
                            "DeviceName": ec2_constants.device,
                            "Ebs": {
                                "VolumeSize": ec2_constants.volume_size,
                            },
                        },
                    ],
                    ImageId=instance_data.image_id,
                    InstanceType=ec2_constants.instance_type,
                    MaxCount=1,
                    MinCount=1,
                    Placement={
                        "Tenancy": ec2_constants.tenancy,
                    },
                    UserData=instance_data.cloud_init_data,
                    NetworkInterfaces=[
                        {
                            "DeviceIndex": 0,
                            "SubnetId": instance_data.subnet_id,
                            "Groups": security_groups_ids,
                            "PrivateIpAddress": instance_data.private_ip,
                            "AssociatePublicIpAddress": True,
                        },
                    ],
                    TagSpecifications=tag_specifications,
                )
                .get("Instances")[0]
                .get("InstanceId")
            )

            waiter = self.ec2.get_waiter("instance_status_ok")
            waiter.wait(InstanceIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the instance!")

    def delete(self, instance_data: InstanceData) -> None:
        """
        Terminates the instance and waits until successful.
        Terminated instances remain visible after termination (for approximately
        one hour).
        By default, Amazon EC2 deletes all EBS volumes that were attached when
        the instance launched. Volumes attached after instance launch continue
        running.
        """

        try:
            self.ec2.terminate_instances(
                InstanceIds=[
                    instance_data.instance_id,
                ],
            )

            waiter = self.ec2.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[instance_data.instance_id])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the instance!")
