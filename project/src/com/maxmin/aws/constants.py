"""
Created on Mar 28, 2023

@author: vagrant
"""
import configparser
import os
from pathlib import Path
from .paths import project_subdir


class IniFileConstants(object):
    """
    Loads ini files into a configuration object.
    """

    def __init__(self, ini_file):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)


class Ec2Constants(IniFileConstants):
    """
    Loads the ec2.ini file
    """

    def __init__(self):
        super().__init__(ProjectFiles.EC2_CONSTANTS_FILE)

        instance = self.config["INSTANCE"]

        self.device = instance["device"]
        self.volume_size = int(instance["volume_size"])
        self.instance_type = instance["instance_type"]
        self.tenancy = instance["tenancy"]


class ProjectDirectories:
    # Prefer repository-relative paths, fall back to DATACENTER_DIR if set
    REPO_ROOT = project_subdir(".").parent
    ACCESS_DIR = project_subdir("access")
    CONFIG_DIR = project_subdir("config")
    TEMPLATES_DIR = project_subdir("project", "templates")
    CONSTANTS_DIR = project_subdir("project", "constants")
    TEST_DIR = project_subdir("project", "tests")


class ProjectFiles:
    EC2_CONSTANTS_FILE = Path(ProjectDirectories.CONSTANTS_DIR) / "ec2.ini"
    CLOUDINIT_TEMPLATE = Path(ProjectDirectories.TEMPLATES_DIR) / "cloudinit.yml.j2"
