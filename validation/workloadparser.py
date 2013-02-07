#!/usr/bin/env python2.7

import math

NODE_LOG = 'log-222-swim-source-onoff-netwr-peak-node.log'
PERIOD_LENGTH = 15*60

if __name__ == "__main__":
	t0 = None
	period = 0
	values = []
	with open(NODE_LOG, 'r') as f:
		for line in f.readlines():
			if not line.startswith('#'):
				lineSplit = line.split(';')
				t = int(lineSplit[0])
				# Nodes
				onNodes = int(lineSplit[1])
				offNodes = int(lineSplit[2])
				runNodes = int(lineSplit[3])
				# Jobs
				runJobs = int(lineSplit[4])
				totalJobs = int(lineSplit[5])
				runTasks = int(lineSplit[6])
				totalTasks = int(lineSplit[7])
				usedSlots = int(lineSplit[8])
				
				if t0 == None:
					t0 = t
					periodstart = t - t0

				if (t-t0) - periodstart > PERIOD_LENGTH:
					print period*PERIOD_LENGTH, float(sum(values))/float(len(values))
					#values = [runNodes]
					values = [onNodes]
					periodstart = period*PERIOD_LENGTH
					period += 1
				else:
					#values.append(runNodes)
					values.append(onNodes)