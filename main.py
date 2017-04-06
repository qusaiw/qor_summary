#!/usr/bin/env python
# Written by Qusai Abu-Obaida
"""The script summarizes QOR data from QOR logs and writes them in an Excel sheet
Works for one or more areas
In order to use with more than one area, the list file has to have a line for each cell and each line should
have teh names of the cells in the different areas separated by commas."""

import argparse
import sys
import os
import logging
import glob
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# You can change these two lists, KEY_WORDS should have the names of the parameters as found in the qor log
# ADDITIONAL_PARAMS can have operations involving other params
# For example if KEY_WORDS = ['rise_delay', 'fall_delay']
# then ADDITIONAL_PARAMS can define a new value (average) ["average = (rise_delay + fall_delay) / 2"]
#  and average will appear in your final log
KEY_WORDS = []
ADDITIONAL_PARAMS = []

# Parsing arguments from the user
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
parser.add_argument('path', nargs='+', help="path1 path2 path3 ....")
parser.add_argument('-l', '--list', default='list', help='path to list file', required=True)
parser.add_argument('-o', '--output', default='results.xls')
args = parser.parse_args()
# appends "cells" to the path if not already provided
if os.path.basename(args.path) != 'cells':
    args.path = os.path.join(args.path, 'cells')


class Cell(object):
    def __init__(self, cells):
        self.cells = cells
        self.fail = None

    def open_log(self, cell, path):
        try:
            wildcard = os.path.join(path, cell, "qor*log")
            logs = glob.glob(wildcard)
            if len(logs) != 1:
                raise ValueError(len(logs))
        except ValueError, length:
            if length == 0:
                self.error("No qor file")
                return
            else:
                self.error("Multiple QOR files")
                return
        log = open(logs[0], 'r')
        for line in log:
            if any(word in line for word in KEY_WORDS):
                pass
            else:
                self.error("Corrupted or unrecognized QOR file format")

    def error(self, error):
        self.fail = error

    def __str__(self):
        return ', '.join(self.cells)


class CellOne(Cell):
    """For extraction of one area"""
    def __init__(self, cells):
        Cell.__init__(self, cells)
        self.cell = cells[0]


class CellMulti(Cell):
    """For extraction out of multiple areas"""
    pass


def read_list():
    """
    Reads the list file provided by the user and performs tests to make sure it's the right format and size
    :return: a list of cells presented as instances of the classes CellOne or CellMulti
    """
    cells = []
    try:
        list_file = open(args.list, 'r')
        if os.stat(args.list).st_size == 0:
            raise IOError("Empty list file")
        num_areas = len(args.path)
        # Depending on the number of areas, method is set to the appropriate class
        method = CellOne if num_areas == 1 else CellMulti
        for line in list_file:
            line = line.strip()
            if not line:
                continue
            line = line.split(',')
            if len(line) != num_areas:
                raise ValueError("List file inconsistent with number of paths given")
            cells.append(method(line))
    except IOError, message:
        sys.exit(message)
    except ValueError, message:
        sys.exit(message)
    list_file.close()
    return cells


def main():
    print read_list()[1]
main()
