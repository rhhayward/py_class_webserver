#!/usr/bin/env python3
from class_webserver import class_webserver

class no_prefix:
    def __init__(self):
        pass
    def get_status(self):
        return "no_prefix"


class with_prefix:
    def __init__(self):
        self.prefix = '/with/prefix'
        pass
    def get_status(self):
        return "with_prefix"

class with_params:
    def __init__(self):
        pass
    def get_with_params(self, param1=None, param2=None):
        return "with_params:param1={}:param2={}".format(param1, param2)


class_webserver([
        no_prefix(),
        with_prefix(),
        with_params(),
    ])
