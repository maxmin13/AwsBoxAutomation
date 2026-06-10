"""
Created on Mar 13, 2024

@author: vagrant
"""
from com.maxmin.aws.base.dao.client import Ec2Dao
from com.maxmin.aws.ec2.dao.domain.snapshot import Snapshot
from com.maxmin.aws.exception import AwsDaoException
from com.maxmin.aws.logs import Logger


class SnapshotDao(Ec2Dao):
    """
    Handles an image's snapshot.
    """

    def delete(self, snapshot: Snapshot) -> None:
        """
        Deletes the backup snapshot of an images.
        """

        try:
            self.ec2.delete_snapshot(SnapshotId=snapshot.snapshot_id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsDaoException("Error deleting the image snapshot!")
