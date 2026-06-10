"""
Created on Mar 27, 2023

@author: vagrant
"""
from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.ec2.dao.domain.image import ImageData
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class ImageDao(Ec2Dao):
    """
    Handles an image (AMI) in AWS.
    """

    def load(self, image_id: str) -> ImageData:
        """
        Loads an image (AMI) by its unique ID identifier.
        Returns a ImageData object.
        """
        try:
            response = self.ec2.describe_images(
                ImageIds=[
                    image_id,
                ],
            ).get(
                "Images"
            )[0]

            return ImageData.build(response)
        except Exception as e:
            Logger.debug(str(e))
            raise AwsDaoException("Error loading the images!")

    def load_by_name(self, image_nm: str) -> list:
        """
        Loads an image (AMI) by its name identifier.
        Returns a list of ImageData objects.
        """
        try:
            response = self.ec2.describe_images(
                Filters=[
                    {
                        "Name": "name",
                        "Values": [
                            image_nm,
                        ],
                    },
                ],
            ).get("Images")

            image_datas = []

            for image in response:
                image_datas.append(ImageData.build(image))

            return image_datas
        except Exception as e:
            Logger.debug(str(e))
            raise AwsDaoException("Error loading the images!")

    def load_all(self, image_nm: str) -> list:
        """
        Loads all images with a tag with key 'name' equal to image_nm.
        Returns a list of ImageData objects.
        """
        try:
            response = self.ec2.describe_images(
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [
                            image_nm,
                        ],
                    },
                ],
            ).get("Images")

            image_datas = []

            for image in response:
                image_datas.append(ImageData.build(image))

            return image_datas
        except Exception as e:
            Logger.debug(str(e))
            raise AwsDaoException("Error loading the images!")

    def create(self, image_data: ImageData) -> None:
        """
        Creates an Amazon EBS-backed AMI from an Amazon EBS-backed instance that
        is either running or stopped. Waits until the image is ready.
        """

        tag_specifications = [{"ResourceType": "image", "Tags": []}]

        for tag in image_data.tags:
            tag_specifications[0]["Tags"].append(tag.to_dictionary())

        try:
            identifier = self.ec2.create_image(
                Name=image_data.image_nm,
                Description=image_data.description,
                InstanceId=image_data.instance_id,
                NoReboot=True,
                TagSpecifications=tag_specifications,
            ).get("ImageId")

            waiter = self.ec2.get_waiter("image_available")
            waiter.wait(ImageIds=[identifier])

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the image!")

    def delete(self, image_data: ImageData) -> None:
        """
        Deregisters the specified AMI.
        When you deregister an AMI, it doesn’t affect any instances that you’ve
        already launched from the AMI.
        """

        try:
            self.ec2.deregister_image(ImageId=image_data.image_id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the image!")
