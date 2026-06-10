"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.ec2.dao.domain.image import ImageData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.ec2.dao.image import ImageDao
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.service.domain.image import Image


class ImageService(object):
    def load_image(
        self,
        image_nm: str,
    ) -> Image:
        """
        Loads the image with a tag with key 'name' equal to image_nm.
        Returns a Image object.
        """
        if not image_nm:
            raise AwsServiceException("Image name is mandatory!")

        try:
            image_dao = ImageDao()
            image_datas = image_dao.load_all(image_nm)

            if len(image_datas) > 1:
                raise AwsServiceException("Found more than one image!")
            elif len(image_datas) == 0:
                Logger.debug("Image not found!")

                response = None
            else:
                image_data = image_datas[0]

                response = Image()

                response.image_id = image_data.image_id
                response.state = image_data.state
                response.description = image_data.description
                response.snapshot_ids = image_data.snapshot_ids

                for t in image_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the image!")

    def load_image_by_name(
        self,
        image_nm: str,
    ) -> Image:
        """
        Loads the image with by its name.
        Returns a Image object.
        """
        if not image_nm:
            raise AwsServiceException("Image name is mandatory!")

        try:
            image_dao = ImageDao()
            image_datas = image_dao.load_by_name(image_nm)

            if len(image_datas) > 1:
                raise AwsServiceException("Found more than one image!")
            elif len(image_datas) == 0:
                Logger.debug("Image not found!")

                response = None
            else:
                image_data = image_datas[0]

                response = Image()

                response.image_id = image_data.image_id
                response.state = image_data.state
                response.description = image_data.description
                response.snapshot_ids = image_data.snapshot_ids

                for t in image_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the image!")

    def create_image(
        self,
        image_nm: str,
        description: str,
        instance_tag_mn: str,
        tags: list,
    ) -> None:
        """
        Creates a image with a tag with key 'name' equal to image_nm.
        """
        if not image_nm:
            raise AwsServiceException("Image name is mandatory!")

        if not description:
            raise AwsServiceException("Image description is mandatory!")

        if not instance_tag_mn:
            raise AwsServiceException("Instance name is mandatory!")

        try:
            # breaks a circular reference with InstanceService
            from com.maxmin.aws.ec2.service.instance import InstanceService

            instance_service = InstanceService()
            instance = instance_service.load_instance(instance_tag_mn)

            if not instance:
                raise AwsServiceException("Instance not found")

            image = self.load_image(image_nm)

            if image:
                raise AwsServiceException("Image already created!")

            Logger.debug("Creating image ...")

            image_data = ImageData()

            image_data.image_nm = image_nm
            image_data.description = description
            image_data.instance_id = instance.instance_id

            image_data.tags.append(TagData("name", image_nm))
            if tags:
                for tag in tags:
                    image_data.tags.append(TagData(tag.key, tag.value))

            image_dao = ImageDao()
            image_dao.create(image_data)

            Logger.debug("Image successfully created!")
        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the image!")

    def delete_image(
        self,
        image_nm: str,
    ) -> None:
        """
        Deletes the image with a tag with key 'name' equal to image_nm.
        """
        if not image_nm:
            raise AwsServiceException("Image name is mandatory!")

        try:
            image = self.load_image(image_nm)

            if image:
                image_data = ImageData
                image_data.image_id = image.image_id

                image_dao = ImageDao()
                image_dao.delete(image_data)

                Logger.debug("Image deleted!")
            else:
                Logger.debug("Image not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the image!")
