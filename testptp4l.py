#!/usr/bin/env python3
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html
"""Module running ptp4l test."""
import argparse
import subprocess
import os
import shutil
import sys
import parse_ptp as parse

def reset_ptp_clock(interface, reset_method="ptp4l"):
    """Reset the PTP clock."""
    # Check if the network interface exists
    if not os.path.exists(f"/sys/class/net/{interface}"):
        print(f"Adapter {interface} does not exist.")
        sys.exit(1)

    # Check if the network interface has PTP clocks
    if not os.path.exists(f"/sys/class/net/{interface}/device/ptp"):
        print("Adapter does not have any PTP clocks")
        sys.exit(1)

    # Get the PTP clock device
    #clock_device = f"/dev/{os.listdir(f'/sys/class/net/{interface}/device/ptp')[0]}"

    # Build the command for clock reset
    if reset_method == "ptp4l":
        reset_cmd = f"timeout 30 ptp4l -i {interface} -m -2 -s --tx_timestamp_timeout 100"
    elif reset_method == "phc_ctl":
        reset_cmd = f"phc_ctl {interface} set freq 0"
    elif reset_method == "phc2sys":
        reset_cmd = f"timeout 30 phc2sys -s {interface} -c CLOCK_REALTIME -O 0"
    elif reset_cmd == "phc_ctl_ext":
        reset_cmd = f"phc_ctl {interface} freq auto set"

    reset_cmd += " > /dev/null 2>/dev/null"
    # Execute the clock reset command
    subprocess.run(reset_cmd, shell=True)

def run_ptp_test(interface, P=None, I=None, offset_threshold=None,
                 config_file=None, timeout=60, verbose=False, cut_first=None,
                 reset_method="ptp4l"):
    """Run the ptp4l test."""
    reset_ptp_clock(interface, reset_method)

    # Build the main ptp4l command
    ptp4l_cmd = f"ptp4l -i {interface} -m -2 -s --tx_timestamp_timeout 100"

    if P:
        ptp4l_cmd += f" --pi_proportional_const {P}"

    if I:
        ptp4l_cmd += f" --pi_integral_const {I}"

    if offset_threshold:
        ptp4l_cmd += f" --servo_offset_threshold {offset_threshold}"

    if config_file:
        ptp4l_cmd += f" -f {config_file}"

    if timeout:
        ptp4l_cmd = f"timeout {timeout} {ptp4l_cmd}"

    ptp4l_cmd += " > ptp4l.log 2>/dev/null"

    if verbose:
        print("CMD:", ptp4l_cmd)
        print("TIMEOUT:", timeout)
        print("P_VAL:", P)
        print("I_VAL:", I)
        print("verbose:", verbose)

    # Execute the main ptp4l command
    subprocess.run(ptp4l_cmd, shell=True)

    # Process the log file
    with open("ptp4l.log", "r", encoding="utf-8") as log_file:
        lines = log_file.readlines()

    filtered_lines = []
    for line in lines:
        if "master offset" in line:
            filtered_lines.append(line)

    if cut_first:
        filtered_lines = filtered_lines[cut_first:]

    if offset_threshold:
        with open("ptp4l.log", "w", encoding="utf-8") as log_file:
            log_file.writelines(filtered_lines)

        with open("ptp4l.log", "r", encoding="utf-8") as log_file:
            lines = log_file.readlines()

        stable_lines = [line for line in lines if "s3" in line]

        with open("ptp4l-stable.log", "w", encoding="utf-8") as stable_file:
            stable_file.writelines(stable_lines)
    else:
        with open("ptp4l.log", "w", encoding="utf-8") as log_file:
            log_file.writelines(filtered_lines)

    path = f"ptp4l_P{P}_I{I}"
    if not os.path.exists(path):
        os.mkdir(path)

    array = parse.parse_file("ptp4l.log", 1)
    parse.plot(array)
    shutil.move("test.png", os.path.join(path, f'ptp4l_P{P}_I{I}.png'))
    shutil.move("ptp4l.log", os.path.join(path, f'ptp4l_P{P}_I{I}.log'))

def main(args):
    """Main function."""
    run_ptp_test(
        args.interface,
        P=args.P,
        I=args.I,
        offset_threshold=args.offset_threshold,
        config_file=args.config_file,
        timeout=args.timeout,
        verbose=args.verbose,
        cut_first=args.cut_first
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PTP Testing Script")
    parser.add_argument("-t", "--timeout", type=int, help="Timeout for ptp4l command")
    parser.add_argument("-i", "--interface", required=True, help="Network interface name")
    parser.add_argument("-P", help="P_VAL")
    parser.add_argument("-I", help="I_VAL")
    parser.add_argument("-c", "--cut_first", type=int, help="Number of lines to cut from the log")
    parser.add_argument("-o", "--offset_threshold", help="Threshold value")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("-f", "--config_file", help="Path to a config file")

    args = parser.parse_args()
    main(args)
