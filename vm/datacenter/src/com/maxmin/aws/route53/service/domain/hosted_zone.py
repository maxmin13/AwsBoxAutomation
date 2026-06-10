"""
Created on Mar 9, 2024

@author: vagrant
"""


class HostedZone(object):

    """
    Class that represents an AWS hosted zone.
    """

    def __init__(self):
        super().__init__()
        self.hosted_zone_id = None
        self.registered_domain = None
