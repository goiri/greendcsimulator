#!/bin/bash

# export GUROBI_HOME=/home/goiri/hadoop-parasol/solver/gurobi500/linux64/
export GUROBI_HOME=/home/goirix/gurobi510/linux64/
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi-`hostname`.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib

python2.7 simulator.py $*
