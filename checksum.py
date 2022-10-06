#!/usr/bin/env python

"""
Modules to verify files integrity.
Part of the IRIS project.

Author: Carlo Bottai
Copyright (c) 2020 - TU/e and EPFL
License: See the LICENSE file.
Date: 2020-03-24

"""

def md5sum(filename):
    """
    Author: Gertjan van den Burg
    License: MIT
    Source: https://github.com/alan-turing-institute/CSV_Wrangling/blob/master/scripts/data_download.py
    """
    
    import hashlib
    
    blocksize = 65536
    hasher = hashlib.md5()
    with open(filename, 'rb') as fid:
        buf = fid.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fid.read(blocksize)
    return hasher.hexdigest()