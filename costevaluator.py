#!/usr/bin/env python2.7

import sys

from commons import *

def getCost(logfilename, start, end):
	with open(logfilename, 'r') as f:
		peakPower = 0.0
		brownCost = 0.0
		for line in f.readlines():
			if not line.startswith('#'):
				lineSplit = line.split('\t')
				t = int(lineSplit[0])
				if t>=start and t<=end:
					brownPrice = float(lineSplit[1])
					greenPower = float(lineSplit[2])
					netmePower = float(lineSplit[3])
					brownPower = float(lineSplit[4])
					batCharPower = float(lineSplit[5])
					batDiscPower = float(lineSplit[6])
					batLevel = float(lineSplit[7])
					workLoad = float(lineSplit[8])
					cooling = float(lineSplit[9])
					execLoad = float(lineSplit[10])
					prevLoad = float(lineSplit[11])
					# Account
					if brownPower > peakPower:
						peakPower = brownPower
					brownCost += 0.25*brownPower/1000.0 * brownPrice
	# Summary
	print 'Brown energy:', costStr(brownCost)
	print 'Peak brown power:', powerStr(peakPower), costStr(13.72*peakPower/1000.0)
	print 'Total cost:', costStr(brownCost + 13.72*peakPower/1000.0)


if __name__ == "__main__":
	getCost(sys.argv[1], 6*30*parseTime('1d'), 7*30*parseTime('1d'))
	#getCost(sys.argv[1], 0, parseTime('2y'))
