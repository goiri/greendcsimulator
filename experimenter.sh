#!/bin/bash

PERIOD="1y"
WORKLOAD="data/workload/variable.workload"
WORKLOAD="data/workload/asplos.workload"

# Solar
bash simulator.sh --solar 3200 --battery     0  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar 2400 --battery     0  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar 1600 --battery     0  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar  800 --battery     0  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar    0 --battery     0  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar 3200 --battery 32000  --period $PERIOD --workload $WORKLOAD --delay
bash simulator.sh --solar    0 --battery 32000  --period $PERIOD --workload $WORKLOAD --delay


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


