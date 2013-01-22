#!/bin/bash

PERIOD="1y"


echo "Experiment starts at: "`date`

echo "Deferrable"
# Parasol: solar and batteries
bash simulator.sh                   --period $PERIOD --workload data/workload/variable.workload --delay
# No batteries
bash simulator.sh --battery         --period $PERIOD --workload data/workload/variable.workload --delay
# No solar
bash simulator.sh --solar           --period $PERIOD --workload data/workload/variable.workload --delay
# Conventional datacenter
bash simulator.sh --solar --battery --period $PERIOD --workload data/workload/variable.workload --delay

echo "Non-deferrable"
# Parasol: solar and batteries
bash simulator.sh                   --period $PERIOD --workload data/workload/variable.workload
# No batteries
bash simulator.sh --battery         --period $PERIOD --workload data/workload/variable.workload
# No solar
bash simulator.sh --solar           --period $PERIOD --workload data/workload/variable.workload
# Conventional datacenter
bash simulator.sh --solar --battery --period $PERIOD --workload data/workload/variable.workload

echo "Experiment finishes at: "`date`


