#!/usr/bin/python3
# Copyright (C) 2023 Milena Olech <milena.olech(at)intel.com>
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html
"""Module providing plots of data gathered during the test."""
import argparse
import statistics as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as plot

def create_kp_ki_plot(k_p, k_i, numbers, filename, epoch, print_epoch):
    """Function plotting kp/ki plot."""
    plt.figure()
    plt.scatter(k_p, k_i)
    plt.ylabel("Ki")
    plt.xlabel("Kp")

    for i in range(len(numbers)):
        x = k_p[i]
        y = k_i[i]
        plt.text(x, y, f"{i}")

    if print_epoch:
        plt.savefig(filename + "_epoch" + epoch + ".png")
    else:
        plt.savefig(filename + ".png")
    plt.close()

def create_score_plot(numbers, scores, filename, epoch, print_epoch):
    """Function plotting scores."""
    plt.plot(numbers, scores, color='green', linestyle='dashed', linewidth = 1,
             marker='o', markerfacecolor='blue', markersize=12)
    plt.ylabel("Score")
    plt.xlabel("Number")

    if print_epoch:
        plt.savefig(filename + "_epoch" + epoch +"_score.png")
    else:
        plt.savefig(filename + "_score.png")
    plt.close()

def graph_elite(filename):
    """Function plotting only elite points from all runs."""
    plt.figure()
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    kp_set = []
    ki_set = []
    numbers_set = []
    scores_set = []
    i = 0

    for line in lines:
        if line.startswith("epoch"):
            continue

        parts = line.strip().split(',')

        if len(parts) == 4:
            try:
                k_p = float(parts[1])
                k_i = float(parts[2])
                number = i
                score = float(parts[3])
                score = round(score, 3)
                scores_set.append(score)
                numbers_set.append(number)
                kp_set.append(k_p)
                ki_set.append(k_i)
                i = i + 1
            except ValueError:
                print(f"Skipping invalid line: {line}")

    filename = filename.replace(".csv", "")
    create_kp_ki_plot(kp_set, ki_set, numbers_set, filename, 0, False)
    create_score_plot(numbers_set, scores_set, filename, 0, False)


def graph_all(filename):
    """Function plotting all data."""
    plt.figure()
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()
        no_of_lines = len(lines)

    reference_epoch = 0
    count = 0

    for line in lines:
        if line.startswith("epoch"):
            continue

        parts = line.strip().split(',')
        if len(parts) == 5:
            epoch = parts[0]
            if reference_epoch != epoch:
                reference_epoch = epoch
                count = count + 1


    for i in range(count):
        kp_set = []
        ki_set = []
        numbers_set = []
        scores_set = []

        for line in lines:
            if line.startswith("epoch"):
                continue

            parts = line.strip().split(',')

            if len(parts) == 5:
                try:
                    k_p = float(parts[2])
                    k_i = float(parts[3])
                    number = float(parts[1])
                    score = float(parts[4])
                    score = round(score, 3)
                    scores_set.append(score)
                    numbers_set.append(number)
                    kp_set.append(k_p)
                    ki_set.append(k_i)
                except ValueError:
                    print(f"Skipping invalid line: {line}")

        filename = filename.replace(".csv", "")
        create_kp_ki_plot(kp_set, ki_set, numbers_set, filename, epoch, True)
        create_score_plot(numbers_set, scores_set, filename, epoch, True)

def create_scatter_plot(input_filename, plot_filename):
    """Function creating scatter plot of the data."""
    plt.figure()
    # Load the CSV file into a DataFrame
    df = pd.read_csv(input_filename)

    # Create a scatter plot
    plt.scatter(df['k_i'], df['k_p'], c=df['rating'], cmap=plot.cm.plasma_r)
    plt.colorbar(label='MSE')
    plt.clim(min(df['rating']),
             (st.median(df['rating']) + (st.median(df['rating']) - min(df['rating']))))

    # Add labels and a title
    plt.xlabel('k_i')
    plt.ylabel('k_p')

    # Save the plot to the result filename
    plt.savefig(plot_filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stability Graph Script")
    parser.add_argument("-f", "--file", help="Path to a results file", required=True)

    args=parser.parse_args()
    graph_elite(args.file)
