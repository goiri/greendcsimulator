#!/bin/bash



# Parasol: solar and batteries
bash simulator.sh                   --period 1d
# No batteries
bash simulator.sh --battery         --period 1d
# No solar
bash simulator.sh --solar           --period 1d
# Conventional datacenter
bash simulator.sh --solar --battery --period 1d
