"""
Created on Mar 28, 2023

@author: vagrant
"""

import unittest

from pytest import fail

from com.maxmin.aws.ec2.dao.ssh import KeyPairDao
from com.maxmin.aws.ec2.dao.domain.ssh import KeyPairData
from com.maxmin.aws.ec2.dao.domain.tag import TagData
from com.maxmin.aws.exception import AwsDaoException
from moto import mock_aws
from comtest.maxmin.aws.utils import TestUtils


class KeyPairDaoTestCase(unittest.TestCase):
    def setUp(self):
        self.test_utils = TestUtils()
        self.key_pair_dao = KeyPairDao()

    @mock_aws
    def test_create_key_pair(self):
        key_pair_tag_datas = []
        key_pair_tag_datas.append(TagData("class", "webservices"))
        key_pair_tag_datas.append(TagData("name", "mykeypair"))

        key_pair_data = KeyPairData()
        key_pair_data.key_pair_nm = "MYKEYPAIR"
        key_pair_data.tags = key_pair_tag_datas

        # run the test
        private_key = self.key_pair_dao.create(key_pair_data)

        assert private_key

        response = self.test_utils.describe_key_pairs("mykeypair")

        assert response[0].get("KeyPairId")
        assert response[0].get("KeyName") == "MYKEYPAIR"

        # public_key field is not returned with moto
        # public_key = response[0].get("PublicKey")
        # assert public_key

        assert len(response[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", response[0].get("Tags"))
            == "mykeypair"
        )
        assert (
            self.test_utils.get_tag_value("class", response[0].get("Tags"))
            == "webservices"
        )

    @mock_aws
    def test_create_key_pair_twice_same_tag_name(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIR1", key_pair_tags, None)

        key_pair_tag_datas = []
        key_pair_tag_datas.append(TagData("class", "webservices"))
        key_pair_tag_datas.append(TagData("name", "mykeypair"))

        key_pair_data = KeyPairData()
        key_pair_data.key_pair_nm = "MYKEYPAIR2"
        key_pair_data.tags = key_pair_tag_datas

        # run the test
        self.key_pair_dao.create(key_pair_data)

        response = self.test_utils.describe_key_pairs("mykeypair")

        assert len(response) == 2

    @mock_aws
    def test_create_key_pair_twice_same_name(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair1"))

        self.test_utils.create_key_pair("MYKEYPAIR", key_pair_tags, None)

        key_pair_tag_datas = []
        key_pair_tag_datas.append(TagData("class", "webservices"))
        key_pair_tag_datas.append(TagData("name", "mykeypair2"))

        key_pair_data = KeyPairData()
        key_pair_data.key_pair_nm = "MYKEYPAIR"
        key_pair_data.tags = key_pair_tag_datas

        try:
            # run the test
            self.key_pair_dao.create(key_pair_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error creating the key pair!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_delete_keypair(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIR", key_pair_tags, None)

        key_pair_data = KeyPairData()
        key_pair_data.key_pair_nm = "MYKEYPAIR"

        # run the test
        self.key_pair_dao.delete(key_pair_data)

        response = self.test_utils.describe_key_pairs("mykeypair")

        assert len(response) == 0

    @mock_aws
    def test_delete_not_existing_keypair(self):
        try:
            key_pair_data = KeyPairData()
            key_pair_data.key_pair_id = "1234"

            self.key_pair_dao.delete(key_pair_data)

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error deleting the key pair!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_key_pair(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        key_pair_id = self.test_utils.create_key_pair(
            "MYKEYPAIR", key_pair_tags, None
        ).get("KeyPairId")

        # run the test
        key_pair_data = self.key_pair_dao.load(key_pair_id)

        assert key_pair_data.key_pair_id == key_pair_id
        assert key_pair_data.key_pair_nm == "MYKEYPAIR"
        # assert key_pair.public_key

        assert len(key_pair_data.tags) == 2
        assert key_pair_data.get_tag_value("name") == "mykeypair"
        assert key_pair_data.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_key_pair_not_found(self):
        try:
            self.key_pair_dao.load("1234")

            fail("ERROR: an exception should have been thrown!")

        except AwsDaoException as e:
            assert str(e) == "Error loading the key pair!"
        except Exception:
            fail("ERROR: an AwsDaoException should have been raised!")

    @mock_aws
    def test_load_all_key_pairs_by_tag_name(self):
        key_pair_tags1 = []
        key_pair_tags1.append(
            self.test_utils.build_tag("class", "webservices")
        )
        key_pair_tags1.append(self.test_utils.build_tag("name", "mykeypair1"))

        key_pair_id1 = self.test_utils.create_key_pair(
            "MYKEYPAIR1", key_pair_tags1, None
        ).get("KeyPairId")

        key_pair_tags2 = []
        key_pair_tags2.append(
            self.test_utils.build_tag("class", "webservices")
        )
        key_pair_tags2.append(self.test_utils.build_tag("name", "mykeypair2"))

        self.test_utils.create_key_pair("MYKEYPAIR2", key_pair_tags2, None)

        # run the test
        key_pair_datas = self.key_pair_dao.load_all("mykeypair1")

        assert len(key_pair_datas) == 1

        assert key_pair_datas[0].key_pair_id == key_pair_id1
        assert key_pair_datas[0].key_pair_nm == "MYKEYPAIR1"
        # assert key_pairs[0].public_key

        assert len(key_pair_datas[0].tags) == 2
        assert key_pair_datas[0].get_tag_value("name") == "mykeypair1"
        assert key_pair_datas[0].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_key_pairs_by_tag_name_more_found(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        key_pair_id1 = self.test_utils.create_key_pair(
            "MYKEYPAIR1", key_pair_tags, None
        ).get("KeyPairId")

        key_pair_id2 = self.test_utils.create_key_pair(
            "MYKEYPAIR2", key_pair_tags, None
        ).get("KeyPairId")

        # run the test
        key_pair_datas = self.key_pair_dao.load_all("mykeypair")

        assert len(key_pair_datas) == 2

        assert key_pair_datas[0].key_pair_id == key_pair_id1
        assert key_pair_datas[0].key_pair_nm == "MYKEYPAIR1"
        # assert key_pairs[0].public_key

        assert len(key_pair_datas[0].tags) == 2
        assert key_pair_datas[0].get_tag_value("name") == "mykeypair"
        assert key_pair_datas[0].get_tag_value("class") == "webservices"

        assert key_pair_datas[1].key_pair_id == key_pair_id2
        assert key_pair_datas[1].key_pair_nm == "MYKEYPAIR2"
        # assert key_pairs[1].public_key

        assert len(key_pair_datas[1].tags) == 2
        assert key_pair_datas[1].get_tag_value("name") == "mykeypair"
        assert key_pair_datas[1].get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_all_key_pairs_by_tag_name_not_found(self):
        key_pair_datas = self.key_pair_dao.load_all("mykeypair")

        assert len(key_pair_datas) == 0
