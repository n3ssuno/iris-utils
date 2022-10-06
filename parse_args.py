#!/usr/bin/env python

"""
Modules to parse the arguments passed through a Makefile or a terminal.
Part of the IRIS project.

Author: Carlo Bottai
Copyright (c) 2020 - TU/e and EPFL
License: See the LICENSE file.
Date: 2020-03-24

"""


import argparse


def parse_io():
    parser = argparse.ArgumentParser('Names Fixer')
    
    parser.add_argument(
        '-i', '--input', 
        help = 'input file', 
        required = False
    )
    parser.add_argument(
        '-I', '--input_list', 
        help = 'list of input files', 
        required = False, 
        nargs = '+'
    )
    parser.add_argument(
        '-o', '--output', 
        help = 'output file or directory', 
        required = False
    )
    parser.add_argument(
        '-O', '--n_output', 
        help = 'number of output files (default: 1)', 
        default = 1, 
        type = int, 
        required = False
    )
    
    return parser.parse_args()
