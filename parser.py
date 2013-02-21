#!/usr/bin/python2.7

import sys
import os
import os.path
import time
import datetime

from subprocess import Popen, call
from operator import itemgetter

from commons import *
from conf import *
from plotter import *

from infrastructure import Batteries

"""
Defines the scenario to evaluate the datacenter
"""
class Scenario:
	def __init__(self, netmeter=0, period=None, workload=None):
		self.netmeter = netmeter
		self.period = period
		self.workload = workload
	
	def __str__(self):
		return str(self.netmeter) + '-' + timeStr(self.period)  + '-' + str(self.workload)
	
	def __cmp__(self, other):
		if self.workload == other.workload:
			if self.netmeter == other.netmeter:
				return self.period - other.period
			else:
				return self.netmeter - other.netmeter
		else:
			return cmp(self.workload, other.workload)
	
	def __hash__(self):
		return hash(str(self))
	
	def __eq__(self, other):
		return (self.netmeter, self.period, self.workload) == (other.netmeter, other.period, other.workload)

"""
Defines the setup of the datacenter.
"""
class Setup:
	def __init__(self, itsize=0.0, solar=0.0, battery=0.0, location=None, deferrable=False, turnoff=False, greenswitch=True, progress=100.0):
		self.location = location
		self.itsize = itsize
		self.solar = solar
		self.battery = battery
		self.deferrable = deferrable
		self.turnoff = turnoff
		self.greenswitch = greenswitch
		self.progress = progress
		
	def __cmp__(self, other):
		if other == None:
			return 1
		else:
			if self.location == other.location:
				if self.turnoff == other.turnoff:
					if self.deferrable == other.deferrable:
						if self.battery == other.battery:
							return self.solar - other.solar
						else:
							return self.battery - other.battery
					else:
						return self.deferrable - other.deferrable
				else:
					return self.turnoff - other.turnoff
			else:
				return cmp(self.location, other.location)

"""
Defines the costs related with operating a datacenter.
"""
class Cost:
	def __init__(self, energy=0.0, peak=0.0, capex=0.0):
		self.capex = capex
		self.energy = energy
		self.peak = peak
	
	def getTotal(self):
		return self.capex + self.energy + self.peak
	
	def getOPEX(self):
		return self.energy + self.peak
	
	def getCAPEX(self):
		return self.capex

"""
Get the filename related to the current setup
"""
def getFilename(scenario, setup):
	filename = 'result'
	# IT size
	filename += '-%.1f' % setup.itsize
	# Solar
	filename += '-%d' % setup.battery
	# Battery
	filename += '-%d' % setup.solar
	# Period
	filename += '-%s' % timeStr(scenario.period)
	# Net metering
	if scenario.netmeter > 0.0:
		filename += '-net%.2f' % scenario.netmeter
	# Workload
	filename += '-%s' % scenario.workload
	# Location
	filename += '-%s' % setup.location
	# Delay
	if setup.deferrable == True:
		filename += '-delay'
	# Always on
	if setup.turnoff == False:
		filename += '-on'
	# GreenSwitch
	if setup.greenswitch == False:
		filename += '-nogreenswitch'
	return filename

"""
Get the depth of discharge information from the logfile
"""
def getDepthOfDischarge(logfile):
	# Get battery model
	battery = Batteries()
	# Results
	numdischarges = 0 # How many discharges
	totaldischarge = 0.0 # Total DoD (%)
	maxdischarge = 0.0 # Maximum DoD (%)
	lifetime = 0.0 # Lifetime (%)
	
	# Read log file
	try:
		with open(logfile, 'r') as fin:
			# Get battery size from file name
			batterysize = int(logfile.split('-')[2])
			# Read file and get info
			prevbatpower = 0.0
			charging = False
			discharging = False
			startbatlevel = None
			for line in fin.readlines():
				if not line.startswith('#'):
					line = line.replace('\n', '')
					lineSplit = line.split('\t')
					# Get battery power
					t =             int(lineSplit[0])
					batcharge =     float(lineSplit[5])
					batdischarge =  float(lineSplit[6])
					batlevel =      float(lineSplit[7])
					batpower = batcharge - batdischarge
					
					if batcharge > 0 and not charging:
						charging = True
						discharging = False
						if startbatlevel != None:
							batlevel0 = 100.0*startbatlevel/batterysize
							batlevel1 = 100.0*prevbatlevel/batterysize
							#print 'Disharging finished', timeStr(t), '%.1f%%'%(batlevel0), '->', '%.1f%%'%(batlevel1), '=', '%.1f%%'%(batlevel0-batlevel1)
							# A discharge of more than 0.1%
							if batlevel0 - batlevel1 > 0.1:
								numdischarges += 1
								totaldischarge += batlevel0 - batlevel1
								if batlevel0 - batlevel1 > maxdischarge:
									maxdischarge = batlevel0 - batlevel1
								# Account lifetime
								dod = batlevel0 - batlevel1
								cycles = battery.getBatteryCycles(dod)
								#print dod, '% -------->', cycles, 'cycles'
								if cycles > 0.0:
									lifetime += 100.0/cycles
						startbatlevel = batlevel
						
					elif batdischarge > 0 and not discharging:
						charging = False
						discharging = True
						#if startbatlevel != None:
							#print 'Charging finished', timeStr(t), '%.1f%%'%(100.0*startbatlevel/batterysize), '->', '%.1f%%'%(100.0*batlevel/batterysize)
						startbatlevel = batlevel
					
					# Store previous value
					prevbatpower = batpower
					prevbatlevel = batlevel
	except Exception, e:
		print 'Error getting depth of discharge for', logfile
		print 'Cause:', e
		#pass
	
	return numdischarges, totaldischarge, maxdischarge, lifetime

"""
Get the energy statistics for a run
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
					
					# Account
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

"""
Generate figures for a setup and scenario
"""
def genFigures(filenamebase):
	# Multi process
	MAX_PROCESSES = 8
	processes = []
	now = time.time()
	newDataFile = False
	# Generate data for plotting
	inputfile =  LOG_PATH+filenamebase+'.log'
	if os.path.isfile(inputfile):
		# Generate input data (make he figure boxed)
		datafile = '/tmp/'+LOG_PATH+filenamebase+'.data'
		if not os.path.isdir(datafile[:datafile.rfind('/')]):
			os.makedirs(datafile[:datafile.rfind('/')])
		if not os.path.isfile(datafile) or os.path.getmtime(datafile) < now - parseTime('6h'):
			genPlotData(inputfile, datafile)
			newDataFile = True
		# Generate a figure for each monthFb
		for i in range(1, 12+1):
			daystart = int(datetime.date(2012, i, 1).strftime('%j'))-1
			if i < 12:
				dayend = int(datetime.date(2012, i+1, 1).strftime('%j'))
			else:
				dayend = int(datetime.date(2012, i, 31).strftime('%j'))
			
			# Generate figure for each month
			imgfile = LOG_PATH+'img/'+filenamebase+'/'+str(i)+'.png'
			if not os.path.isdir(imgfile[:imgfile.rfind('/')]):
				os.makedirs(imgfile[:imgfile.rfind('/')])
			if not os.path.isfile(imgfile) or os.path.getmtime(imgfile) < now - parseTime('6h') or os.path.getmtime(datafile) < now - parseTime('6h'):
				p = Popen(['/bin/bash', 'plot.sh', datafile, imgfile, '%d' % (daystart*24), '%d' % (dayend*24)])#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
				processes.append(p)
			
			# Generate figure for a couple days in a month
			imgfile = LOG_PATH+'img/'+filenamebase+'/'+str(i)+'-day.png'
			if not os.path.isdir(imgfile[:imgfile.rfind('/')]):
				os.makedirs(imgfile[:imgfile.rfind('/')])
			if not os.path.isfile(imgfile) or os.path.getmtime(imgfile) < now - parseTime('6h') or os.path.getmtime(datafile) < now - parseTime('6h'):
				p = Popen(['/bin/bash', 'plot.sh', datafile, imgfile, '%d' % ((daystart+15)*24), '%d' % ((daystart+18)*24)])#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
				processes.append(p)
			
			# Wait until we only have 8 figures to go
			while len(processes)>MAX_PROCESSES:
				for p in processes:
					if p.poll() != None:
						processes.remove(p)
				if len(processes)>MAX_PROCESSES:
					time.sleep(0.5)
	# Wait for everybody to finish
	while len(processes)>0:
		for p in processes:
			if p.poll() != None:
				processes.remove(p)
		if len(processes)>0:
			time.sleep(0.5)

"""
Generate figures for a filename base
"""
def generateFigures(scenario, setup):
	genFigures(getFilename(scenario, setup))

"""
Save the details of an experiment with a datacenter with a given setup.
"""
def saveDetails(scenario, setup, cost):
	with open(LOG_PATH+getFilename(scenario, setup)+".html", 'w') as fout:
		# Header
		fout.write('<html>\n')
		fout.write('<head>\n')
		fout.write('  <title>Green Datacenter Simulator results</title>\n')
		fout.write('  <link rel="stylesheet" type="text/css" href="style.css"/>\n')
		fout.write('</head>\n')
		fout.write('<body>\n')
		
		# Content
		fout.write('<h1>Scenario</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Period: %s</li>\n' % timeStr(scenario.period))
		fout.write('  <li>Net metering: %.1f%%</li>\n' % (scenario.netmeter*100.0))
		fout.write('</ul>\n')
		
		fout.write('<h1>Setup</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Location: %s</li>\n' % setup.location.replace('_', ' ').title())
		fout.write('  <li>IT: %s</li>\n' % powerStr(setup.itsize))
		fout.write('  <li>Solar: %s</li>\n' % powerStr(setup.solar))
		fout.write('  <li>Battery: %s</li>\n' % energyStr(setup.battery))
		fout.write('</ul>\n')
		
		fout.write('<h1>Workload</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Workload: %s</li>\n' % scenario.workload.title())
		fout.write('  <li>Turn on/off: %s</li>\n' % ('V' if setup.turnoff else '-'))
		fout.write('  <li>Deferrable: %s</li>\n' % ('V' if setup.deferrable else '-'))
		fout.write('</ul>\n')
		
		fout.write('<h1>Cost</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Brown energy: %s</li>\n' % costStr(cost.energy))
		fout.write('  <li>Brown peak power: %s</li>\n' % costStr(cost.peak))
		fout.write('  <li>OPEX: %s</li>\n' % costStr(cost.getOPEX()))
		fout.write('  <li>CAPEX: %s</li>\n' % costStr(cost.getCAPEX()))
		fout.write('  <li>Total: %s</li>\n' % costStr(cost.getTotal()))
		fout.write('</ul>\n')
		
		fout.write('<h1>Battery</h1>\n')
		numdischarges, totaldischarge, maxdischarge, lifetime = getDepthOfDischarge(LOG_PATH+getFilename(scenario, setup)+'.log')
		fout.write('<ul>\n')
		fout.write('  <li>Number of discharges: %d</li>\n' % numdischarges)
		if numdischarges>0:
			fout.write('  <li>Average discharge: %.1f%%</li>\n' % (totaldischarge/numdischarges))
			fout.write('  <li>Maximum discharge: %.1f%%</li>\n' % (maxdischarge))
			fout.write('  <li>Total discharge: %.1f%%</li>\n' % totaldischarge)
			fout.write('  <li>Lifetime: %.1f%% (%.1f years)</li>\n' % (lifetime, 100.0/lifetime))
		fout.write('</ul>\n')
		
		fout.write('<h1>Log</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li><a href="%s">Log file</a></li>\n' % (getFilename(scenario, setup)+'.log'))
		fout.write('</ul>\n')
		
		# Figure for each month
		fout.write('<h1>Graphics</h1>\n')
		for i in range(1, 12+1):
			fout.write('<h2>%s</h2>\n' % (datetime.date(2012, i, 1).strftime('%B')))
			fout.write('<img src="%s"/><br/>\n' % ('img/'+getFilename(scenario, setup)+'/'+str(i)+'.png'))
			fout.write('<img src="%s"/><br/>\n' % ('img/'+getFilename(scenario, setup)+'/'+str(i)+'-day.png'))
		
		# Footer
		fout.write('</body>\n')
		fout.write('</html>\n')

"""
Draws an HTML bar chart
"""
def getBarChart(vals, maxval, width=100, height=15, color='blue'):
	out = ''
	out += '<table border="0" cellspacing="0" cellpadding="0">'
	out += '<tr height="%d">' % height
	if isinstance(color, str):
		colors = [color, 'yellow', 'red', 'green', 'orange', 'black', 'blue']
	else:
		colors = color + ['yellow', 'red', 'green', 'orange', 'black', 'blue']
	i=0
	total = 0
	for val in vals:
		if not math.isinf(val):
			out += '<td width="%dpx" bgcolor="%s" title="%.1f"/>' % (width*1.0*val/maxval, colors[i%len(colors)], val)
		total += val
		i+=1
	if not math.isinf(total):
		out += '<td width="%dpx"/>' % (width*1.0*(maxval-total)/maxval)
	out += '</tr>'
	out += '</table>'
	return out

"""
Write a table header for the experiments
"""
def writeExperimentHeader(fout):
	# First row header
	fout.write('  <tr>\n')
	fout.write('    <th></th>\n')
	fout.write('    <th colspan="5"></th>\n') #fout.write('<th colspan="5">Scenario</th>\n')
	fout.write('    <th colspan="4"></th>\n') #fout.write('<th colspan="4">Setup</th>\n')
	fout.write('    <th colspan="9">Cost</th>\n')
	fout.write('    <th colspan="1">Lifetime</th>\n')
	fout.write('    <th colspan="2">Savings</th>\n')
	fout.write('  </tr>\n')
	# Second row header
	fout.write('  <tr>\n')
	# Setup
	fout.write('    <th></th>\n')
	fout.write('    <th width="70px">DC Size</th>\n')
	fout.write('    <th width="70px">Period</th>\n')
	fout.write('    <th width="80px">Location</th>\n')
	fout.write('    <th width="80px">Net meter</th>\n')
	fout.write('    <th width="80px">Workload</th>\n')
	fout.write('    <th width="70px">Solar</th>\n')
	fout.write('    <th width="70px">Battery</th>\n')
	fout.write('    <th width="70px">Delay</th>\n')
	fout.write('    <th width="70px">On/off</th>\n')
	# Cost
	fout.write('    <th width="80px">Energy</th>\n')
	fout.write('    <th width="80px">Peak</th>\n')
	fout.write('    <th width="150px" colspan="2">OPEX</th>\n')
	fout.write('    <th width="80px">CAPEX</th>\n')
	fout.write('    <th width="150px" colspan="2">Total (1 year)</th>\n')
	fout.write('    <th width="150px" colspan="2">Total (%d years)</th>\n' % TOTAL_YEARS)
	# Lifetime
	fout.write('    <th width="80px">Battery</th>\n')
	# Saving
	fout.write('    <th width="80px">Yearly</th>\n')
	fout.write('    <th width="80px">Ammort</th>\n')
	fout.write('  </tr>\n')

"""
Write a line summarizing an experiment
"""
def writeExperimentLine(fout, scenario, setup, cost, batterylifetime, basesetup, basecost):
	fout.write('<tr>\n')
	# Experiment progress
	experimentDescription = getBarChart([setup.progress, 100-setup.progress], 100, width=75, color=['green', '#C0C0C0'])
	if cost.energy > 0.0 or cost.peak > 0.0 or cost.capex > 0.0:
		experimentDescription = 'R'
	if setup == basesetup:
		experimentDescription = '<b>'+experimentDescription+'</b>'
	fout.write('<td align="center"><a href="%s">%s</a></td>\n' % (getFilename(scenario, setup)+'.html', experimentDescription))
	# Setup
	fout.write('<td align="center">%s</td>\n' % (powerStr(setup.itsize)))
	fout.write('<td align="right">%s</td>\n' % (timeStr(scenario.period)))
	fout.write('<td align="right">%s</td>\n' % (setup.location.replace('_', ' ').title()[0:10]))
	fout.write('<td align="right">%.1f%%</td>\n' % (scenario.netmeter*100.0))
	fout.write('<td align="right">%s</td>\n' % (scenario.workload.title()))
	# Solar
	if setup.solar == 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	else:
		fout.write('<td align="right">%s</td>\n' % powerStr(setup.solar))
	# Battery
	if setup.battery == 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	else:
		fout.write('<td align="right">%s</td>\n' % energyStr(setup.battery))
	# Deferrable
	fout.write('<td align="center">%s</td>\n' % ('<font color="green">&#10003;</font>' if setup.deferrable else '<font color="#999999">&#9747;</font>'))
	# Turn on/off nodes
	fout.write('<td align="center">%s</td>\n' % ('<font color="green">&#10003;</font>' if setup.turnoff else '<font color="#999999">&#9747;</font>'))
	# Costs
	fout.write('<td align="right">%s</td>\n' % costStr(cost.energy))
	fout.write('<td align="right">%s</td>\n' % costStr(cost.peak))
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(cost.getOPEX()))
	fout.write('<td>\n')
	fout.write(getBarChart([cost.energy, cost.peak], 2.5*1000, width=100))
	fout.write('</td>\n')
	fout.write('<td align="right">%s</td>\n' % costStr(cost.getCAPEX()))
	# Total cost
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(cost.getTotal()))
	fout.write('<td>\n')
	fout.write(getBarChart([cost.energy, cost.peak, cost.capex], 16*1000, width=150))
	fout.write('</td>\n')
	# Total in N years
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX()))
	fout.write('<td>\n')
	fout.write(getBarChart([cost.energy*TOTAL_YEARS, cost.peak*TOTAL_YEARS, cost.capex], 44*1000, width=150))
	fout.write('</td>\n')
	
	# Calculate ammortization
	# Saving compare to baseline
	saveopexyear = basecost.getOPEX() - cost.getOPEX()
	savecapex =  cost.getCAPEX() - basecost.getCAPEX()
	ammortization = float(savecapex)/float(saveopexyear) if saveopexyear != 0.0 else 0.0
	
	# Lifetime battery
	if batterylifetime != None:
		batterylifetime = 100.0/lifetime
		if saveopexyear < 0:
			fout.write('<td align="right" width="80px"><font color="red">%.1fy</font></td>\n' % (batterylifetime))
		elif batterylifetime >= ammortization:
			if batterylifetime > 100:
				fout.write('<td align="right" width="80px"><font color="#999999">No use</font></td>\n')
			else:
				fout.write('<td align="right" width="80px"><font color="green">%.1fy</font></td>\n' % (batterylifetime))
		else:
			fout.write('<td align="right" width="80px"><font color="#999999">%.1fy</font></td>\n' % (batterylifetime))
	else:
		fout.write('<td align="right" width="80px"><font color="#999999">&#9747;</font></td>\n')

	# Costs
	if saveopexyear < 0:
		fout.write('<td align="right"><font color="#FF0000">%s</font></td>\n' % costStr(saveopexyear))
	else:
		fout.write('<td align="right">%s</td>\n' % costStr(saveopexyear))
	# Amortization
	if saveopexyear < 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	elif ammortization == 0:
		fout.write('<td align="center"></td>\n')
	elif ammortization < TOTAL_YEARS:
		fout.write('<td align="right">%.1fy</td>\n' % ammortization)
	else:
		fout.write('<td align="right"><font color="#FF0000">%.1fy</font></td>\n' % ammortization)
	fout.write('<tr/>\n')
	
	

# Parsing
if __name__ == "__main__":
	# Collect results by checking all files in the log directory
	print 'Collecting results...'
	results = {}
	for filename in sorted(os.listdir(LOG_PATH)):
		#print LOG_PATH+filename
		if filename.endswith('.log'):
			# Get data from filename
			split = filename[:-4].split('-')
			split.pop(0)
			itsize = float(split.pop(0))
			battery = int(split.pop(0))
			solar = int(split.pop(0))
			period = parseTime(split.pop(0))
			# Net metering
			netmeter = 0.0
			if split[0].startswith('net'):
				netmeter = float(split.pop(0)[4:])
			# Workload
			workload = split.pop(0)
			# Location
			location = split.pop(0)
			# Read the rest of the values
			delay = False
			alwayson = False
			greenswitch = True
			while len(split) > 0:
				value = split.pop(0)
				if value == 'on':
					alwayson = True
				elif value == 'delay':
					delay = True
				elif value == 'nogreenswitch':
					greenswitch = False
				else:
					print 'Unknown value:', value
			
			# Open file to check progress or final results
			costenergy = 0.0
			costpeak = 0.0
			costcapex = 0.0
			lastTime = 0
			try:
				with open(LOG_PATH+filename) as f:
					# Go to the end of the file
					f.seek(-2*1024, os.SEEK_END)
					f.readline()
					# Start checking from the end
					for line in f.readlines():
						if line.startswith('#'):
							line = line.replace('\n', '')
							if line.startswith('# Brown energy:'):
								costenergy = parseCost(line.split(' ')[3])
							elif line.startswith('# Peak brown power:'):
								costpeak = parseCost(line.split(' ')[4])
							elif line.startswith('# Infrastructure:'):
								costcapex = parseCost(line.split(' ')[2])
							elif line.startswith('# Total:'):
								#print 'Total:', line.split(' ')[2]
								pass
						else:
							try:
								expTime = int(line.split('\t')[0])
								if expTime > lastTime:
									lastTime = expTime
							except Exception, e:
								print 'Error reading log file', line, e
			except Exception, e:
				print 'Cannot read file', LOG_PATH+filename, e
			progress = 100.0*lastTime/period
			
			# Create data structures
			scenario = Scenario(netmeter=netmeter, period=period, workload=workload)
			setup =    Setup(itsize=itsize, solar=solar, battery=battery, location=location, deferrable=delay, turnoff=not alwayson, greenswitch=greenswitch, progress=progress)
			cost =     Cost(energy=costenergy, peak=costpeak, capex=costcapex)
			
			# Check battery lifetime
			batterylifetime = None
			if '--nobattery' not in sys.argv:
				numdischarges, totaldischarge, maxdischarge, lifetime = getDepthOfDischarge(LOG_PATH+getFilename(scenario, setup)+'.log')
				if lifetime > 0:
					batterylifetime = 100.0/lifetime
			
			# Store results
			if scenario not in results:
				results[scenario] = []
			results[scenario].append((setup, cost, batterylifetime))
	
	# Main Summary
	# ============================================================
	print 'Generating summary...'
	with open(LOG_PATH+'summary.html', 'w') as fout:
		# Header
		fout.write('<html>\n')
		fout.write('<head>\n')
		fout.write('<title>Green Datacenter Simulator results</title>\n')
		fout.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
		fout.write('</head>\n')
		fout.write('<body>\n')
		
		fout.write('<h1>Workloads</h1>\n')
		fout.write('<table>\n')
		fout.write('<thead>\n')
		fout.write('<tr>\n')
		fout.write('  <th colspan="3"></th>\n')
		fout.write('  <th colspan="6">Non-deferrable</th>\n')
		fout.write('  <th colspan="6">Deferrable</th>\n')
		fout.write('</tr>\n')
		fout.write('<tr>\n')
		fout.write('  <th></th>\n')
		fout.write('  <th colspan="2">Base cost</th>\n')
		fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
		fout.write('  <th width="160px" colspan="2">Solar</th>\n')
		fout.write('  <th width="160px" colspan="2">Battery</th>\n')
		fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
		fout.write('  <th width="160px" colspan="2">Solar</th>\n')
		fout.write('  <th width="160px" colspan="2">Battery</th>\n')
		fout.write('</tr>\n')
		fout.write('</thead>\n')
		fout.write('<tbody>\n')
		for scenario in sorted(results.keys()):
			# Get experiment baseline
			basesetup, basecost, basebatterylifetime = sorted(results[scenario], key=itemgetter(0))[0]
			for setup, cost, batterylifetime in results[scenario]:
				if setup.solar==0 and setup.battery==0 and setup.deferrable==False and setup.turnoff==True:
					basesetup = setup
					basecost = cost
					#if setup.location=='NEWARK_INTERNATIONAL_ARPT':
					break
			# Get experiment best result
			# Print experiment
			fout.write('<tr>\n')
			fout.write('  <td><a href="summary-%s.html">%s</a></td>\n' % (scenario.workload, scenario.workload.title()))
			# Base
			fout.write('  <td>%s</td>\n' % costStr(basecost.getOPEX()*TOTAL_YEARS + basecost.getCAPEX()))
			fout.write('  <td>' + getBarChart([basecost.energy*TOTAL_YEARS, basecost.peak*TOTAL_YEARS, basecost.capex], 24*1000)+'</td>\n')
			
			# Best non deferrable
			bestsetup, bestcost, bestbatterylifetime = basesetup, basecost, basebatterylifetime
			for setup, cost, batterylifetime in results[scenario]:
				if cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX() < bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX():
					if not setup.deferrable:
						bestsetup = setup
						bestcost = cost
			fout.write('  <td><a href="%s.html">%s</a></td>\n' % (getFilename(scenario, bestsetup), costStr(bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX())))
			fout.write('  <td>' + getBarChart([bestcost.energy*TOTAL_YEARS, bestcost.peak*TOTAL_YEARS, bestcost.capex], 24*1000)+'</td>\n')
			fout.write('  <td align="right">%s</td>\n' % powerStr(bestsetup.solar))
			fout.write('  <td>' + getBarChart([bestsetup.solar], 4.8*1000, color='green')+'</td>\n')
			fout.write('  <td align="right">%s</td>\n' % energyStr(bestsetup.battery))
			fout.write('  <td>' + getBarChart([bestsetup.battery], 32*1000, color='yellow')+'</td>\n')
			# Best non-deferrable
			bestsetup, bestcost, bestbatterylifetime = basesetup, basecost, basebatterylifetime
			for setup, cost, batterylifetime in results[scenario]:
				if cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX() < bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX():
					if setup.deferrable:
						bestsetup = setup
						bestcost = cost
			fout.write('  <td><a href="%s.html">%s</a></td>\n' % (getFilename(scenario, bestsetup), costStr(bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX())))
			fout.write('  <td>' + getBarChart([bestcost.energy*TOTAL_YEARS, bestcost.peak*TOTAL_YEARS, bestcost.capex], 24*1000)+'</td>\n')
			fout.write('  <td align="right">%s</td>\n' % powerStr(bestsetup.solar))
			fout.write('  <td>' + getBarChart([bestsetup.solar], 4.8*1000, color='green')+'</td>\n')
			fout.write('  <td align="right">%s</td>\n' % energyStr(bestsetup.battery))
			fout.write('  <td>' + getBarChart([bestsetup.battery], 32*1000, color='yellow')+'</td>\n')
			fout.write('</tr>\n')
		fout.write('</tbody>\n')
		fout.write('</table>\n')
		
		# Add 3D figures to the summary page
		i=0
		fout.write('<table>\n')
		fout.write('<tr>\n')
		for scenario in sorted(results.keys()):
			fout.write('<td>\n')
			fout.write('<h2>%s</h2>\n' % scenario.workload.title())
			imgfile =  '3d-'+str(scenario)+'.svg'
			fout.write('<a href="summary-%s.html"><img src="%s" width="400px"></a>\n' % (scenario.workload, imgfile))
			fout.write('</td>\n')
			i+=1
			if i%4 == 0:
				fout.write('<tr>\n')
				fout.write('</tr>\n')
		fout.write('</tr>\n')
		fout.write('</table>\n')
		
		fout.write('<h1>Locations</h1>\n')
		locations = []
		for scenario in sorted(results.keys()):
			for setup, cost, batterylifetime in results[scenario]:
				if setup.location not in locations:
					locations.append(setup.location)
		for location in locations:
			fout.write('<h2>%s</h2>\n' % location.replace('_', ' ').title())
			fout.write('<table>\n')
			fout.write('<thead>\n')
			fout.write('<tr>\n')
			fout.write('  <th colspan="3"></th>\n')
			fout.write('  <th colspan="6">Non-deferrable</th>\n')
			fout.write('  <th colspan="6">Deferrable</th>\n')
			fout.write('</tr>\n')
			fout.write('<tr>\n')
			fout.write('  <th></th>\n')
			fout.write('  <th colspan="2">Base cost</th>\n')
			fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
			fout.write('  <th width="160px" colspan="2">Solar</th>\n')
			fout.write('  <th width="160px" colspan="2">Battery</th>\n')
			fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
			fout.write('  <th width="160px" colspan="2">Solar</th>\n')
			fout.write('  <th width="160px" colspan="2">Battery</th>\n')
			fout.write('</tr>\n')
			fout.write('</thead>\n')
			fout.write('<tbody>\n')
			for scenario in sorted(results.keys()):
				# Get experiment baseline
				basesetup, basecost, basebatterylifetime = None, None, None
				for setup, cost, batterylifetime in results[scenario]:
					if setup.solar==0 and setup.battery==0 and setup.deferrable==False and setup.turnoff==True and setup.location==location:
						basesetup = setup
						basecost = cost
						break
				if basesetup != None:
					# Print experiment
					fout.write('<tr>\n')
					fout.write('  <td><a href="summary-%s.html">%s</a></td>\n' % (scenario.workload, scenario.workload.title()))
					# Base
					fout.write('  <td>%s</td>\n' % costStr(basecost.getOPEX()*TOTAL_YEARS + basecost.getCAPEX()))
					fout.write('  <td>' + getBarChart([basecost.energy*TOTAL_YEARS, basecost.peak*TOTAL_YEARS, basecost.capex], 24*1000)+'</td>\n')
					# Best non deferrable
					bestsetup, bestcost, bestbatterylifetime = basesetup, basecost, basebatterylifetime
					for setup, cost, batterylifetime in results[scenario]:
						if cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX() < bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX():
							if not setup.deferrable and setup.location==location:
								bestsetup = setup
								bestcost = cost
					fout.write('  <td><a href="%s.html">%s</a></td>\n' % (getFilename(scenario, bestsetup), costStr(bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX())))
					fout.write('  <td>' + getBarChart([bestcost.energy*TOTAL_YEARS, bestcost.peak*TOTAL_YEARS, bestcost.capex], 24*1000)+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % powerStr(bestsetup.solar))
					fout.write('  <td>' + getBarChart([bestsetup.solar], 4.8*1000, color='green')+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % energyStr(bestsetup.battery))
					fout.write('  <td>' + getBarChart([bestsetup.battery], 32*1000, color='yellow')+'</td>\n')
					# Best non-deferrable
					bestsetup, bestcost, bestbatterylifetime = basesetup, basecost, basebatterylifetime
					for setup, cost, batterylifetime in results[scenario]:
						if cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX() < bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX():
							if setup.deferrable and setup.location==location:
								bestsetup = setup
								bestcost = cost
					fout.write('  <td><a href="%s.html">%s</a></td>\n' % (getFilename(scenario, bestsetup), costStr(bestcost.getOPEX()*TOTAL_YEARS + bestcost.getCAPEX())))
					fout.write('  <td>' + getBarChart([bestcost.energy*TOTAL_YEARS, bestcost.peak*TOTAL_YEARS, bestcost.capex], 24*1000)+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % powerStr(bestsetup.solar))
					fout.write('  <td>' + getBarChart([bestsetup.solar], 4.8*1000, color='green')+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % energyStr(bestsetup.battery))
					fout.write('  <td>' + getBarChart([bestsetup.battery], 32*1000, color='yellow')+'</td>\n')
					fout.write('</tr>\n')
			fout.write('</tbody>\n')
			fout.write('</table>\n')
		
		
		fout.write('<h1>All experiments</h1>\n')
		fout.write('<a href="summary-experiments.html">All experiments</a>\n')
		
		
		# Footer
		fout.write('</body>\n')
		fout.write('</html>\n')
	
	# All experiments
	# ============================================================
	print 'Generating all experiments summary...'
	with open(LOG_PATH+'summary-experiments.html', 'w') as fout:
		# Header
		fout.write('<html>\n')
		fout.write('<head>\n')
		fout.write('<title>Green Datacenter Simulator results</title>\n')
		fout.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
		fout.write('</head>\n')
		fout.write('<body>\n')
		
		# All experiments
		fout.write('<h1>All experiments</h1>\n')
		# Table header
		fout.write('<table>\n')
		fout.write('<thead>\n')
		writeExperimentHeader(fout)
		fout.write('</thead>\n')
		# Table body
		fout.write('<tbody>\n')
		for scenario in sorted(results.keys()):
			# Get data
			try:
				# Get experiment baseline
				basesetup, basecost, basebatterylifetime = sorted(results[scenario], key=itemgetter(0))[0]
				for setup, cost, batterylifetime in results[scenario]:
					if setup.solar==0 and setup.battery==0 and setup.deferrable==False and setup.turnoff==True:
						basesetup = setup
						basecost = cost
						if setup.location=='NEWARK_INTERNATIONAL_ARPT':
							break
				
				# Draw result in a row
				for setup, cost, batterylifetime in sorted(results[scenario], key=itemgetter(0)):
					writeExperimentLine(fout, scenario, setup, cost, batterylifetime, basesetup, basecost)
			except Exception, e:
				print 'Error:', e
		# Finish table content
		fout.write('</tbody>\n')
		fout.write('</table>\n')
		# Footer
		fout.write('</body>\n')
		fout.write('</html>\n')
	
	# Scenario details
	# ============================================================
	print 'Generating scenario details...'
	for scenario in sorted(results.keys()):
		with open(LOG_PATH+'summary-%s.html' % scenario.workload, 'w') as fout:
			# Header
			fout.write('<html>\n')
			fout.write('<head>\n')
			fout.write('<title>%s</title>\n' % (scenario.workload.title()))
			fout.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
			fout.write('</head>\n')
			fout.write('<body>\n')
			
			fout.write('<h1>%s</h1>\n' % scenario.workload.title())
			# 3D Figure
			imgfile =  ''
			fout.write('<img width="800px" src="3d-'+str(scenario)+'.svg">\n')
			fout.write('<img width="800px"src="3d-'+str(scenario)+'-base.svg">\n')
			
			# All experiments
			fout.write('<table>\n')
			fout.write('<thead>\n')
			writeExperimentHeader(fout)
			fout.write('</thead>\n')
			fout.write('<tbody>\n')
			# Write data
			try:
				# Get experiment baseline
				basesetup, basecost, basebatterylifetime = sorted(results[scenario], key=itemgetter(0))[0]
				for setup, cost, batterylifetime in results[scenario]:
					#if setup.location=='NEWARK_INTERNATIONAL_ARPT' and 
					if setup.solar==0 and setup.battery==0 and setup.deferrable==False and setup.turnoff==True:
						basesetup = setup
						basecost = cost
						if setup.location=='NEWARK_INTERNATIONAL_ARPT':
							break
				
				# Draw result in a row
				for setup, cost, batterylifetime in sorted(results[scenario], key=itemgetter(0)):
					writeExperimentLine(fout, scenario, setup, cost, batterylifetime, basesetup, basecost)
			except Exception, e:
				print 'Error:', e
			# Finish table content
			fout.write('</tbody>\n')
			fout.write('</table>\n')
			# Footer
			fout.write('</body>\n')
			fout.write('</html>\n')
	
	# 3D Figures
	# ============================================================
	if '--summary' not in sys.argv:
		print 'Generating 3D figures...'
		for scenario in sorted(results.keys()):
			# Data for 3D figure
			figure3d = {}
			figure3dlocations = []
			
			# Data for 3D Figure
			for setup, cost, batterylifetime in sorted(results[scenario], key=itemgetter(0)):
				if setup.turnoff:
					if setup.location not in figure3dlocations:
						figure3dlocations.append(setup.location)
					if (setup.solar, setup.battery) not in figure3d:
						figure3d[setup.solar, setup.battery] = {}
					figure3d[setup.solar, setup.battery][setup.deferrable, setup.location] = cost.energy*TOTAL_YEARS + cost.peak*TOTAL_YEARS + cost.capex
			
			# Generate each one of the 3D figures
			datafile =     LOG_PATH+'3d-'+str(scenario)+'.data'
			imgfile =      LOG_PATH+'3d-'+str(scenario)+'.svg'
			imgfilebase =  LOG_PATH+'3d-'+str(scenario)+'-base.svg'
			#with open('3d.data', 'w') as f3ddata:
			with open(datafile, 'w') as f3ddata:
				f3ddata.write('# '+' '.join(figure3dlocations)+'\n')
				for solar, battery in sorted(figure3d):
					aux = [99999999] * 2 * len(figure3dlocations)
					for location in figure3dlocations:
						if (False, location) in figure3d[solar, battery]:
							aux[figure3dlocations.index(location)*2+0] = figure3d[solar, battery][False, location]
						if (True, location) in figure3d[solar, battery]:
							aux[figure3dlocations.index(location)*2+1] = figure3d[solar, battery][True, location]
					out = '%11.1f\t%11.1f' % (solar, battery)
					for i in range(0, len(figure3dlocations)):
						out += '\t%11.2f\t%11.2f' % (aux[i*2+0], aux[i*2+1])
					f3ddata.write(out+'\n')
			call(['bash', '3dplot.sh', datafile, imgfile])
			call(['bash', '3dplot.sh', datafile, imgfilebase, '1'])
	
	# Experiments details
	# ============================================================
	if '--summary' not in sys.argv:
		# Generate detailed page for experiment
		print 'Generating details...'
		total = 0
		for scenario in sorted(results.keys()):
			for setup, cost, batterylifetime in sorted(results[scenario], key=itemgetter(0)): # , cmp=cmpsetup
				saveDetails(scenario, setup, cost)
				total += 1
	
	# Figures
	# ============================================================
	if '--summary' not in sys.argv:
		# Generate figures
		print 'Generating monthly figures...'
		current = 0
		last = datetime.datetime.now()
		for scenario in sorted(results.keys(), reverse=False):
			for setup, cost, batterylifetime in sorted(results[scenario], key=itemgetter(0), reverse=False): # , cmp=cmpsetup
				generateFigures(scenario, setup)
				current+=1
				if datetime.datetime.now()-last > datetime.timedelta(seconds=30):
					print '%.1f%%' % (100.0*current/total)
					last = datetime.datetime.now()
