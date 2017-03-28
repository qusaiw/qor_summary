#!/usr/bin/env python
# Written by Qusai Abu-Obaida

"""The script summarizes QOR data from QOR logs and writes them in an Excel sheet"""

import argparse
import glob


def parse():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
    parser.add_argument('path', nargs='+', help="path1 path2 path3 ....")
    parser.add_argument('-l', '--list', default='list', help='path to list file')
    return parser.parse_args()


class Cell(object):
    def __init__(self, name):
        assert isinstance(name, str)
        self.name = name
        self.attributes = {}
        self.error = ""

    def add_attribute(self, attr, value):
        self.attributes[attr] = value

    def get_attributes(self):
        return self.attributes

    def set_error(self, error):
        assert isinstance(error, str)
        self.error = error


def read_list(list_file):
    assert isinstance(list_file, str)
    files_list = []
    f = open(list_file, 'r')
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        log_files = glob.glob("%s/qor*log")
        if len(log_files) > 1:
            instance = Cell(line)
            instance.set_error("More than one qor log files")
            files_list.append(instance)
            continue
        log_file = log_files[0]
        instance = Cell(line)
        read_log(log_file, instance)
        files_list.append(instance)
        

def read_log(log, cell):
    pass
