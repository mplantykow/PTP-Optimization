# Precision Time Protocol Optimization (PTP Optimization)

Precision Time Protocol (PTP) Optimization framework aims to optimize the time synchronization using the linuxptp suite by optimizing the Proportional-Integral servo’s parameters. The proposed framework automatically searches for the best variables using a Genetic Algorithm. Different evaluation functions can be used to fulfill optimization goal.

Read more: https://netdevconf.info/0x15/slides/24/netDev%200x15%20Precision%20Time%20Protocol%20optimization%20using%20genetic%20algorithm.pdf

## License

The software is copyrighted by the authors and is licensed under the GNU General Public License. See the file, COPYING, for details of the license terms.

## Hardware

PTP is implemented in PTP-aware networking hardware, that implements the IEEE 1588 standard. To succesfully run the code, an adequate Networking adapter and a proper driver must be installed in the system.

## Software

As this script uses linuxptp suite it is targeted against the linux operating system. Python3 must be installed.

### Required python packages

Use the pip to install required python packages.

```bash
pip install numpy
pip install sklearn
```

## Usage

To succesfully run the script with dedault settings run following code:

```bash
python3 main.py --i EnpXfY
```
where EpnXfY stnads for the interface name. If you want to check the interface name please run following command to print all interfaces name:

```bash
ip a
```
## Configureme

Configureme.py file is used to configure the stability verification, genetic algorithm, and debug level.

| **Argument**              | **Description**                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------- |
| stability_verification    | Stability verification                                                                |
| reduction_determinant     | Kp and Ki reduction granularity in case of instability after mutation or crossover    |
| gen_population_size       | Initial population size                                                               |
| gen_epochs                | Number of epochs                                                                      |
| gen_max_kp                | Max value of Kp                                                                       |
| gen_max_kp                | Max value of Ki                                                                       |
| gen_num_random            | Number of random parents added to each epoch                                          |
| gen_num_inherited         | Number of the best parents that are crossed to create a new generation                |
| gen_num_replicated        | Number of the best parents that are replicated to create a new generation             |
| gen_mutation_coef         | Mutation coefficient                                                                  |
| gen_debug_level           | Determines level of debug prints                                                      |
| gen_elite_size            | Number of elite chromosomes                                                           |

## Arguments

Provided script accepts a set of parameters:

| **Argument** | **Description**                                | Default 	|
| ------------ | ---------------------------------------------- | --------- |
| --i          | Interface                                      | -         |
| --t          | Time of a single test                          | 120       |
| --metric     | Evaluation metric (1 - MSE, 2 - RMSE, 3 - MAE) | 1         |

## Contributing

All contributions will be considered for acceptance through pull requests. 
