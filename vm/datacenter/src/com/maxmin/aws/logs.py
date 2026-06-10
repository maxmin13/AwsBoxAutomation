"""
Created on Mar 18, 2023

@author: vagrant
"""


class Logger(object):
    __log_debug = 1
    __log_warn = 2
    __log_info = 3
    __log_error = 4

    __log_level = __log_warn

    @staticmethod
    def info(message):
        if Logger.__log_level <= Logger.__log_info:
            print(message)

    @staticmethod
    def debug(message):
        if Logger.__log_level <= Logger.__log_debug:
            print(f"DEBUG: {message}")

    @staticmethod
    def warn(message):
        if Logger.__log_level <= Logger.__log_warn:
            print(f"WARN: {message}")

    @staticmethod
    def error(message):
        if Logger.__log_level <= Logger.__log_error:
            print(f"ERROR: {message}")
