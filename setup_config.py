#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820
import configparser
import os

# configure logging
config_parser = configparser.RawConfigParser()

dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(dir, 'settings.ini')

config_parser.read(config_file_path)
