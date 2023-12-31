### [General settings]
# Debug level: 1 for basic, 2 for full logging
debug_level = 1
# Application: ptp4l, phc2sys
app = "ptp4l"
# Metric: MSE, RMSE, MAE
metric = "MAE"
# Fixed Kp, Ki values from initial_values.csv
initial_values = False
# If true, a graph for each epoch is generated
graph_per_epoch = False

### Servo stability verification
# Stability verification: Complex (Complex & stable), Real (Real & stable), False
stability_verification = "Real"
# Based on [1], it is advised to do not modify
gen_max_kp_stable_complex = 1
# Based on [1], it is advised to do not modify
gen_max_kp_stable_real = 2
# Based on [1], it is advised to do not modify
gen_max_ki_stable = 4
# Kp and Ki reduction granularity in case of
# instability after mutation or crossover
reduction_determinant = 0.001

### [Genetic algorithm]
# Initial population size
gen_population_size = 8
# Number of epochs
gen_epochs = 8
# Max value that is considered for Kp
# Ignored when stability_verification is set to True
gen_max_kp = 5
# Max value that is considered for Ki
# Ignored when stability_verification is set to True
gen_max_ki = 5
# Number of random parents added to each epoch
gen_num_random = 2
# Number of the best parents that are replicated to create a new generation
gen_num_inherited = 5
# Number of the best parents that are replicated to create a new generation
gen_num_replicated = 4
# Mutation coefficient
gen_mutation_coef = 1
# Number of elite chromosomes
gen_elite_size = 1
# Set to True to retest repeated creatures or False to assign previous result
test_repeted_creatures = False

# [1] Measurement, Control and Communication Using IEEE 1588
