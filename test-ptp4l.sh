#!/bin/bash
# Copyright (c) 2021 Intel
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html

#parse the commandline
while [[ "$#" -gt 0 ]]
do
    case $1 in
	-t|--timeout) TIMEOUT="$2"; shift ;;
	-i) interface="$2"; shift ;;
	-P) P_VAL="$2"; shift ;;
	-I) I_VAL="$2"; shift ;;
	-v|--verbose) VERBOSE=1 ;;
	-o|--offset) OFFSET=$2; shift;;
	*) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

#check if slave has a valid PTP clock assigned
	if [ ! -d "/sys/class/net/$interface" ]
	then
		echo "Adapter $interface does not exist."
		exit 1
	fi

	if [ ! -d "/sys/class/net/$interface/device/ptp" ]
	then
		echo "Adapter does not have any PTP clocks"
		exit 1
	fi

        C_VAL="/dev/"$(ls -1 /sys/class/net/$interface/device/ptp)
#	optionally, add code for clearing current frequency corrections
#	./clearadj/clearadj

#Build the command
RES_CLK="phc_ctl $interface set freq 0"
eval $RES_CLK

CMD="ptp4l -i $interface -m -2 -s --tx_timestamp_timeout 100"
DIR="ptp4l"
[ -n $P_VAL ] && CMD=$CMD" --pi_proportional_const $P_VAL" DIR=$DIR"_P$P_VAL"
[ -n $I_VAL ] && CMD=$CMD" --pi_integral_const $I_VAL" DIR=$DIR"_I$I_VAL"
[ -n $TIMEOUT ] && CMD="timeout $TIMEOUT $CMD"
CMD="$CMD > $DIR.log"

if [[ -n "$VERBOSE" ]]
then
	echo "CMD: $CMD"
	echo "TIMEOUT: $TIMEOUT"
	echo "P_VAL: $P_VAL"
	echo "I_VAL: $I_VAL"
	echo "verbose $VERBOSE"
fi

eval $CMD
chmod 600 "$DIR.log"
cat "$DIR.log" | grep master\ offset > temp.log
mv -f temp.log "$DIR.log"

[[ ! -d "$DIR" && ! -L "$DIR" && ! -f "$DIR" ]] && mkdir $DIR
python3 parse_ptp.py --input $DIR.log --plot
mv $DIR.log $DIR
mv test.png $DIR/$DIR.png
