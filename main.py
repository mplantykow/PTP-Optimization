#!/usr/bin/python3
"""Module providing GA for PTP PI controller."""
# Copyright (c) 2021 Intel
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html

import sys
import random
import os
import argparse
import time
import numpy
import configureme as config
from evaluate import Creature

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

def validate_stability(k_p, k_i):
    """Function validating stability."""
    eq1 = (((k_p + k_i)*(k_p + k_i)) < (4*k_i))
    eq2 = 0 <= k_i <= 4
    eq3 = 0 <= k_p <= 1
    if eq1 and eq2 and eq3:
        return True
    return False

def draw_stable_kp_ki():
    """Function drawing stable k_p and k_i pair."""
    stable = False
    while not stable:
        k_p = random.uniform(0, config.gen_max_kp_stable)
        k_i = random.uniform(0, config.gen_max_ki_stable)
        if validate_stability(k_p, k_i):
            stable = True
    return k_p, k_i

def redefine_kp_ki_to_stable(k_p, k_i):
    """Function redefining k_p and k_i to stable."""
    if validate_stability(k_p, k_i):
        return k_p,k_i
    stable = False
    while not stable:
        #Print stability related calculations to the file
        if config.debug_level != 1:
            with open(stabilityfilename, "a", encoding="utf-8") as stabilityfile:
                stabilityfile.write(f"{k_i};{k_p}\n")
        if k_i < 1:
            k_i = k_i + (1 - k_i) * config.reduction_determinant
        if k_i > 1:
            k_i = k_i - (k_i - 1) * config.reduction_determinant
        if k_i == 0:
            k_i = k_i + config.reduction_determinant
        if k_p == 0:
            k_p = k_p + config.reduction_determinant
        k_p = k_p - config.reduction_determinant * k_p
        k_i = round(k_i, 3)
        k_p = round(k_p, 3)
        if validate_stability(k_p, k_i):
            stable = True
    return k_p,k_i

if config.metric not in {"MSE", "RMSE", "MAE"}:
    print("Specify one of the following metrics: MSE, RMSE, MAE")
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

#Define filenames
csvfilename = str(config.app) + "_"  + timestr + ".csv"
logfilename = str(config.app) + "_" + timestr + ".log"
elitefilename = str(config.app) + "_" + timestr + "_elite.csv"
stabilityfilename = str(config.app) + "_" + timestr + "_stability.log"

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
print("Default k_p: " + str(default.k_p) + " default k_i: " + str(default.k_i) + \
      " Score: " + str(default.rating) + "\n")

with open(logfilename, "a", encoding="utf-8") as f:
    f.write("\n***************************************************************\n")
    f.write("Default settings results:\n")
    f.write(f"k_p: {default.k_p}, k_i: {default.k_i}, Score: {default.rating}\n")

if config.stability_verification is True:
    print("Stability verification enabled")

#Initial population
population = []
elite = []
initial_values = False

if config.initial_values is True:
    initial_values = True

print("Creating initial population...")

if (config.gen_mutation_coef > 1 or config.gen_mutation_coef < -1):
    sys.exit("Improper mutation coefficient in the config file")

for _ in range(config.gen_population_size):
    if initial_values is True:
        k_p = config.initial_kp
        k_i = config.initial_ki
        initial_values = False
        population.append(Creature(k_p, k_i))
        continue

    if config.stability_verification is True:
        k_p,k_i = draw_stable_kp_ki()
        population.append(Creature(k_p,k_i))
    else:
        population.append(Creature(random.uniform(0, config.gen_max_kp),
                                   random.uniform(0, config.gen_max_ki))) #nosec

cntr = 0
print("Initial population created!")

if config.debug_level != 1:
    for creature in population:
        print("Creature", cntr)
        print(creature.k_p)
        print(creature.k_i)
        cntr = cntr + 1

for epoch in range(config.gen_epochs):
    print("***************************************************************")
    print("EPOCH NUMBER ", epoch)
    print("***************************************************************")

    score = []
    sorted_scores_indexes = []

    #Evaluate candidates
    i = 0
    for parent in population:
        print("Evaluating creature number ", i)
        new_k_p = round(parent.k_p,3)
        new_k_i = round(parent.k_i,3)
        parent.mutate(new_k_p, new_k_i)
        print("k_p: ", new_k_p)
        print("k_i: ", new_k_i)
        parent.evaluate_data(args.i, args.t)
        score.append(parent.rating)
        string = str(epoch) + "," + str(i) + "," + str(parent.k_p) + "," + \
                 str(parent.k_i) + "," + str(parent.rating) + "\n"
        with open(csvfilename, "a", encoding="utf-8") as csvfile:
            csvfile.write(string)
        i = i + 1

    print("Score:  ", score)

    #Select candidates fo new generation
    sorted_scores_indexes = numpy.argsort(score)

    #Pick the best result and save it to the file
    index = sorted_scores_indexes[0]

    with open(logfilename, "a", encoding="utf-8") as f:
        f.write(f"Epoch number: {epoch}\n")
        f.write(f"k_p: {population[index].k_p} ")
        f.write(f"k_i: {population[index].k_p} ")
        f.write(f"Score: {score[index]}\n")
        #Write all scores to the file
        for i in range(0, len(score)):
            f.write(f"k_p: {population[i].k_p} ")
            f.write(f"k_i: {population[i].k_i} ")
            f.write(f"Test {i} Score: {score[i]}\n")
        os.chmod(logfilename, 0o600)

    print("Sorted Scores indexes: ", sorted_scores_indexes)

    #Create Elite
    for i in range(0,config.gen_elite_size):
        index = sorted_scores_indexes[i]
        elite.append(population[index])
    elite.sort(key = lambda Creature: Creature.rating)

    for i in range(0, len(elite)):
        if i is config.gen_elite_size:
            del elite[i:len(elite)]
            break

    string = str(epoch) + "," + str(elite[0].k_p) + "," + str(elite[0].k_i) + "," + \
             str(elite[0].rating) + "\n"
    with open(elitefilename, "a", encoding="utf-8") as elitefile:
        elitefile.write(string)

    improvement = (elite[0].rating * 100)/default.rating
    print("Best score ever improvement over default: " + str(improvement) + "%\n")
    with open(logfilename, "a", encoding="utf-8") as f:
        f.write(f"Best score ever improvement over default: {improvement}%\n")

    #Create new generation
    new_generation = []

    #Crossing parents
    print("Crossing parents...")
    x = 0
    for x in range(config.gen_num_inherited):
        y = x + 1
        for _ in range(config.gen_num_inherited - x - 1):
            print(x, " + ", y)
            if config.stability_verification:
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
            print("New generation creature ", cntr)
            print(creature.k_p)
            print(creature.k_i)
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
            print("New generation creature ", cntr2)
            print(creature.k_p)
            print(creature.k_i)
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
            print("New generation creature ", cntr2)
            print(creature.k_p)
            print(creature.k_i)
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
            print("New generation creature ", cntr)
            print(creature.k_p)
            print(creature.k_i)
            cntr = cntr + 1

    #Print information about progress
    number_of_creatures = len(new_generation)
    progress = number_of_creatures * (epoch + 1)
    epoch_progress = number_of_creatures * config.gen_epochs
    print("***************************************************************")
    print("Progress: ", progress/epoch_progress * 100, "%")
    print("***************************************************************")

    #Switching generations
    population = new_generation

with open(logfilename, "a", encoding="utf-8") as f:
    f.write("\n***************************************************************\n")
    f.write("Genetic algorithm best results:\n")
    os.chmod(logfilename, 0o600)
    for creature in elite:
        f.write(f"k_p: {creature.k_p}, k_i: {creature.k_i}, Score: {creature.rating}\n")
