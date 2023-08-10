#!/usr/bin/python3
# Copyright (c) 2021 Intel
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html

import sys
import random
import numpy
import subprocess #nosec
import shlex
import argparse
import os
import configureme as config
from evaluate import Creature

class Range():
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __eq__(self, other):
        return self.start <= other <= self.end
    def __contains__(self, item):
        return self.__eq__(item)
    def __iter__(self):
        yield self


if ((config.metric != "MSE") and (config.metric != "RMSE") and (cofig.metric != "MAE")):
    print("Specify one of the following metrics: MSE, RMSE, MAE")
    exit()
if (config.gen_population_size < 8):
    print("Min population size: 8")
    exit()
if (config.gen_epochs < 1):
    print("Min number of epochs: 1")
    exit()
if (config.gen_max_kp <= 0):
    print("Max Kp must be greater than 0")
    exit()
if (config.gen_max_ki <= 0):
    print("Max Ki must be greater than 0")
    exit()
if (config.gen_num_random < 0):
    print("The number of randomly added creatures must be greater or equal to 0")
    exit()
if (config.gen_num_inherited < 0):
    print("The number of inherited creatures must be greater or equal to 0")
    exit()
if (config.gen_num_repicated < 0):
    print("Number of replicated creatures must be greater or equal to 0")
    exit()
if (config.gen_mutation_coef < 1):
    print("Mutation coef must be greater or equal 1")
    exit()
if (config.gen_elite_size < 0):
    print("Elite size must be greater or equal 0")
    exit()

#Validate interface
adapterlist = os.listdir('/sys/class/net/')
parser = argparse.ArgumentParser(description='Genetic algorithm for PID in PTP implementation')

#List of arguments
parser.add_argument("--i", type=str, choices = adapterlist, help="Interface")
parser.add_argument("--t", default=120, choices=range(1,9999), type=int, help="-t from PTP script", metavar="[1-9999]")

args = parser.parse_args()

#Initial population
population = []
elite = []

print("Creating initial population...")

if (config.gen_mutation_coef > 1 or config.gen_mutation_coef < -1):
    sys.exit("Improper mutation coefficient in the config file")

for _ in range(config.gen_population_size):
    population.append(Creature(random.uniform(0, config.gen_max_kp), random.uniform(0, config.gen_max_ki))) #nosec

iter = 0
print("Initial population created!")

if (config.debug_level != 1):
    for creature in population:
        print("Creature", iter)
        print(creature.Kp)
        print(creature.Ki)
        iter = iter + 1

with open("ptp_optimization.log", "a") as f:
        f.write(f"***************************************************************\n")
        f.write(f"Genetic algorithm results:\n")
        os.chmod("ptp_optimization.log", 0o600);

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
        new_kp = round(parent.Kp,2)
        new_ki = round(parent.Ki,2)
        parent.mutate(new_kp, new_ki)
        parent.evaluate_data(args.i, args.t)
        score.append(parent.rating)
        i = i + 1

    print("Score:  ", score)

    #Select candidates fo new generation
    sorted_scores_indexes = numpy.argsort(score)

    #Pick the best result and save it to the file
    index = sorted_scores_indexes[0]

    with open("ptp_optimization.log", "a") as f:
        f.write(f"Epoch number: {epoch}\n")
        f.write(f"Kp: {population[index].Kp} ")
        f.write(f"Ki: {population[index].Ki} ")
        f.write(f"Score: {score[index]}\n")
        os.chmod("ptp_optimization.log", 0o600)

    print("Sorted Scores indexes: ", sorted_scores_indexes)

    #Create Elite
    for i in range(0,config.gen_elite_size):
        index = sorted_scores_indexes[i]
        elite.append(population[index])
    elite.sort(key = lambda Creature: Creature.rating)

    for i in range(0, len(elite)):
        if i == config.gen_elite_size:
            del elite[i:len(elite)]
            break

    #Create new generation
    new_generation = []

    #Crossing parents
    print("Crossing parents...")
    x = 0
    for x in range(config.gen_num_inherited):
        y = x + 1
        for _ in range(config.gen_num_inherited - x - 1):
            print(x, " + ", y)
            new_generation.append(
                Creature(population[sorted_scores_indexes[x]].Kp, population[sorted_scores_indexes[y]].Ki))
            new_generation.append(
                Creature(population[sorted_scores_indexes[y]].Kp, population[sorted_scores_indexes[x]].Ki))
            y = y + 1
        x = x + 1
    print("New generation creation - crossed creatures added!")
    if config.debug_level != 1:
        iter = 0
        for creature in new_generation:
            print("New generation creature ", iter)
            print(creature.Kp)
            print(creature.Ki)
            iter = iter + 1

    new_generation_size = len(new_generation)

    #Replicating parents
    print("Replicating parents...")
    for x in range(config.gen_num_replicated):
        new_generation.append(Creature(population[sorted_scores_indexes[x]].Kp, population[sorted_scores_indexes[x]].Ki))
    print("New generation creation - replicated creatures added!")
    if config.debug_level != 1:
        iter2 = 0
        for creature in new_generation:
            if iter2 < new_generation_size:
                iter2 = iter2 + 1
                continue
            print("New generation creature ", iter2)
            print(creature.Kp)
            print(creature.Ki)
            iter2 = iter2 + 1
    new_generation_size = len(new_generation)

    #Adding randoms
    print("Adding new random parents")
    for _ in range(config.gen_num_random):
        new_generation.append(Creature(random.uniform(0, config.gen_max_kp), random.uniform(0, config.gen_max_ki))) #nosec

    print("New generation creation - random creatures added!")
    if config.debug_level != 1:
        iter2 = 0
        for creature in new_generation:
            if iter2 < new_generation_size:
                iter2 = iter2 + 1
                continue
            print("New generation creature ", iter2)
            print(creature.Kp)
            print(creature.Ki)
            iter2 = iter2 + 1

    #Mutation
    print("Mutants are coming...")
    for creature in new_generation:
        rand_x = random.uniform(-1, 1) #nosec
        new_kp = creature.Kp + (rand_x * config.gen_mutation_coef)
        new_kp = max(0, min(new_kp, config.gen_max_kp))
        rand_y = random.uniform(-1, 1) #nosec
        new_ki = creature.Ki + (rand_y * config.gen_mutation_coef)
        new_ki = max(0, min(new_ki, config.gen_max_ki))
        creature.mutate(new_kp, new_ki)
    print("Mutation finished!")
    if config.debug_level != 1:
        iter = 0
        for creature in new_generation:
            print("New generation creature ", iter)
            print(creature.Kp)
            print(creature.Ki)
            iter = iter + 1

    #Print information about progress
    number_of_creatures = len(new_generation)
    progress = number_of_creatures * (epoch + 1)
    epoch_progress = number_of_creatures * config.gen_epochs
    print("***************************************************************")
    print("Progress: ", progress/epoch_progress * 100, "%")
    print("***************************************************************")

    #Switching generations
    population = new_generation


with open("ptp_optimization.log", "a") as f:
    f.write(f"\n***************************************************************\n")
    f.write("Genetic algorithm best results:\n")
    os.chmod("ptp_optimization.log", 0o600)
    for creature in elite:
        f.write(f"Kp: {creature.Kp}, Ki: {creature.Ki}, Score: {creature.rating}\n")

default = Creature(0.7,0.3)
default.evaluate_data(args.i, args.t)

with open("ptp_optimization.log", "a") as f:
    f.write(f"\n***************************************************************\n")
    f.write("Default settings results:\n")
    f.write(f"Kp: {default.Kp}, Ki: {default.Ki}, Score: {default.rating}\n")
    os.chmod("ptp_optimization.log", 0o600)
