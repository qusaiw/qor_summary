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
KEY_WORDS = ["rise_delay", "fall_delay", "avg_delay", "cud_delay_fr", "cud_delay_rf", "cud_avg_delay",
             "rise_fall_perc_diff"]

# Parsing arguments from the user

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
parser.add_argument('path', nargs='+', help="path1 path2 path3 ....")
parser.add_argument('-l', '--list', default='list', help='path to list file', required=True)
parser.add_argument('-o', '--output', default='results.csv')
args = parser.parse_args()
# appends "cells" to the path if not already provided
new_paths = []
for i in args.path:
    if os.path.basename(i) != 'cells':
        new_paths.append(os.path.join(i, 'cells'))
    else:
        new_paths.append(i)
args.path = new_paths


class Cell(object):
    def __init__(self, cells):
        self.cells = cells
        self.attributes = []
        # expected to hold a list of CSV lines to write in order onto the final output
        self.content = []
        self.pins = []
        self.fail = None

    def open_log(self, cell, path):
        indices = []
        try:
            # pattern for QOR file
            wildcard = os.path.join(path, cell, "qor*log")
            logs = glob.glob(wildcard)[:]
            if len(logs) != 1:
                raise ValueError(len(logs))

        except ValueError, length:
            if str(length) == "0":
                self.error("No qor file for %s" % cell)
                return
            else:
                self.error("Multiple QOR files in %s" % cell)
                return
        log = open(logs[0], 'r')
        lines = log.readlines()
        # Flag for finding any keyword in the file.
        found_attributes = False
        pin_num = 0
        for line_num, line in enumerate(lines):
            if len(line.strip()) == 0:
                continue
            if any(word in line for word in KEY_WORDS):
                if self.attributes:
                    continue
                found_attributes = True
                line = line.split(',')
                indices = []
                for n, word in enumerate(line):
                    if word in KEY_WORDS:
                        indices.append(n)
                        self.attributes.append(word)
                continue
            if found_attributes and "END Simulation" not in line:
                pin_num += 1
                # flipflops don't have a pin name in the QOR file
                pin_name = None
                line = line.split(',')
                # the first element contains the <cell_name>_PIN_<pin_name>
                # so these next lines are for unpacking it and modifying line[0] to have just the first value
                to_unpack = line[0].split("\t")
                line[0] = to_unpack[1]
                to_unpack = to_unpack[0].split('_PIN_')
                if len(to_unpack) == 2:
                    pin_name = to_unpack[1]
                elif len(to_unpack) > 2:
                    self.error("Unrecognized format in %s" % cell)
                    return
                pin_name = cell if not pin_name else pin_name
                self.pins.append(pin_name)
                if pin_num == 1:
                    new_values = [cell, pin_name]
                else:
                    new_values = ["", pin_name]
                for index in indices:
                    new_values.append(line[index])
                new_values = ",".join(new_values)
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
        self.open_log(self.cell, args.path[0])


class CellMulti(Cell):
    """For extraction out of multiple areas"""

    def __init__(self, cells):
        Cell.__init__(self, cells)
        self.all_contents = []
        self.pins_check = []
        for n, cell in enumerate(cells):
            cell = cell.strip()
            self.attributes = []
            self.pins = []
            self.open_log(cell, args.path[n])
            self.pins_check.append(self.pins)
            self.all_contents.append(self.content)
            self.content = []
        self.content = self.all_contents[:]
        if not all(self.pins_check[0] == another_pin for another_pin in self.pins_check) and not self.fail:
            self.error("Mismatched pins for %s" % str(self.cells))
        if not self.fail and all(len(self.content[0]) == len(another) for another in self.content):
            self.content = zip(*self.content)
            for n in range(len(self.content)):
                self.content[n] = ",,,".join(self.content[n])


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
            line = [cell.strip() for cell in line]
            cells.append(method(line))
    except IOError, message:
        sys.exit(message)
    except ValueError, message:
        sys.exit(message)
    list_file.close()
    return cells


def write_attributes(attributes, paths):
    """
    Writes the attributes line as many times as there are paths
    :param attributes: list containing the attributes of the cell ex: ["rise_delay", "fall_delay", "average"]
    :param paths: int representing the number of areas given
    :return: a comma separated string to write in the CSV file
    """
    line = []
    for _ in range(paths):
        line.extend(["", ""] + attributes + ["", ""])
    return ",".join(line)


def write_csv(cells):
    """
    Writes the CSV file using with the name provided by the user or the default "results.csv"
    :param cells: a list of cell instances from the children of the class "Cell"
    """
    csv_file = []
    attributes = None
    for cell in cells:
        if cell.fail:
            print cell.fail
        if cell.attributes and not attributes:
            attributes = cell.attributes[:]
            csv_file.append(write_attributes(attributes, len(args.path)))
        if attributes and cell.attributes and (attributes != cell.attributes):
            attributes = cell.attributes[:]
            csv_file.append(write_attributes(attributes, len(args.path)))
        if cell.fail:
            csv_file.append(str(cell.fail))
        else:
            csv_file.extend(cell.content)
        csv_file.append("")
    out_file = open(args.output, 'w+')
    for line in csv_file:
        out_file.write(line + "\n")


def main():
    cells = read_list()
    write_csv(cells)

if __name__ == '__main__':
    main()
