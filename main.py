#!/usr/bin/python3
# Copyright (c) 2021 Intel
# Copyright (C) 2023 Milena Olech <milena.olech(at)intel.com>
# Copyright (C) 2023 Marta Plantykow <m.plantykow(at)gmail.com>
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html
"""Module providing GA for PTP PI controller."""

import sys
import random
import os
import shutil
import argparse
import time
import numpy
import configureme as config
from evaluate import Creature
from create_graph import graph_elite
from create_graph import graph_all
from create_graph import create_scatter_plot

class Range():
    """Class providing range"""
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __eq__(self, other):
        return self.start <= other <= self.end
    def __contains__(self, item):
        return self.__eq__(item)
    def __iter__(self):
        yield self

def validate_stability(p_term, i_term):
    """Function validating stability."""
    if config.stability_verification == "Complex":
        eq1 = (((p_term + i_term)*(p_term + i_term)) < (4*i_term))
        eq2 = 0 <= i_term <= 4
        eq3 = 0 <= p_term <= 1
        if eq1 and eq2 and eq3:
            return True
        return False
    if config.stability_verification == "Real":
        eq1 = ((2*p_term) < (4 - i_term))
        eq2 = 0 <= i_term <= 4
        eq3 = 0 <= p_term <= 2
        if eq1 and eq2 and eq3:
            return True
        return False
    return True

def draw_stable_kp_ki():
    """Function drawing stable k_p and k_i pair."""
    stable = False
    if config.stability_verification == "Complex":
        gen_max_kp_stable = config.gen_max_kp_stable_complex
    else:
        gen_max_kp_stable = config.gen_max_kp_stable_real
    while not stable:
        p_term = random.uniform(0, gen_max_kp_stable)
        i_term = random.uniform(0, config.gen_max_ki_stable)
        if validate_stability(p_term, i_term):
            stable = True
    return p_term, i_term

def redefine_kp_ki_to_stable(p_term, i_term):
    """Function redefining k_p and k_i to stable."""
    if validate_stability(p_term, i_term):
        return p_term,i_term
    stable = False
    if config.stability_verification == "Complex":
        while not stable:
            if config.debug_level != 1:
                with open(stabilityfilename, "a", encoding="utf-8") as stabilityfile:
                    stabilityfile.write(f"{i_term};{p_term}\n")
            if i_term < 1:
                i_term = i_term + (1 - i_term) * config.reduction_determinant
            if i_term > 1:
                i_term = i_term - (i_term - 1) * config.reduction_determinant
            if i_term == 0:
                i_term = i_term + config.reduction_determinant
            if p_term == 0:
                p_term = p_term + config.reduction_determinant
            p_term = p_term - (p_term * config.reduction_determinant)
            i_term = round(i_term, 3)
            p_term = round(p_term, 3)
            if validate_stability(p_term, i_term):
                stable = True
        return p_term,i_term
    if config.stability_verification == "Real":
        while not stable:
            if config.debug_level != 1:
                with open(stabilityfilename, "a", encoding="utf-8") as stabilityfile:
                    stabilityfile.write(f"{i_term};{p_term}\n")
            i_term = i_term - (i_term * config.reduction_determinant)
            p_term = p_term - (p_term * config.reduction_determinant)
            if i_term <= 0:
                i_term = i_term + config.reduction_determinant
            if p_term <= 0:
                p_term = p_term + config.reduction_determinant
            i_term = round(i_term, 3)
            p_term = round(p_term, 3)
            if validate_stability(p_term, i_term):
                stable = True
        return p_term,i_term
    return p_term,i_term

if config.metric not in {"MSE", "RMSE", "MAE"}:
    print("Specify one of the following metrics: MSE, RMSE, MAE")
    sys.exit()
if config.stability_verification not in {"Complex", "Real", "False"}:
    print("Specify one of the following options for stability verification: Complex, Real, False")
    sys.exit()
if config.gen_population_size < 8:
    print("Min population size: 8")
    sys.exit()
if config.gen_epochs < 1:
    print("Min number of epochs: 1")
    sys.exit()
if config.gen_max_kp <= 0:
    print("Max k_p must be greater than 0")
    sys.exit()
if config.gen_max_ki <= 0:
    print("Max k_i must be greater than 0")
    sys.exit()
if config.gen_num_random < 0:
    print("The number of randomly added creatures must be greater or equal to 0")
    sys.exit()
if config.gen_num_inherited < 0:
    print("The number of inherited creatures must be greater or equal to 0")
    sys.exit()
if config.gen_num_replicated < 0:
    print("Number of replicated creatures must be greater or equal to 0")
    sys.exit()
if config.gen_mutation_coef < 1:
    print("Mutation coef must be greater or equal 1")
    sys.exit()
if config.gen_elite_size < 0:
    print("Elite size must be greater or equal 0")
    sys.exit()
if config.test_repeted_creatures not in {True, False}:
    print("Specify one of the following options for testing repeated creatures: True, False")
    sys.exit()


#Validate interface
adapterlist = os.listdir('/sys/class/net/')
parser = argparse.ArgumentParser(description='Genetic algorithm for PID in PTP implementation')

#List of arguments
parser.add_argument("--i", type=str, choices = adapterlist, help="Interface")
parser.add_argument("--t", default=120, choices=range(1,9999), type=int,
                    help="-t from PTP script", metavar="[1-9999]")

args = parser.parse_args()

#Pull date and time to use as log filename
timestr = time.strftime("%Y%m%d-%H%M%S")
result_path = f'./{config.app}_{timestr}'
#Define filenames
os.makedirs(result_path, exist_ok=True)
csvfilename = f'{result_path}/{config.app}.csv'
logfilename = f'{result_path}/{config.app}.log'
elitefilename = f'{result_path}/{config.app}_elite.csv'
stabilityfilename = f'{result_path}/{config.app}_stability.log'
initialvaluesfilename = "initial_values.csv"

#Add header to csvfilename
with open(csvfilename, "a", encoding="utf-8") as csvfile:
    csvfile.write("epoch,creature,k_p,k_i,rating\n")

#Add header to elitefilename
with open(elitefilename, "a", encoding="utf-8") as elitefile:
    elitefile.write("epoch,k_p,k_i,rating\n")

#Measure default settings
print("Measuring result with default settings...")
default = Creature(0.7,0.3)
default.evaluate_data(args.i, args.t)
shutil.move(f"{config.app}_P0.7_I0.3", f"{result_path}/{config.app}_P0.7_I0.3")
print(f"Default k_p: {default.k_p} default k_i: {default.k_i} Score: {default.rating}\n")

with open(logfilename, "a", encoding="utf-8") as f:
    f.write("\n***************************************************************\n")
    f.write("Default settings results:\n")
    f.write(f"k_p: {default.k_p}, k_i: {default.k_i}, Score: {default.rating}\n")

if config.stability_verification is True:
    print("Stability verification enabled")

#Initial population
population_size = config.gen_population_size
population = []
elite = []
count = 0

print("Creating initial population...")

if (config.gen_mutation_coef > 1 or config.gen_mutation_coef < -1):
    sys.exit("Improper mutation coefficient in the config file")

if config.initial_values is True:
    with open(initialvaluesfilename, "r", encoding="utf-8") as initial_values:
        lines = initial_values.readlines()
        no_of_lines = len(lines)
        if no_of_lines > population_size:
            sys.exit("Improper number of initial values")

        for line in lines:
            parts = line.strip().split(',')
            if len(parts) == 2:
                try:
                    k_p = float(parts[0])
                    k_i = float(parts[1])
                    population.append(Creature(k_p, k_i))
                    count = count + 1
                except ValueError:
                    print(f"Skipping invalid line: {line}")

population_size = population_size - count

for _ in range(population_size):
    if config.stability_verification in {"Real", "Complex"}:
        k_p,k_i = draw_stable_kp_ki()
        population.append(Creature(k_p,k_i))
    else:
        population.append(Creature(random.uniform(0, config.gen_max_kp),
                                   random.uniform(0, config.gen_max_ki))) #nosec

cntr = 0
print("Initial population created!")

if config.debug_level != 1:
    for creature in population:
        print(f'Creature {cntr} k_p: {creature.k_p} k_i: {creature.k_i}')
        cntr = cntr + 1

for epoch in range(config.gen_epochs):
    print("***************************************************************")
    print(f"EPOCH NUMBER {epoch}")
    print("***************************************************************")

    score = []
    sorted_scores_indexes = []

    #Evaluate candidates
    i = 0
    for parent in population:
        new_k_p = round(parent.k_p,3)
        new_k_i = round(parent.k_i,3)
        parent.mutate(new_k_p, new_k_i)
        print(f'Epoch {epoch}: creature {i}, k_p {new_k_p:.3f},'\
              f' k_i {new_k_i:.3f} ', end="", flush=True)
        parent.evaluate_data(args.i, args.t)
        if config.test_repeted_creatures is False:
            if os.path.isdir(f"{config.app}_P{parent.k_p}_I{parent.k_i}"):
                shutil.move(f"{config.app}_P{parent.k_p}_I{parent.k_i}",
                            f"{result_path}/{config.app}_P{parent.k_p}_I{parent.k_i}")
        else:
            if os.path.isdir(f"{config.app}_P{parent.k_p}_I{parent.k_i}"):
                shutil.move(f"{config.app}_P{parent.k_p}_I{parent.k_i}",
                            f"{result_path}/{config.app}_P{parent.k_p}_I{parent.k_i}_Epoch{epoch}_Creature{i}")

        score.append(parent.rating)
        with open(csvfilename, "a", encoding="utf-8") as csvfile:
            csvfile.write(f"{epoch},{i},{parent.k_p},{parent.k_i},{parent.rating}\n")
        i = i + 1

    if config.debug_level == 2:
        print(f"Score:  {score}")

    #Select candidates fo new generation
    sorted_scores_indexes = numpy.argsort(score)

    #Pick the best result and save it to the file
    index = sorted_scores_indexes[0]

    with open(logfilename, "a", encoding="utf-8") as f:
        f.write(f"Epoch number: {epoch}\n")
        f.write(f"k_p: {population[index].k_p:.3f} ")
        f.write(f"k_i: {population[index].k_p:.3f} ")
        f.write(f"Score: {score[index]:.3f}\n")
        #Write all scores to the file
        for i in range(len(score)):
            f.write(f"Test {i}: k_p: {population[i].k_p:.3f} ")
            f.write(f"k_i: {population[i].k_i:.3f} ")
            f.write(f" Score: {score[i]:.3f}\n")
        #os.chmod(logfilename, 0o600)

    if config.debug_level == 2:
        print("Sorted Scores indexes: ", sorted_scores_indexes)

    #Create Elite
    for i in range(config.gen_elite_size):
        index = sorted_scores_indexes[i]
        elite.append(population[index])
    elite.sort(key = lambda Creature: Creature.rating)

    for i in range(len(elite)):
        if i is config.gen_elite_size:
            del elite[i:len(elite)]
            break

    with open(elitefilename, "a", encoding="utf-8") as elitefile:
        elitefile.write(f"{epoch},{elite[0].k_p},{elite[0].k_i},{elite[0].rating}\n")

    print(f"Epoch {epoch}: Best score: {elite[0].rating} default {default.rating}")
    if elite[0].rating > default.rating:
        print(f"Result worse by {(elite[0].rating-default.rating)/default.rating:.1%}\n")
        with open(logfilename, "a", encoding="utf-8") as f:
            f.write(f"Result worse by {(elite[0].rating-default.rating)/default.rating:.1%}\n")
    else:
        print(f"Result better by {(default.rating-elite[0].rating)/default.rating:.1%}\n")
        with open(logfilename, "a", encoding="utf-8") as f:
            f.write(f"Result better by {(default.rating-elite[0].rating)/default.rating:.1%}\n")

    #Create new generation
    new_generation = []

    #Crossing parents
    print("Crossing parents...")
    x = 0
    for x in range(config.gen_num_inherited):
        y = x + 1
        for _ in range(config.gen_num_inherited - x - 1):
            if config.debug_level == 2:
                print(x, " + ", y)
            if config.stability_verification:
                if config.debug_level == 2:
                    print("Veryfing parent stability")
                if (validate_stability(population[sorted_scores_indexes[x]].k_p,
                                       population[sorted_scores_indexes[y]].k_i)):
                    new_generation.append(Creature(population[sorted_scores_indexes[x]].k_p,
                                                   population[sorted_scores_indexes[y]].k_i))
                else:
                    k_p, k_i = redefine_kp_ki_to_stable(population[sorted_scores_indexes[x]].k_p,
                                                      population[sorted_scores_indexes[y]].k_i)
                    new_generation.append(Creature(k_p, k_i))
                if (validate_stability(population[sorted_scores_indexes[y]].k_p,
                                       population[sorted_scores_indexes[x]].k_i)):
                    new_generation.append(Creature(population[sorted_scores_indexes[x]].k_p,
                                                   population[sorted_scores_indexes[y]].k_i))
                else:
                    k_p, k_i = redefine_kp_ki_to_stable(population[sorted_scores_indexes[y]].k_p,
                                                      population[sorted_scores_indexes[x]].k_i)
                    new_generation.append(Creature(k_p, k_i))
            else:
                new_generation.append(Creature(population[sorted_scores_indexes[x]].k_p,
                                               population[sorted_scores_indexes[y]].k_i))
                new_generation.append(Creature(population[sorted_scores_indexes[y]].k_p,
                                               population[sorted_scores_indexes[x]].k_i))
            y = y + 1
        x = x + 1
    print("New generation creation - crossed creatures added!")
    if config.debug_level != 1:
        cntr = 0
        for creature in new_generation:
            print(f"New generation creature {cntr}, k_p: {creature.k_p}, k_i: {creature.k_i}")
            cntr = cntr + 1

    new_generation_size = len(new_generation)

    #Replicating parents
    print("Replicating parents...")
    for x in range(config.gen_num_replicated):
        new_generation.append(Creature(population[sorted_scores_indexes[x]].k_p,
                                       population[sorted_scores_indexes[x]].k_i))
    print("New generation creation - replicated creatures added!")
    if config.debug_level != 1:
        cntr2 = 0
        for creature in new_generation:
            if cntr2 < new_generation_size:
                cntr2 = cntr2 + 1
                continue
            print(f'New generation creature {cntr2} k_p: {creature.k_p:.3f}'\
                  f' k_i: {creature.k_i:.3f}')
            cntr2 = cntr2 + 1
    new_generation_size = len(new_generation)

    #Adding randoms
    print("Adding new random parents")
    for _ in range(config.gen_num_random):
        if config.stability_verification is True:
            k_p,k_i = draw_stable_kp_ki()
            new_generation.append(Creature(k_p,k_i))
        else:
            new_generation.append(Creature(random.uniform(0, config.gen_max_kp),
                                           random.uniform(0, config.gen_max_ki))) #nosec

    print("New generation creation - random creatures added!")
    if config.debug_level != 1:
        cntr2 = 0
        for creature in new_generation:
            if cntr2 < new_generation_size:
                cntr2 = cntr2 + 1
                continue
            print(f'New generation creature {cntr2} k_p: {creature.k_p:.3f}'\
                  f' k_i: {creature.k_i:.3f}')
            cntr2 = cntr2 + 1

    #Mutation
    print("Mutants are coming...")
    for creature in new_generation:
        rand_x = random.uniform(-1, 1) #nosec
        new_kp = creature.k_p + (rand_x * config.gen_mutation_coef)
        new_kp = max(0, min(new_kp, config.gen_max_kp))
        rand_y = random.uniform(-1, 1) #nosec
        new_ki = creature.k_i + (rand_y * config.gen_mutation_coef)
        new_ki = max(0, min(new_ki, config.gen_max_ki))
        if not validate_stability(new_kp, new_ki):
            new_kp, new_ki = redefine_kp_ki_to_stable(new_kp, new_ki)
        creature.mutate(new_kp, new_ki)
    print("Mutation finished!")
    if config.debug_level != 1:
        cntr = 0
        for creature in new_generation:
            print(f'New generation creature {cntr} k_p: {creature.k_p:.3f}'\
                  f' k_i: {creature.k_i:.3f}')
            cntr = cntr + 1

    #Print information about progress
    number_of_creatures = len(new_generation)
    progress = number_of_creatures * (epoch + 1)
    epoch_progress = number_of_creatures * config.gen_epochs
    print("***************************************************************")
    print(f"Progress: {progress/epoch_progress:.1%}")
    print("***************************************************************")

    #Switching generations
    population = new_generation

with open(logfilename, "a", encoding="utf-8") as f:
    f.write("\n***************************************************************\n")
    f.write("Genetic algorithm best results:\n")
    #os.chmod(logfilename, 0o600)
    for creature in elite:
        f.write(f"k_p: {creature.k_p}, k_i: {creature.k_i}, Score: {creature.rating}\n")

if config.graph_per_epoch:
    graph_all(csvfilename)

graph_elite(elitefilename)
create_scatter_plot(csvfilename, "scatter_plot.png")
