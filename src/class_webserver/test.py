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

class_webserver([
        with_prefix(),
        no_prefix(),
    ])
