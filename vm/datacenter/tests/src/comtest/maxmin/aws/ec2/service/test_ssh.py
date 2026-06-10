"""
Created on Mar 28, 2023

@author: vagrant
"""

import os
import stat
import unittest

from moto import mock_aws
from pytest import fail

from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.ec2.service.ssh import KeyPairService
from com.maxmin.aws.exception import AwsServiceException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.utils import TestUtils
from com.maxmin.aws.ec2.service.domain.tag import Tag


class KeypairServiceTestCase(unittest.TestCase):
    PRIVATE_KEY_FILE = f"{ProjectDirectories.ACCESS_DIR}/mykeypair"

    def setUp(self):
        self.test_utils = TestUtils()
        self.key_pair_service = KeyPairService()

    def tearDown(self):
        self.test_utils.delete_private_key_file(
            KeypairServiceTestCase.PRIVATE_KEY_FILE
        )

    @classmethod
    def setUpClass(cls):
        test_utils = TestUtils()
        test_utils.delete_private_key_file(
            KeypairServiceTestCase.PRIVATE_KEY_FILE
        )

    @classmethod
    def tearDownClass(cls):
        test_utils = TestUtils()
        test_utils.delete_private_key_file(
            KeypairServiceTestCase.PRIVATE_KEY_FILE
        )

    @mock_aws
    def test_create_key_pair(self):
        key_pair_tags = []
        key_pair_tags.append(Tag("class", "webservices"))

        # run the test
        self.key_pair_service.create_key_pair("mykeypair", key_pair_tags)

        key_pairs = self.test_utils.describe_key_pairs("mykeypair")

        assert key_pairs[0].get("KeyPairId")
        # assert key_pairs[0].get("PublicKey") # moto lib bug lives the field empty

        assert len(key_pairs[0].get("Tags")) == 2
        assert (
            self.test_utils.get_tag_value("name", key_pairs[0].get("Tags"))
            == "mykeypair"
        )
        assert (
            self.test_utils.get_tag_value("class", key_pairs[0].get("Tags"))
            == "webservices"
        )

        private_key_file = f"{ProjectDirectories.ACCESS_DIR}/mykeypair"

        assert os.path.isfile(private_key_file) is True

        st = os.stat(private_key_file)

        assert bool(st.st_mode & stat.S_IREAD) is True

    @mock_aws
    def test_create_key_pair_twice(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "keypair"))

        self.test_utils.create_key_pair(
            "MYKEYPAIR", key_pair_tags, KeypairServiceTestCase.PRIVATE_KEY_FILE
        )

        key_pair_tags = []
        key_pair_tags.append(Tag("class", "webservices"))

        try:
            self.key_pair_service.create_key_pair("mykeypair", key_pair_tags)

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Error creating the key pair!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_delete_key_pair(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair(
            "mykeypair", key_pair_tags, KeypairServiceTestCase.PRIVATE_KEY_FILE
        )

        # run the test
        self.key_pair_service.delete_key_pair("mykeypair")

        response = self.test_utils.describe_key_pairs("mykeypair")

        assert len(response) == 0

        assert os.path.isfile(KeypairServiceTestCase.PRIVATE_KEY_FILE) is False

    @mock_aws
    def test_delete_not_existing_key_pair(self):
        self.key_pair_service.delete_key_pair("mykeypair")

        # no error expected
        pass

    @mock_aws
    def test_load_key_pair(self):
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
        key_pair = self.key_pair_service.load_key_pair("mykeypair1")

        assert key_pair.key_pair_id == key_pair_id1

        assert len(key_pair.tags) == 2
        assert key_pair.get_tag_value("name") == "mykeypair1"
        assert key_pair.get_tag_value("class") == "webservices"

    @mock_aws
    def test_load_security_group_more_found(self):
        key_pair_tags = []
        key_pair_tags.append(self.test_utils.build_tag("class", "webservices"))
        key_pair_tags.append(self.test_utils.build_tag("name", "mykeypair"))

        self.test_utils.create_key_pair("MYKEYPAIR1", key_pair_tags, None)

        self.test_utils.create_key_pair("MYKEYPAIR2", key_pair_tags, None)

        try:
            # run the test
            self.key_pair_service.load_key_pair("mykeypair")

            fail("An exception should have been thrown!")

        except AwsServiceException as ex:
            assert str(ex) == "Found more than one key pair!"
        except Exception as e:
            Logger.error(str(e))
            fail("An AwsServiceException should have been raised!")

    @mock_aws
    def test_load_key_pair_not_found(self):
        key_pair = self.key_pair_service.load_key_pair("mykeypair")

        assert not key_pair
