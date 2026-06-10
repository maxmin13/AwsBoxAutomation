"""
Created on Mar 20, 2023

@author: vagrant
"""

import boto3


class Ec2Dao(object):
    def __init__(self):
        self.ec2 = boto3.client("ec2")


class Route53Dao(object):
    def __init__(self):
        self.route53 = boto3.client("route53")
