#!/bin/bash

# export GUROBI_HOME=/home/goiri/hadoop-parasol/solver/gurobi500/linux64/
export GUROBI_HOME=/home/goiri/gurobi510/linux64/
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
# Check licence
if [ -e $GUROBI_HOME/gurobi-`hostname`.lic ]; then
	export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi-`hostname`.lic
fi
if [ -e $GUROBI_HOME/gurobi.lic.`hostname` ]; then
	export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic.`hostname`
fi

python2.7 simulator.py $*
