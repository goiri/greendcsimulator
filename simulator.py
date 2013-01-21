#!/usr/bin/env python2.7

from optparse import OptionParser

from conf import *
from commons import *
from infrastructure import *
from location import *
from workload import *

# GreenSwitch
import sys
sys.path.append('/home/goiri/hadoop-parasol')
sys.path.append('/home/goirix/hadoop-parasol')
from parasolsolver import ParasolModel
from parasolsolvercommons import TimeValue

"""
Simulator
TODO list:
* Deferrable workloads
* Battery lifetime model
* Amortization periods calculation
* Change options from command line
"""
class Simulator:
	def __init__(self, infrafile, locationfile, workloadfile, period=SIMULATIONTIME):
		self.infra = Infrastructure(infrafile)
		self.location = Location(locationfile)
		self.workload = Workload(workloadfile)
		self.period = period
	
	def run(self):
		costbrownenergy = 0.0
		costbrownpower = 0.0
		peakbrown = 0.0
		peakbrownaccountingtime = 0
		# No previous load
		prevload = 0.0
		# We start with full capacity
		battery = self.infra.battery.capacity
		
		# Datacenter
		# Location traces
		# Workload
		print 'Simulation period: %s' % (timeStr(self.period))
		if self.workload.deferrable:
			print 'Deferrable workload'
		for t in range(0, self.period/TIMESTEP):
			time = t*TIMESTEP
			brownenergyprice = self.location.getBrownPrice(time)
			temperature = self.location.getTemperature(time)
			workload = self.workload.getLoad(time)
			coolingpower = self.infra.cooling.getPower(temperature)
			netmetering = self.location.netmetering
			
			# Green power
			solar = self.location.getSolar(time)
			solarpower = solar * self.infra.solar.capacity * self.infra.solar.efficiency
			wind = self.location.getWind(time)
			windpower = wind * self.infra.wind.capacity * self.infra.wind.efficiency
			greenpower = solarpower + windpower
			
			# Apply GreenSwitch policy
			solver = ParasolModel()
			solver.options.optCost = 1.0
			# Load
			solver.options.loadDelay = self.workload.deferrable
			solver.options.prevLoad = prevload
			solver.options.minSize = self.workload.minimum
			solver.options.maxSize = self.infra.it.getMaxPower()
			# Power infrastructure costs
			solver.options.netMeter = self.location.netmetering
			solver.options.peakCost = self.location.brownpowerprice
			solver.options.previousPeak = 0.95*peakbrown
			# Battery
			solver.options.batCap = self.infra.battery.capacity
			solver.options.batIniCap = battery
			#solver.options.batDischargeMax = 0.235294117647
			solver.options.batDischargeMax = 0.20 # 20% DoD
			solver.options.batEfficiency = self.infra.battery.efficiency
			
			#solver.options.debug = 3
			# TODO
			"""
			print timeStr(time)
			print 'Input:'
			print "  Size:", solver.options.minSize, solver.options.maxSize, 'W'
			print "  Max time:", solver.options.maxTime, 'h'
			print "  Peak cost:", solver.options.peakCost
			print "  Batt:", solver.options.batIniCap, solver.options.batCap, solver.options.batDischargeMax, '%.1f%%' % (100.0*solver.options.batIniCap/solver.options.batCap)
			"""
						
			# Fill data with predictions
			greenAvail = []
			brownPrice = []
			worklPredi = []
			for predhour in range(0, 24):
				g = self.location.getSolar(time + predhour*60*60) * self.infra.solar.capacity * self.infra.solar.efficiency
				b = self.location.getBrownPrice(time + predhour*60*60)
				w = self.workload.getLoad(time + predhour*60*60) + self.infra.cooling.getPower(self.location.getTemperature(time + predhour*60*60))
				greenAvail.append(TimeValue(predhour*60*60, g))
				brownPrice.append(TimeValue(predhour*60*60, b))
				worklPredi.append(TimeValue(predhour*60*60, w))
			
			obj, sol = solver.solvePeak(greenAvail=greenAvail, brownPrice=brownPrice, load=worklPredi, previousPeak=0.95*peakbrown, stateChargeBattery=False)
			
			# Check if GreenSwitch gives a solution
			if sol == None:
				# Default behavior
				print "No solution at", timeStr(time)
				brownpower = workload + coolingpower - greenpower
				netpower = 0.0
				if brownpower < 0.0:
					netpower = -1.0*brownpower
					brownpower = 0.0
				prevload = 0.0
			else:
				# Calculate brown power and net metering
				brownpower = sol['BattBrown[0]'] + sol['LoadBrown[0]']
				netpower = sol['NetGreen[0]']
				# Battery
				batdischarge = sol['LoadBatt[0]']
				batcharge = sol['BattBrown[0]'] + sol['BattGreen[0]']
				batpower = self.infra.battery.efficiency * batcharge - batdischarge
				battery += (TIMESTEP/3600.0) * batpower
				# Load load
				workload = round(self.workload.getLoad(time) + self.infra.cooling.getPower(self.location.getTemperature(time)), 4)
				execload = round(sol['LoadBatt[0]'] + sol['LoadGreen[0]'] + sol['LoadBrown[0]'], 4)
				# Delay load
				if self.workload.deferrable:
					# Delayed load = Current workload - executed load
					prevload += workload - execload
				# Debug
				'''
				print 'Deferrable workload:'
				print ' Time    ', timeStr(time)
				print ' Workload', workload
				print ' Load    ', execload
				print ' Delay   ', (workload - execload)
				print ' To delay', prevload
				'''
			# Peak brown
			if brownpower > peakbrown:
				peakbrown = brownpower
			
			# DEBUG
			#print timeStr(time), sol['PeakBrown'], peakbrown
			#print timeStr(time), '\t%.1f'%brownpower, '\t%.1f'%greenpower, '\t%.1f'%netpower, '\t%.1f'%batcharge, '\t%.1f'%batdischarge, '\t%.1f' % (100.0*solver.options.batIniCap/solver.options.batCap), '\t%.1f' % (solver.options.previousPeak)
			
			# Operational costs
			# Grid electricity
			costbrownenergy += (TIMESTEP/SECONDS_HOUR) * brownpower/1000.0 * brownenergyprice # (seconds -> hours) * kW * $/kWh
			# Net metering
			costbrownenergy -= (TIMESTEP/SECONDS_HOUR) * netpower/1000.0 * brownenergyprice * netmetering # (seconds -> hours) * kW * $/kWh * %
			
			# Peak power accounting every month
			peakbrownaccountingtime += TIMESTEP
			if peakbrownaccountingtime >= 30*24*60*60: # One month
				#print 'New month', timeStr(time) # TODO
				costbrownpower += self.location.brownpowerprice * peakbrown/1000.0
				# Reseat accounting
				peakbrownaccountingtime = 0
				peakbrown = 0.0
			
			#print timeStr(time), '\t$%.2f/kWh' % brownenergyprice, '\t%.2fW' % greenpower, '\t%.2fW' % netpower, '\t%.2fW' % brownpower, '\t%.2fC' % temperature, '\t%.2fW' % workload
		
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


if __name__ == "__main__":
	parser = OptionParser(usage="usage: %prog [options] filename", version="%prog 1.0")
	# Data files
	parser.add_option('-w', '--workload', dest='workload', help='specify the workload file',       default=DATA_PATH+'/workload/variable.workload')
	parser.add_option('-l', '--location', dest='location', help='specify the location file',       default=DATA_PATH+'/parasol.location')
	parser.add_option('-i', '--infra',    dest='infra',    help='specify the infrastructure file', default=DATA_PATH+'/parasol.infra')
	# Period
	parser.add_option('-p', '--period',   dest='period',   help='specify the infrastructure file', default='1y')
	# Infrastructure options
	parser.add_option('-s', '--solar',    dest='solar',   action="store_false", help='specify the infrastructure has solar')
	parser.add_option('-b', '--battery',  dest='battery', action="store_false", help='specify the infrastructure has solar')
	# Load
	parser.add_option('-d', '--delay',    dest='delay',   action="store_true",  help='specify if we can delay the load')
	
	(options, args) = parser.parse_args()
	
	# Initialize simulator
	simulator = Simulator(options.infra, options.location, options.workload, parseTime(options.period))
	if options.battery == False:
		simulator.infra.battery.capacity = 0.0
	if options.solar == False:
		simulator.infra.solar.capacity = 0.0
	if options.delay == True:
		simulator.workload.deferrable = True
	simulator.infra.printSummary()
	
	# Run simulation
	simulator.run()
