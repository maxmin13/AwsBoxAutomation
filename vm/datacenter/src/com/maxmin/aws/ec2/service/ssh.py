"""
Created on Mar 20, 2023

@author: vagrant
"""

import os
import stat

from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.ec2.dao.ssh import KeyPairDao

from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.service.domain.ssh import KeyPair
from com.maxmin.aws.ec2.service.domain.tag import Tag
from com.maxmin.aws.ec2.dao.domain.ssh import KeyPairData
from com.maxmin.aws.ec2.dao.domain.tag import TagData


class KeyPairService(object):
    def load_key_pair(
        self,
        key_pair_nm: str,
    ) -> KeyPair:
        """
        Loads the key pair with a tag with key 'name' equal to key_pair_nm.
        Returns a KeyPair object.
        """
        if not key_pair_nm:
            raise AwsServiceException("Key pair name is mandatory!")

        try:
            key_pair_dao = KeyPairDao()
            key_pair_datas = key_pair_dao.load_all(key_pair_nm)

            if len(key_pair_datas) > 1:
                raise AwsServiceException("Found more than one key pair!")
            elif len(key_pair_datas) == 0:
                Logger.debug("Key pair not found!")

                response = None
            else:
                key_pair_data = key_pair_datas[0]

                response = KeyPair()
                response.key_pair_id = key_pair_data.key_pair_id
                response.public_key = key_pair_data.public_key

                for t in key_pair_data.tags:
                    response.tags.append(Tag(t.key, t.value))

            return response

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error loading the key pair!")

    def create_key_pair(self, key_pair_nm: str, tags: list) -> None:
        """
        Creates a key pair on AWS and saves the private key on a local file.
        """

        if not key_pair_nm:
            raise AwsServiceException("Key pair name is mandatory!")

        try:
            key_pair = self.load_key_pair(key_pair_nm)

            if key_pair:
                raise AwsServiceException("Key pair already created!")

            Logger.debug("Creating key pair ...")

            key_pair_data = KeyPairData()
            key_pair_data.key_pair_nm = key_pair_nm

            key_pair_data.tags.append(TagData("name", key_pair_nm))
            if tags:
                for tag in tags:
                    key_pair_data.tags.append(TagData(tag.key, tag.value))

            key_pair_dao = KeyPairDao()
            private_key = key_pair_dao.create(key_pair_data)

            private_key_file = os.path.join(
                ProjectDirectories.ACCESS_DIR, key_pair_nm
            )

            private_key_file_handle = open(private_key_file, "x")
            private_key_file_handle.write(private_key)
            private_key_file_handle.close()

            # Setting the given file to be read by the owner.
            os.chmod(private_key_file, stat.S_IREAD)

            Logger.info(f"Private key file {private_key_file}")
            Logger.debug("Key pair successfully created!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error creating the key pair!")

    def delete_key_pair(
        self,
        key_pair_nm: str,
    ) -> None:
        """
        Deletes a key pair with a tag with key 'name' equal to key_pair_nm.
        """
        if not key_pair_nm:
            raise AwsServiceException("Key pair name is mandatory!")

        try:
            key_pair = self.load_key_pair(key_pair_nm)

            if key_pair:
                key_pair_data = KeyPairData()
                key_pair_data.key_pair_nm = key_pair_nm

                key_pair_dao = KeyPairDao()
                key_pair_dao.delete(key_pair_data)

                Logger.debug("Key pair deleted!")

                private_key_file = os.path.join(
                    ProjectDirectories.ACCESS_DIR, key_pair_nm
                )

                if os.path.isfile(private_key_file) is True:
                    os.remove(private_key_file)

                    Logger.debug("Private key file deleted!")
            else:
                Logger.debug("Key pair not found!")

        except AwsServiceException as ex:
            Logger.error(str(ex))
            raise ex
        except Exception as e:
            Logger.error(str(e))
            raise AwsServiceException("Error deleting the key pair!")
