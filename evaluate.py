#!/usr/bin/python3
# Copyright (c) 2021 Intel
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
        rating = 0

    def mutate(self, new_k_p, new_k_i):
        """Function mutating data."""
        self.k_p = new_k_p
        self.k_i = new_k_i

    def evaluate_data(self, interface, time):
        """Function evaluationg data."""
        #Check if provided k_p and k_i are not repeated
        repeated_data = self.validate_data()
        if repeated_data == 0:
            print("Correct data!")
            try:
                if config.app == "phc2sys":
                    subprocess.check_call(
                            split('./test-phc2sys.sh -s %s -c CLOCK_REALTIME -P %s -I %s -t %s' %
                                 (str(interface), str(self.k_p), str(self.k_i), str(time))))
                elif config.app == "ptp4l":
                    subprocess.check_call(
                            split('./test-ptp4l.sh -i %s -P %s -I %s -t %s' %
                                 (str(interface), str(self.k_p), str(self.k_i), str(time))))
            except subprocess.SubprocessError:
                if config.app == "phc2sys":
                    print("Error calling phc2sys")
                elif config.app == "ptp4l":
                    print("Error calling ptp4l")
                sys.exit()
            self.get_data_from_file()

            i = 0
            if config.debug_level != 1:
                for i in range(len(Master_offset)):
                    print(Master_offset[i])

            stripped_master_offset = Master_offset[2::]

            if config.debug_level != 1:
                for i in range(len(stripped_master_offset)):
                    print(stripped_master_offset[i])

            #Calculate MSE
            if config.metric=="MSE":
                if config.debug_level != 1:
                    print("Choosen metric: MSE")
                rating = rate_data_mse(stripped_master_offset)
            #Calculate RMSE
            elif config.metric=="RMSE":
                if config.debug_level != 1:
                    print("Choosen metric: RMSE")
                rating = rate_data_rmse(stripped_master_offset)
            #Calculate MAE
            elif config.metric=="MAE":
                if config.debug_level != 1:
                    print("Choosen metric: MAE")
                rating = rate_data_mae(stripped_master_offset)

            Rating_table.append(rating)
        #If k_p and k_i are repeated, return previously calculated rating
        else:
            print("Evaluate.py: Incorrect data!")
            rating = Rating_table[repeated_data - 1]

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
        if config.debug_level != 1:
            print("Number of already checked data: ", len(Checked_data))
        return 0

    def get_data_from_file(self):
        """Function getting master offset from file."""
        Master_offset.clear()
        if config.app == "phc2sys":
            file_name = "phc2sys_P%s_I%s/phc2sys_P%s_I%s.log" % (str(self.k_p),
                                                                 str(self.k_i),
                                                                 str(self.k_p),
                                                                 str(self.k_i))
        elif config.app == "ptp4l":
            file_name = "ptp4l_P%s_I%s/ptp4l_P%s_I%s.log" % (str(self.k_p),
                                                             str(self.k_i),
                                                             str(self.k_p),
                                                             str(self.k_i))
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
    print("MSE: ", mse)

    return mse

def rate_data_rmse(data):
    """Function calculating RMSE."""
    arr = [0 for i in range(len(data))]

    array1 = list(map(float, arr))
    array2 = list(map(int, data))
    rmse = mean_squared_error(array1, array2, squared=False)
    print("RMSE: ", rmse)

    return rmse

def rate_data_mae(data):
    """Function calculating MAE."""
    arr = [0 for i in range(len(data))]

    array1 = list(map(float, arr))
    array2 = list(map(int, data))
    mae = mean_absolute_error(array1, array2)
    print("MAE: ", mae)

    return mae
