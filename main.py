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
        self.attributes = []
        # expected to hold a list of CSV lines to write in order onto the final output
        self.content = []
        self.pins = []
        self.fail = None

    def open_log(self, cell, path):
        try:
            # pattern for QOR file
            wildcard = os.path.join(path, cell, "qor*log")
            logs = glob.glob(wildcard)
            if len(logs) != 1:
                raise ValueError(len(logs))
        except ValueError, length:
            if length == 0:
                self.error("No qor file for %s" % cell)
                return
            else:
                self.error("Multiple QOR files in %s" % cell)
                return
        log = open(logs[0], 'r')
        lines = log.readlines()
        # Flag for finding any keyword in the file.
        found_attributes = False
        for line_num, line in enumerate(lines):
            if any(word in line for word in KEY_WORDS):
                found_attributes = True
                line = line.split(',')
                indices = []
                for n, word in line:
                    if word in KEY_WORDS:
                        indices.append(n)
                        self.attributes.append(word)
            if found_attributes and "END Simulation" not in line:
                # flipflops don't have a pin name in the QOR file
                pin_name = None
                line = line.split(',')
                # the first element contains the <cell_name>_PIN_<pin_name>
                # so these next lines are for unpacking it and modifying line[0] to have just the first value
                to_unpack = line[0].split(" ")
                line[0] = to_unpack[1]
                to_unpack = to_unpack[0].split('_PIN_')
                if len(to_unpack) == 2:
                    pin_name = to_unpack[1]
                elif len(to_unpack) > 2:
                    self.error("Unrecognized formal in %s" % cell)
                    return
                pin_name = cell if not pin_name else pin_name
                self.pins.append(pin_name)
                new_values = []
                for value in line:
                    new_values.append(value)
                self.content.append(new_values)
        if not found_attributes:
            self.error("Corrupted or unrecognized QOR file format for %s" % cell)
            return

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
