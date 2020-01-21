#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (C)Eduardo Ribeiro - 1600820
import logging
import os
from setup_config import config_parser

log_file = config_parser.get('log', 'log_file')

logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(levelname)s: %(asctime)s %(message)s')

logger = logging.getLogger()
