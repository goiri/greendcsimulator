#!/bin/bash

# Experiment duration
PERIOD="1y"

# Workloads
# Independent workloads
WORKLOAD="data/workload/asplos.workload"
WORKLOAD="data/workload/hotmail.workload"
WORKLOAD="data/workload/messenger.workload"
WORKLOAD="data/workload/wikipedia.workload"
WORKLOAD="data/workload/flash.workload"
WORKLOAD="data/workload/variable.workload"
WORKLOAD="data/workload/mix.workload"
# All workloads
WORKLOADS="data/workload/asplos.workload data/workload/search.workload data/workload/hotmail.workload data/workload/messenger.workload data/workload/wikipedia.workload data/workload/flash.workload data/workload/orkut.workload data/workload/mix.workload"

# Locations
LOCATIONS=""
LOCATIONS=$LOCATIONS" data/locations/newark.location"
LOCATIONS=$LOCATIONS" data/locations/quito.location"

# Net metering. It's already defined in the location
NETMETER_0=0.0  #   0%
NETMETER_WR=0.4 #  40%
NETMETER_RR=1.0 # 100%

# Simple experiments
# LOCATIONS="data/locations/newark.location"
# WORKLOADS="data/workload/asplos.workload"

# Infrastructure
INFRASTRUCTURES=""
INFRASTRUCTURES=$INFRASTRUCTURES" data/parasol.infra"
INFRASTRUCTURES=$INFRASTRUCTURES" data/large.infra"

# Large
SOLARS="0 1MW 2MW 5MW 10MW 15MW"
BATTERIES="0 1MWh 2MWh 5MWh 10MWh 20MWh 50MWh 100MWh"
# Parasol
# SOLARS=" 0 800 1600 2400 3200 4000 4800"
# BATTERIES="0 800 8000 16000 24000 32000"

# Multiprocess
MAXTHREADS=`cat /proc/cpuinfo  | grep processor | wc -l`
NUMTHREADS=0

# Read modes from command line
while [ $# -gt 0 ]; do
	case $1 in
		"--datacenter")
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				if [[ $1 == "large" ]]; then
					INFRASTRUCTURES="data/large.infra"
					SOLARS="0 1MW 2MW 5MW 10MW 15MW"
					BATTERIES="0 1MWh 2MWh 5MWh 10MWh 20MWh 50MWh 100MWh"
				elif [[ $1 == "parasol" ]]; then
					INFRASTRUCTURES="data/parasol.infra"
					SOLARS=" 0 800 1600 2400 3200 4000 4800"
					BATTERIES="0 8000 16000 24000 32000"
				fi
				shift
			done
			;;
		"--solar")
			shift
			SOLARS=$1
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				SOLARS=$SOLARS" "$1
				shift
			done
			;;
		"--battery")
			shift
			BATTERIES=$1
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				BATTERIES=$BATTERIES" "$1
				shift
			done
			;;
		"--location")
			shift
			LOCATIONS=$1
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				LOCATIONS=$LOCATIONS" "$1
				shift
			done
			;;
		"--infrastructure")
			shift
			INFRASTRUCTURES=$1
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				INFRASTRUCTURES=$INFRASTRUCTURES" "$1
				shift
			done
			;;
		"--workload")
			shift
			WORKLOADS=$1
			shift
			while [[ $1 != --* && $# -gt 0 ]]; do
				WORKLOADS=$WORKLOADS" "$1
				shift
			done
			;;
		*)
			echo "Unknown option: $1"
			shift
			;;
	esac
done

if true; then
	for ALWAYSON in ""; do # for ALWAYSON in "" "--alwayson"; do
		for INFRASTRUCTURE in $INFRASTRUCTURES; do
			for LOCATION in $LOCATIONS; do
				for WORKLOAD in $WORKLOADS; do
					for DELAY in "" "--delay"; do
						for BATTERY in $BATTERIES; do
							for SOLAR in $SOLARS; do
								# Wait for empty slots
								if [ $NUMTHREADS -ge $MAXTHREADS ]; then
									# We have filled all the threads, wait for them to finish
									echo "`date`: Waiting for ${THREADS[@]}"
									for THREADID in ${THREADS[@]}; do
										wait $THREADID
									done
									NUMTHREADS=0
								fi
								# Run more simulations
								bash simulator.sh -i $INFRASTRUCTURE --solar $SOLAR --battery $BATTERY --period $PERIOD --workload $WORKLOAD -l $LOCATION $DELAY $ALWAYSON > /dev/null &
								# Store the PID
								THREADS[$NUMTHREADS]=$!
								let NUMTHREADS=$NUMTHREADS+1
	done;	done;	done;	done;	done;	done;	done
	
	# Wait for everybody to finish
	echo "`date`: Waiting for ${THREADS[@]}"
	for THREADID in ${THREADS[@]}; do
		wait $THREADID
	done
fi

if false; then
	bash simulator.sh --solar    0 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --alwayson
	bash simulator.sh --solar 3200 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar 2400 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar 1600 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar  800 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar    0 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar 3200 --battery 32000  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
	bash simulator.sh --solar    0 --battery 32000  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR
fi

if false; then
	bash simulator.sh --solar 3200 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar 2400 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar 1600 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar  800 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar    0 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar 3200 --battery 32000  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar    0 --battery 32000  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay
	bash simulator.sh --solar    0 --battery     0  --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR --delay --alwayson
fi