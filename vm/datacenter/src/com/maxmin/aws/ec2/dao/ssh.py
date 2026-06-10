"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.ec2.dao.domain.ssh import KeyPairData
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class KeyPairDao(Ec2Dao):
    def load(self, key_pair_id: str) -> KeyPairData:
        """
        Loads a key pair by its unique identifier.
        Returns a KeyPairData object.
        """
        try:
            response = self.ec2.describe_key_pairs(
                KeyPairIds=[
                    key_pair_id,
                ],
                IncludePublicKey=True,
            ).get("KeyPairs")[0]

            return KeyPairData.build(response)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the key pair!")

    def load_all(self, key_pair_nm: str) -> list:
        """
        Loads all key pairs with a tag with key 'name' equals key_pair_nm.
        Returns a list of KeyPairData objects.
        """
        try:
            response = self.ec2.describe_key_pairs(
                IncludePublicKey=True,
                Filters=[
                    {
                        "Name": "tag-value",
                        "Values": [
                            key_pair_nm,
                        ],
                    },
                ],
            ).get("KeyPairs")

            key_pair_datas = []

            for key_pair in response:
                key_pair_datas.append(KeyPairData.build(key_pair))

            return key_pair_datas
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error loading the key pairs!")

    def create(self, key_pair_data: KeyPairData) -> str:
        """
        Create a 2048-bit RSA key pair with the specified name.
        Amazon EC2 stores the public key and returns the private key for you
        to save to a file. The private key is returned as an unencrypted PEM
        encoded PKCS#8 private key.
        Throws an error if a key par with the same name exists on AWS.
        Returns the private key to save to a local file.
        """
        try:
            tag_specifications = [{"ResourceType": "key-pair", "Tags": []}]

            for tag in key_pair_data.tags:
                tag_specifications[0]["Tags"].append(tag.to_dictionary())

            response = self.ec2.create_key_pair(
                KeyName=key_pair_data.key_pair_nm,
                KeyType="rsa",
                KeyFormat="pem",
                TagSpecifications=tag_specifications,
            )

            return response.get("KeyMaterial")

        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error creating the key pair!")

    def delete(self, key_pair_data: KeyPairData) -> None:
        """
        Deletes the key pair from AWS.
        """
        try:
            # self.ec2.delete_key_pair(KeyPairId=key_pair_data.key_pair_id)
            self.ec2.delete_key_pair(KeyName=key_pair_data.key_pair_nm)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the key pair!")
