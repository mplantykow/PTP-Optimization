#!/usr/bin/python3
# Copyright (c) 2021 Intel
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html
"""Script for parsing and plotting linuxptp tools logs"""

import re
import argparse
import os
import sys
import warnings
import numpy as np
from matplotlib import pyplot as plt


def parse_ptp4l_out(line):
    """Parse ptp4l logs"""
    # journalctl -u ptp4l.service
    # pattern = r'^(.+)ptp4l\[[0-9]+\]: \[(.+)\] master offset\s+(-?[0-9]+)'\
    #           r' s([0123]) freq\s+([+-]\d+) path delay\s+(-?\d+)$'
    # standard ptp4l.log
    pattern = r'^ptp4l\[(\d+).(\d+)\]: master offset\s+(-?[0-9]+) s([0123])'\
              r' freq\s+([+-]\d+) path delay\s+(-?\d+)$'
    # https://regexr.com/

    # Regex search
    res = re.search(pattern, line)
    # if pattern was matched
    if res:
        kernel_sec    = int(float(res.group(1)))
        kernel_nsec   = int(res.group(2)) * 1000000
        master_offset = int(res.group(3))
        state         = int(res.group(4))
        freq          = int(res.group(5))
        path_delay    = int(res.group(6))

        row = [kernel_sec, kernel_nsec, state, master_offset, freq, path_delay]
    else:
        row = []

    return row


def parse_phc2sys_out(line):
    """Parse phc2sys logs"""
    # journalctl -u ptp4l.service
    # pattern = r'^(.+)ptp4l\[[0-9]+\]: \[(.+)\] master offset\s+(-?[0-9]+)'\
    #           r's([012]) freq\s+([+-]\d+) path delay\s+(-?\d+)$'
    # standard phc2sys.log:
    # phc2sys[689991.253]: CLOCK_REALTIME phc offset        33 s2 freq   -5355 delay    603
    pattern = r'^phc2sys\[(\d+).(\d+)\]:\s+(\S+)\s+(\S+) offset\s+(-?[0-9]+)'\
              r' s([0123]) freq\s+([+-]\d+) delay\s+(-?\d+)'
    # https://regexr.com/

    # Regex search
    res = re.search(pattern, line)
    # if pattern was matched
    if res:
        kernel_sec    = int(float(res.group(1)))
        kernel_nsec   = int(res.group(2)) * 1000000
        master_offset = int(res.group(5))
        state         = int(res.group(6))
        freq          = int(res.group(7))
        path_delay    = int(res.group(8))

        row = [kernel_sec, kernel_nsec, state, master_offset, freq, path_delay]
    else:
        row = []

    return row


def filter_stable(arr):
    """Filter output to stable results only"""
    stable = []

    for element in arr:
        if element[2] == 2 or element[2] == 3:
            stable.append(True)
        else:
            stable.append(False)

    return arr[stable]


def plot(result_array):
    """Plot logged data to a file"""
    warnings.filterwarnings('ignore')
    figure, axes = plt.subplots(nrows=3, ncols=1)

    result_array = filter_stable(result_array)

    #master_offset
    axes[0].set_title('Master offset')
    axes[0].plot(result_array[:,0],result_array[:,3])
    axes[0].set(xlabel='[s]', ylabel='[ns]')
    axes[0].set_xlim([0, max(result_array[:,0])])
    #axes[0].set_yscale('symlog')
    axes[0].spines['bottom'].set_position('zero')
    #freq
    axes[1].set_title('Frequency')
    axes[1].plot(result_array[:,0],result_array[:,4])
    axes[1].set(xlabel='[s]', ylabel='[ppb]')
    axes[1].set_xlim([0, max(result_array[:,0])])
    axes[1].spines['bottom'].set_position('zero')
    #path_delay
    axes[2].set_title('Path delay')
    axes[2].plot(result_array[:,0],result_array[:,5])
    axes[2].set(xlabel='[s]', ylabel='[ns]')
    axes[2].set_xlim([0, max(result_array[:,0])])

    #print only outer labels
    for ax in axes.flat:
        ax.label_outer()

    figure.tight_layout()
    #plt.show()
    figure.set_figheight(10)
    figure.set_figwidth(15)
    plt.savefig("test.png")

    # the histogram of the data
    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html
    #plt.hist(array[:,3], 30, density=1, facecolor='g', alpha=0.75)
    #
    #plt.ylabel('Probability')
    #plt.title('Histogram of offset')
    #plt.axis([-10, 10, 0, 0.3])
    #plt.grid(True)
    #plt.show()


def parse_file(filename, normalize=0):
    """Parse log file"""
    # Using readlines()
    with open(filename, 'r', encoding="utf-8") as file1:
        lines = file1.readlines()

    if lines:
        if lines[0].startswith("phc2sys"):
            file_type = 1
        else:
            file_type = 0
    else:
        #Handle the case where Lines is empty
        print("The file is empty or Linex[0] does not exist")
        sys.exit()

    for line in lines:
        if file_type:
            vector = parse_phc2sys_out(line)
        else:
            vector = parse_ptp4l_out(line)

        if vector:
            try:
                result
            except NameError:
                result = np.array(vector)
            else:
                result = np.vstack([result, vector])
        else:
            continue

        # extract state
        state = vector[2]
        if state == 0:
            try:
                start_time
            except NameError:
                start_time = vector[0]
            continue

        if state == 1:
            continue

        if state in (2,3):
            try:
                start_delay
            except NameError:
                start_delay = vector[0] - start_time

    if normalize:
        result = result - [start_time, 0, 0, 0 ,0 ,0]

    return result


def unit_test():
    """Run unit-test for parsing functions"""
    test_string = 'ptp4l[145810.411]: master offset        -24' \
                  ' s2 freq     -27 path delay       642'
    print("parse_ptp4l_out:")
    result = parse_ptp4l_out(test_string)
    print(test_string)
    print(result)

    test_string = 'phc2sys[689991.253]: CLOCK_REALTIME phc offset        33 s2'\
                  ' freq   -5355 delay    603'
    print("parse_phc2sys_out:")
    result = parse_phc2sys_out(test_string)
    print(test_string)
    print(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PCAP reader')
    parser.add_argument('--input', metavar='<input file name>',
                        help='input file to parse', nargs='?', const=1, default='ptp4l.log')
    parser.add_argument('--ut', action='store_true')
    parser.add_argument('--plot', action='store_true')
    args = parser.parse_args()

    if args.ut:
        unit_test()
        sys.exit(0)

    if not os.path.isfile(args.input):
        print(f'File {format(args.input)} does not exist!', file=sys.stderr)
        sys.exit(-1)

    array = parse_file(args.input, 1)

    if args.plot:
        plot(array)

    sys.exit(0)
