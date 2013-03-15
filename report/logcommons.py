#!/usr/bin/python2.7

import os

"""
Get the depth of discharge information from the logfile
"""
def getBatteryStats(logfile):
	numdischarges = None
	totaldischarge = None
	maxdischarge = None
	lifetime = None
	try:
		with open(logfile, 'r') as f:
			# Go to the end of the file
			f.seek(-2*1024, os.SEEK_END)
			f.readline()
			# Start checking from the end
			for line in f.readlines():
				if line.startswith('#'):
					line = line.replace('\n', '')
					if line.startswith('# Battery number discharges:'):
						numdischarges = int(line.split(' ')[4])
					elif line.startswith('# Battery max discharge'):
						maxdischarge = float(line.split(' ')[4][:-1])
					elif line.startswith('# Battery total discharge:'):
						totaldischarge = float(line.split(' ')[4][:-1])
					elif line.startswith('# Battery lifetime:'):
						lifetime = float(line.split(' ')[3][:-1])
	except Exception, e:
		print 'Error getting battery stats', logfile
	return numdischarges, totaldischarge, maxdischarge, lifetime

"""
Read the log file and get the statistics about energy consumption
"""
def getEnergyStats(logfile):
	try:
		brownenergy = 0.0
		greenenergy = 0.0
		netmeenergy = 0.0
		peakpower = 0.0
		batchgenergy = 0.0
		batdisenergy = 0.0
		costenergy = 0.0
		costnetmeter = 0.0
		loadenergy = 0.0
		costpeak = 0.0
		with open(logfile, 'r') as fin:
			for line in fin.readlines():
				if not line.startswith('#'):
					line = line.replace('\n', '')
					lineSplit = line.split('\t')
					# Get battery power
					t =             int(lineSplit[0])
					brownprice =    float(lineSplit[1])
					greenpower =    float(lineSplit[2])
					netmeter =      float(lineSplit[3])
					brownpower =    float(lineSplit[4])
					batcharge =     float(lineSplit[5])
					batdischarge =  float(lineSplit[6])
					batlevel =      float(lineSplit[7])
					workload =      float(lineSplit[8])
					coolingpower =  float(lineSplit[9])
					execload =      float(lineSplit[10])
					prevload =      float(lineSplit[11])
					
					# Account TODO per month
					if brownpower > peakpower:
						peakpower = brownpower
					
					brownenergy += brownpower * (TIMESTEP/3600.0)
					greenenergy += greenpower * (TIMESTEP/3600.0)
					netmeenergy += netmeter * (TIMESTEP/3600.0)
					batchgenergy += batcharge * (TIMESTEP/3600.0)
					batdisenergy += batdischarge * (TIMESTEP/3600.0)
					costenergy += (brownpower * (TIMESTEP/3600.0))/1000.0 * brownprice
					costnetmeter += 0.4*(netmeter * (TIMESTEP/3600.0))/1000.0 * brownprice
					loadenergy += execload * (TIMESTEP/3600.0)
		costpeak = peakpower/1000.0 * 13.61
		
		print logfile
		print 'Energy and power:'
		print '\tBrown energy: %.1fWh' % brownenergy
		print '\tGreen energy: %.1fWh' % greenenergy
		print '\tNet metering energy: %.1fWh' % netmeenergy
		print '\tBattery charge energy: %.1fWh' % batchgenergy
		print '\tBattery discharge energy: %.1fWh' % batdisenergy
		print '\tLoad energy: %.1fWh' % (loadenergy)
		print '\tTotal used: %.1fWh' % (batdisenergy+greenenergy+brownenergy)
		print '\tPeak power: %.1fW' % peakpower
		print 'Cost:'
		print '\tEnergy cost: $%.2f - $%.2f = $%.2f' % (costenergy, costnetmeter, costenergy-costnetmeter)
		print '\tPower cost: $%.2f' % costpeak
	except Exception, e:
		print e

