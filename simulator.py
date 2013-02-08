#!/usr/bin/env python2.7

from optparse import OptionParser

from conf import *
from commons import *
from infrastructure import *
from location import *
from workload import *
from datetime import datetime, timedelta

# GreenSwitch
import sys
#sys.path.append('/home/goiri/hadoop-parasol')
#sys.path.append('/home/goirix/hadoop-parasol')
sys.path.append('parasolsolver')
from parasolsolver import ParasolModel
from parasolsolvercommons import TimeValue

"""
Simulator
TODO list:
* Check why in some experiments the executed load is higher than the load
* Add DC size to log name
* Infrastructure for long experiments in multiple servers (50%)
* Battery lifetime model (50% parser)
* Provide better data for the power consumption of the ATOMs
* On/off peak prices around the world are tricky. We dont have summar/winter pricings
"""
class Simulator:
	def __init__(self, infrafile, locationfile, workloadfile, period=SIMULATIONTIME, turnoff=True):
		self.infra = Infrastructure(infrafile)
		self.location = Location(locationfile)
		self.workload = Workload(workloadfile)
		self.period = period
		# Policy
		self.greenswitch = True
		# Workload
		self.turnoff = turnoff
	
	def getLogFilename(self):
		filename = LOG_PATH+'/result'
		# Size
		filename += '-%.1f' % self.infra.it.getMaxPower()
		# Solar
		filename += '-%d' % self.infra.battery.capacity
		# Battery
		filename += '-%d' % self.infra.solar.capacity
		# Period
		filename += '-%s' % timeStr(self.period)
		# Net metering
		if self.location.netmetering > 0.0:
			filename += '-net%.2f' % self.location.netmetering
		# Workload
		workloadname = self.workload.filename
		workloadname = workloadname[workloadname.rfind('/')+1:workloadname.rfind('.')]
		filename += '-%s' % workloadname
		# Location
		if self.location.name != None:
			filename += '-%s' % self.location.name
		# Delay
		if self.workload.deferrable == True:
			filename += '-delay'
		# Always on
		if self.turnoff == False:
			filename += '-on'
		# GreenSwitch
		if self.greenswitch == False:
			filename += '-nogreenswitch'
		# GreenSwitch
		filename += '.log'
		return filename
	
	"""
	Run simulation
	"""
	def run(self):
		# Costs
		costbrownenergy = 0.0
		costbrownpower = 0.0
		# Peak brown
		peakbrown = 0.0
		# Store start date for peak brown accounting
		startdate = datetime(2013, 1, 1)
		currentmonth = 1
		# No previous load
		prevload = 0.0
		# We start with full capacity
		battery = self.infra.battery.capacity
		# Battery
		batcharge = 0.0
		batdischarge = 0.0
		# State
		stateChargeBattery = False
		stateNetMeter = False
		
		# Datacenter
		# Location traces
		# Workload
		print 'Simulation period: %s' % (timeStr(self.period))
		if self.workload.deferrable:
			print 'Deferrable workload'
		if self.turnoff != False:
			print 'Turn off nodes'
			
		# Logging file
		try:
			fout = open(self.getLogFilename(), 'w')
			fout.write('# Time\tBPrice\tGreen\tNetMet\tBrown\tBatChar\tBatDisc\tBatLevel\tWorload\tCooling\tExLoad\tPrLoad\n')
		except Exception, e:
			fout = None
			print e
		
		
		# Iterate maximum time PERIOD in steps of TIMESTEP
		for t in range(0, self.period/TIMESTEP):
			time = t*TIMESTEP
			brownenergyprice = self.location.getBrownPrice(time)
			temperature = self.location.getTemperature(time)
			coolingpower = self.infra.cooling.getPower(temperature)
			netmetering = self.location.netmetering
			
			# Green power
			solar = self.location.getSolar(time)
			solarpower = solar * self.infra.solar.capacity * self.infra.solar.efficiency
			wind = self.location.getWind(time)
			windpower = wind * self.infra.wind.capacity * self.infra.wind.efficiency
			greenpower = solarpower + windpower
			
			# Apply policy
			if not self.greenswitch:
				# If we don't use GreenSwitch, there is no solution
				sol = None
			else:
				# Use GreenSwitch policy
				solver = ParasolModel()
				solver.options.optCost = 1.0
				# Load
				solver.options.loadDelay = self.workload.deferrable
				solver.options.prevLoad = prevload
				solver.options.minSize = self.infra.it.getPower(self.workload.minimum, minimum=True, turnoff=self.turnoff)
				solver.options.maxSize = self.infra.it.getMaxPower()
				# Power infrastructure costs
				solver.options.netMeter = self.location.netmetering
				solver.options.peakCost = self.location.brownpowerprice
				#solver.options.previousPeak = peakbrown
				solver.options.previousPeak = 0.95*peakbrown
				#solver.options.previousPeak = 0.0
				# Battery
				solver.options.batCap = self.infra.battery.capacity
				solver.options.batIniCap = battery
				#solver.options.batDischargeMax = 0.235294117647
				solver.options.batDischargeMax = 0.20 # 20% DoD
				solver.options.batEfficiency = self.infra.battery.efficiency
				
				# TODO DEBUG
				#solver.options.debug = 3
				"""
				print timeStr(time)
				print 'Input:'
				print "  Size:", solver.options.minSize, solver.options.maxSize, 'W'
				print "  Max time:", solver.options.maxTime, 'h'
				print "  Peak cost:", solver.options.peakCost
				print "  Batt:", solver.options.batIniCap, solver.options.batCap, solver.options.batDischargeMax, '%.1f%%' % (100.0*solver.options.batIniCap/solver.options.batCap)
				"""
				
				# TODO Workload prediction
				workloadPrediction = False
				
				# Fill data with actual values and predictions
				greenAvail = []
				brownPrice = []
				worklPredi = []
				for predhour in range(0, 24):
					# Actual values
					if predhour == 0:
						# Workload
						reqNodes = self.workload.getLoad(time)
						reqNodes = self.workload.getLoad(time)
						loadPower = self.infra.it.getPower(reqNodes, turnoff=self.turnoff)
						temperature = self.location.getTemperature(time)
						coolingPower = self.infra.cooling.getPower(temperature)
						w = loadPower + coolingPower
						worklPredi.append(TimeValue(0, w))
						# Green available
						greenAvail.append(TimeValue(0, greenpower))
						# Brown price
						b = self.location.getBrownPrice(time)
						brownPrice.append(TimeValue(0, b))
					# Predictions
					else:
						# Workload prediction
						predseconds = predhour*60*60
						#reqNodes = self.workload.getLoad(time + predseconds)
						reqNodes = 0.0
						for i in range(0, int(60.0*60.0/TIMESTEP)):
							reqNodes += self.workload.getLoad(time + predseconds + i*TIMESTEP)
						reqNodes = float(reqNodes)/(60.0*60.0/TIMESTEP)
						loadPower = self.infra.it.getPower(reqNodes, turnoff=self.turnoff)
						temperature = self.location.getTemperature(time + predseconds)
						coolingPower = self.infra.cooling.getPower(temperature)
						w = loadPower + coolingPower
						worklPredi.append(TimeValue(predseconds, w))
						# Green availability prediction: right now is perfect knowledge
						g = self.location.getSolar(time + predseconds) * self.infra.solar.capacity * self.infra.solar.efficiency
						greenAvail.append(TimeValue(predseconds, g))
						# Brown price prediction
						b = self.location.getBrownPrice(time + predseconds)
						brownPrice.append(TimeValue(predseconds, b))
				
				# Generate solution
				obj, sol = solver.solvePeak(greenAvail=greenAvail, brownPrice=brownPrice, load=worklPredi, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
				
			# Check if we have a GreenSwitch solution
			if sol == None:
				if self.greenswitch:
					print "No solution at", timeStr(time)
				# Calculate workload: Get the number of nodes required
				reqNodes = self.workload.getLoad(time)
				loadPower = self.infra.it.getPower(reqNodes, turnoff=self.turnoff)
				temperature = self.location.getTemperature(time)
				coolingPower = self.infra.cooling.getPower(temperature)
				# Default behavior
				brownpower = loadPower + coolingPower - greenpower
				netpower = 0.0
				if brownpower < 0.0:
					netpower = -1.0*brownpower
					brownpower = 0.0
				# Load
				workload = loadPower + coolingPower
				execload = workload
				# State
				stateChargeBattery = False
				if netpower > 0:
					stateNetMeter = True
				else:
					stateNetMeter = False
			else:
				# Get solution from solver
				# Calculate brown power and net metering
				brownpower = sol['BattBrown[0]'] + sol['LoadBrown[0]']
				netpower = sol['NetGreen[0]']
				# Battery
				batdischarge = sol['LoadBatt[0]']
				batcharge = sol['BattBrown[0]'] + sol['BattGreen[0]']
				# Load
				reqNodes = self.workload.getLoad(time)
				loadPower = self.infra.it.getPower(reqNodes, turnoff=self.turnoff)
				coolingPower = self.infra.cooling.getPower(self.location.getTemperature(time + predhour*60*60))
				workload = loadPower + coolingPower
				execload = round(sol['LoadBatt[0]'] + sol['LoadGreen[0]'] + sol['LoadBrown[0]'], 4)
				
				# Delay load
				if self.workload.deferrable:
					# Delayed load = Current workload - executed load
					prevload += (workload - execload)*(TIMESTEP/3600.0)
					
				# Fix solution to match actual system
				# Sometimes the solver says to run more than is there
				if execload > workload+prevload:
					execload = workload+prevload
				# If we charge, we cannot do net metering
				if batcharge>0 and netpower>0:
					netpower = 0
					batcharge += netpower
				# If we have surplus green power, use it for what is being used before
				if execload + batcharge + netpower < greenpower:
					if batcharge > 0:
						batcharge = greenpower - execload
					else:
						netpower = greenpower - execload
				
				# Charge battery
				battery += ((self.infra.battery.efficiency * batcharge) - batdischarge) * (TIMESTEP/3600.0)
				if battery > self.infra.battery.capacity:
					battery = self.infra.battery.capacity
				
				# Change state
				if batcharge > 0:
					stateChargeBattery = True
				else:
					stateChargeBattery = False
				if netpower > 0:
					stateNetMeter = True
				else:
					stateNetMeter = False
				
				# TODO DEBUG
				#print '%s\t%.2fW\t%.2fW\tPeak:%.2fW' % (timeStr(time), sol['LoadBrown[0]'], sol['LoadBatt[0]']+sol['LoadGreen[0]']+sol['LoadBrown[0]'], peakbrown)
				#print timeStr(time), prevload, workload, execload, sol['LoadBatt[0]'], sol['LoadGreen[0]'], sol['LoadBrown[0]']
				
				"""
				# TODO Debug one one particular solution
				if timeStr(time) == '17h' or timeStr(time) == '22h':
					print '======================='
					for t in range(0, solver.options.maxTime):
						print t, '%6.1f'%sol['LoadBatt['+str(t)+']'], '%6.1f'%sol['LoadGreen['+str(t)+']'], '%6.1f'%sol['LoadBrown['+str(t)+']'], worklPredi[t].v
					print '======================='
				"""
			
			# Check peak brown power
			if brownpower > peakbrown:
				peakbrown = brownpower
			
			# DEBUG
			#print timeStr(time), sol['PeakBrown'], peakbrown
			#print timeStr(time), '\t%.1f'%brownpower, '\t%.1f'%greenpower, '\t%.1f'%netpower, '\t%.1f'%batcharge, '\t%.1f'%batdischarge, '\t%.1f' % (100.0*solver.options.batIniCap/solver.options.batCap), '\t%.1f' % (solver.options.previousPeak)
			#print '%10s' % timeStr(time), '\t%6.1f' % workload, '\t%6.1f' % coolingpower, '\t%6.1f' % execload, '\t%6.1f' % (execload-workload), '\t', prevload
			
			# Account operational costs
			# Grid electricity
			costbrownenergy += (TIMESTEP/SECONDS_HOUR) * brownpower/1000.0 * brownenergyprice # (seconds -> hours) * kW * $/kWh
			# Net metering
			costbrownenergy -= (TIMESTEP/SECONDS_HOUR) * netpower/1000.0 * brownenergyprice * netmetering # (seconds -> hours) * kW * $/kWh * %
			
			# Peak power accounting every month
			if (startdate + timedelta(seconds=time)).month != currentmonth:
				costbrownpower += self.location.brownpowerprice * peakbrown/1000.0
				# Reseat accounting
				peakbrown = 0.0
				currentmonth = (startdate + timedelta(seconds=time)).month
			
			# Logging
			if fout != None:
				fout.write('%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n' % (time, brownenergyprice, greenpower, netpower, brownpower, batcharge, batdischarge, battery, workload, coolingpower, execload, prevload))
				fout.flush()
		
		# Account for the last month
		costbrownpower += self.location.brownpowerprice * peakbrown/1000.0
		
		# Infrastructure cost
		costinfrastructure = 0.0
		# Solar
		costinfrastructure += self.infra.solar.capacity * self.infra.solar.price
		# Wind
		costinfrastructure += self.infra.wind.capacity * self.infra.wind.price
		# Battery
		costinfrastructure += self.infra.battery.capacity * self.infra.battery.price
		
		# Summary
		print '$%.2f + $%.2f + $%.2f = $%.2f' % (costbrownenergy, costbrownpower, costinfrastructure, costbrownenergy+costbrownpower+costinfrastructure)
		# Log file
		if fout != None:
			fout.write('# Summary:\n')
			fout.write('# Brown energy: $%.2f\n' % (costbrownenergy))
			fout.write('# Peak brown power: $%.2f\n' % (costbrownpower))
			fout.write('# Infrastructure: $%.2f\n' % (costinfrastructure))
			fout.write('# Total: $%.2f\n' % (costbrownenergy+costbrownpower+costinfrastructure))
			fout.close()

if __name__ == "__main__":
	parser = OptionParser(usage="usage: %prog [options] filename", version="%prog 1.0")
	# Data files
	parser.add_option('-w', '--workload', dest='workload', help='specify the workload file',       default=DATA_PATH+'/workload/variable.workload')
	parser.add_option('-l', '--location', dest='location', help='specify the location file',       default=DATA_PATH+'/parasol.location')
	parser.add_option('-i', '--infra',    dest='infra',    help='specify the infrastructure file', default=DATA_PATH+'/parasol.infra')
	# Period
	parser.add_option('-p', '--period',   dest='period',   help='specify the infrastructure file', default='1y')
	# Infrastructure options
	parser.add_option('-s', '--solar',    dest='solar',     type="float", help='specify the infrastructure has solar', default=None)
	parser.add_option('-b', '--battery',  dest='battery',   type="float", help='specify the infrastructure has batteries', default=None)
	parser.add_option('--nosolar',        dest='nosolar',   action="store_true",  help='specify the infrastructure has no solar')
	parser.add_option('--nobattery',      dest='nobattery', action="store_true",   help='specify the infrastructure has no batteries')
	# GreenSwitch
	parser.add_option('-g', '--nogswitch',dest='greenswitch',action="store_false", help='specify if we use greenswitch')
	# Load
	parser.add_option('-d', '--delay',    dest='delay',    action="store_true",  help='specify if we can delay the load')
	parser.add_option('-o', '--alwayson', dest='alwayson', action="store_true",  help='specify if the system is always on')
	# Location
	parser.add_option('--net',            dest='netmeter', type="float", help='specify the net metering revenue', default=None)
	
	(options, args) = parser.parse_args()
	
	# Initialize simulator
	simulator = Simulator(options.infra, options.location, options.workload, parseTime(options.period), turnoff=not options.alwayson)
	if options.nobattery == True:
		simulator.infra.battery.capacity = 0.0
	if options.nosolar == True:
		simulator.infra.solar.capacity = 0.0
	if options.battery != None:
		simulator.infra.battery.capacity = options.battery
	if options.solar != None:
		simulator.infra.solar.capacity = options.solar
	if options.delay == True:
		simulator.workload.deferrable = True
	if options.netmeter != None:
		simulator.location.netmetering = options.netmeter
	if options.greenswitch == False:
		simulator.greenswitch = False
	simulator.infra.printSummary()
	
	# Run simulation
	simulator.run()
