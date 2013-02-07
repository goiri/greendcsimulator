#!/bin/bash

PERIOD="1y"
WORKLOAD="data/workload/variable.workload"
WORKLOAD="data/workload/asplos.workload"
# WORKLOAD="data/workload/hotmail.workload"

NETMETER_0=0.0
NETMETER_WR=0.4
NETMETER_RR=1.0

# Threading
MAXTHREADS=16
NUMTHREADS=0

if true; then
	for ALWAYSON in "" "--alwayson"; do
		for DELAY in "--delay" ""; do
			for SOLAR in 3200 0 800 1600 2400; do
				for BATTERY in 0 32000 8000 16000 24000; do
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
					bash simulator.sh --solar $SOLAR --battery $BATTERY --period $PERIOD --workload $WORKLOAD --net $NETMETER_WR $DELAY $ALWAYSON > /dev/null &
					# Store the PID
					THREADS[$NUMTHREADS]=$!
					let NUMTHREADS=$NUMTHREADS+1
				done
			done
		done
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

if false; then
	echo "Experiment starts at: "`date`

	echo "Deferrable"
	# Parasol: solar and batteries
	bash simulator.sh                       --period $PERIOD --workload $WORKLOAD --delay
	# No batteries
	bash simulator.sh --nobattery           --period $PERIOD --workload $WORKLOAD --delay
	# No solar
	bash simulator.sh --nosolar             --period $PERIOD --workload $WORKLOAD --delay
	# Conventional datacenter
	bash simulator.sh --nosolar --nobattery --period $PERIOD --workload $WORKLOAD --delay

	echo "Non-deferrable"
	# Parasol: solar and batteries
	bash simulator.sh                       --period $PERIOD --workload $WORKLOAD
	# No batteries
	bash simulator.sh --nobattery           --period $PERIOD --workload $WORKLOAD
	# No solar
	bash simulator.sh --nosolar             --period $PERIOD --workload $WORKLOAD
	# Conventional datacenter
	bash simulator.sh --nosolar --nobattery --period $PERIOD --workload $WORKLOAD

	echo "Experiment finishes at: "`date`
fi


