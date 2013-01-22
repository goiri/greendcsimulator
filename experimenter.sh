#!/bin/bash

PERIOD="1y"
WORKLOAD="data/workload/variable.workload"
WORKLOAD="data/workload/asplos.workload"


echo "Experiment starts at: "`date`

echo "Deferrable"
# Parasol: solar and batteries
bash simulator.sh                   --period $PERIOD --workload $WORKLOAD --delay
# No batteries
bash simulator.sh --battery         --period $PERIOD --workload $WORKLOAD --delay
# No solar
bash simulator.sh --solar           --period $PERIOD --workload $WORKLOAD --delay
# Conventional datacenter
bash simulator.sh --solar --battery --period $PERIOD --workload $WORKLOAD --delay

echo "Non-deferrable"
# Parasol: solar and batteries
bash simulator.sh                   --period $PERIOD --workload $WORKLOAD
# No batteries
bash simulator.sh --battery         --period $PERIOD --workload $WORKLOAD
# No solar
bash simulator.sh --solar           --period $PERIOD --workload $WORKLOAD
# Conventional datacenter
bash simulator.sh --solar --battery --period $PERIOD --workload $WORKLOAD

echo "Experiment finishes at: "`date`


