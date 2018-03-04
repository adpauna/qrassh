# Copyright (c) 2009-2014 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

"""
This module contains ...
"""

from __future__ import division, absolute_import

import configparser

def readConfigFile(cfgfile):
    """
    Read config files and return ConfigParser object

    @param cfgfile: filename or array of filenames
    @return: ConfigParser object
    """
    parser = configparser.ConfigParser()
    parser.read(cfgfile)
    return parser

CONFIG = readConfigFile(("irassh.cfg.dist", "etc/irassh.cfg", "irassh.cfg"))

