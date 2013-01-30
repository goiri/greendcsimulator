#!/usr/bin/python2.7

import os

from commons import *
from conf import *

if __name__ == "__main__":
	for filename in os.listdir(LOG_PATH):
		print LOG_PATH+filename
		if filename.endswith('.log'):
			split = filename[:-4].split('-')
			split.pop(0)
			battery = int(split.pop(0))
			solar = int(split.pop(0))
			period = parseTime(split.pop(0))
			# Net metering
			netmeter = 0.0
			if split[0].startswith('net'):
				netmeter = float(split.pop(0)[4:])
			# Workload
			workload = split.pop(0)
			# Read the rest of the values
			delay = False
			alwayson = False
			while len(split) > 0:
				value = split.pop(0)
				if value == 'on':
					alwayson = True
				elif value == 'delay':
					delay = True
				else:
					print 'Unknown value:', value
			
			print battery, solar, timeStr(period), netmeter, workload, delay, alwayson