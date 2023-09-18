#!/usr/bin/python3
# Copyright (c) 2021 Intel
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html
"""GA for PID in PTP."""

import subprocess #nosec
from shlex import split
import sys
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
import configureme as config
import testptp4l

Rating_table = []
Checked_data = []
Master_offset = []

class Creature():
    """Creature class."""
    rating = 0

    def __init__(self, k_p, k_i):
        """Init function."""
        self.k_p = k_p
        self.k_i = k_i
        self.rating = 0

    def mutate(self, new_k_p, new_k_i):
        """Function mutating data."""
        self.k_p = new_k_p
        self.k_i = new_k_i

    def evaluate_data(self, interface, time):
        """Function evaluationg data."""
        #Check if provided k_p and k_i are not repeated
        repeated_data = self.validate_data()
        if repeated_data:
            print("Evaluate.py: Repeated data!")
            self.rating = Rating_table[repeated_data - 1]
            return

        try:
            if config.app == "phc2sys":
                subprocess.check_call(
                        split(f'./test-phc2sys.sh -s {interface} -c CLOCK_REALTIME'\
                                f' -P {self.k_p} -I {self.k_i} -t {time}'))
            elif config.app == "ptp4l":
                testptp4l.run_ptp_test(interface, P=self.k_p, I=self.k_i, timeout=time)
        except subprocess.SubprocessError:
            if config.app == "phc2sys":
                print("Error calling phc2sys")
            elif config.app == "ptp4l":
                print("Error calling ptp4l")
            sys.exit()
        self.get_data_from_file()

        stripped_master_offset = Master_offset[2::]

        if config.debug_level != 1:
            print("\nEvaluate.py: Master offset:")
            for offset in enumerate(Master_offset):
                print(offset)
            print("\nEvaluate.py: Stripped master offset:")
            for offset in enumerate(stripped_master_offset):
                print(offset)

        #Calculate MSE
        if config.metric=="MSE":
            rating = rate_data_mse(stripped_master_offset)
        #Calculate RMSE
        elif config.metric=="RMSE":
            rating = rate_data_rmse(stripped_master_offset)
        #Calculate MAE
        elif config.metric=="MAE":
            rating = rate_data_mae(stripped_master_offset)
        Rating_table.append(rating)

        self.rating = rating

    def validate_data(self):
        """Function validating data."""
        if len(Checked_data) > 0:
            cntr = 1
            for creature in Checked_data:
                if(creature.k_p == self.k_p and creature.k_i == self.k_i):
                    return cntr
                cntr = cntr + 1

        Checked_data.append(Creature(self.k_p, self.k_i))
        return 0

    def get_data_from_file(self):
        """Function getting master offset from file."""
        Master_offset.clear()
        if config.app == "phc2sys":
            file_name = f"phc2sys_P{self.k_p}_I{self.k_i}/phc2sys_P{self.k_p}_I{self.k_i}.log"
        elif config.app == "ptp4l":
            file_name = f"ptp4l_P{self.k_p}_I{self.k_i}/ptp4l_P{self.k_p}_I{self.k_i}.log"
        else:
            file_name = "filename"

        with open(file_name, 'r', encoding="utf-8") as read_file:
            for line in read_file:
                splitted = line.split()
                if config.app == "phc2sys":
                    Master_offset.append(splitted[4])
                elif config.app == "ptp4l":
                    Master_offset.append(splitted[3])

        return Master_offset

def rate_data_mse(data):
    """Function calculationg MSE."""
    arr = [0 for i in range(len(data))]

    array1 = list(map(float, arr))
    array2 = list(map(int, data))
    mse = mean_squared_error(array1, array2)
    mse = round(mse,3)
    print(f"MSE: {mse}")

    return mse

def rate_data_rmse(data):
    """Function calculating RMSE."""
    arr = [0 for i in range(len(data))]

    array1 = list(map(float, arr))
    array2 = list(map(int, data))
    rmse = mean_squared_error(array1, array2, squared=False)
    rmse = round(rmse,3)
    print(f"RMSE: {rmse}")

    return rmse

def rate_data_mae(data):
    """Function calculating MAE."""
    arr = [0 for i in range(len(data))]

    array1 = list(map(float, arr))
    array2 = list(map(int, data))
    mae = mean_absolute_error(array1, array2)
    mae = round(mae,3)
    print(f"MAE: {mae:.3f}")

    return mae
