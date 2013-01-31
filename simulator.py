#!/usr/bin/env python2.7

from optparse import OptionParser

from conf import *
from commons import *
from infrastructure import *
from location import *
from workload import *

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
* Battery lifetime model
"""
class Simulator:
	def __init__(self, infrafile, locationfile, workloadfile, period=SIMULATIONTIME, turnoff=True):
		self.infra = Infrastructure(infrafile)
		self.location = Location(locationfile)
		self.workload = Workload(workloadfile)
		self.period = period
		# Workload
		self.turnoff = turnoff
	
	def getLogFilename(self):
		filename = LOG_PATH+'/result'
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
		# Delay
		if self.workload.deferrable == True:
			filename += '-delay'
		# Always on
		if self.turnoff == False:
			filename += '-on'
		filename += '.log'
		return filename
	
	"""
	Calculate the load based on the number of servers
	"""
	def calculateITPower(self, numServers, minimum=False):
		power = 0.0
		reqServers = numServers
		# Walk the racks
		for rackId in sorted(self.infra.it.racks.keys()):
			# Add switch power
			rackUtilization = 1.0
			if reqServers < len(self.infra.it.racks[rackId].servers):
				rackUtilization = math.ceil(reqServers) / float(len(self.infra.it.racks[rackId].servers))
			powerSwitchIdle = self.infra.it.racks[rackId].switch.poweridle
			powerSwitchPeak = self.infra.it.racks[rackId].switch.powerpeak
			power += powerSwitchIdle + rackUtilization*(powerSwitchPeak - powerSwitchIdle)
			
			# Walk the servers in the rack
			for serverId in self.infra.it.racks[rackId].servers:
				# Add server power
				if reqServers > 0:
					if minimum:
						power += self.infra.it.racks[rackId].servers[serverId].poweridle
					else:
						power += self.infra.it.racks[rackId].servers[serverId].powerpeak
					reqServers -= 1
					if reqServers < 0:
						reqServers = 0
				elif self.turnoff == False:
					power += self.infra.it.racks[rackId].servers[serverId].poweridle
				else:
					power += self.infra.it.racks[rackId].servers[serverId].powers3
		return power
	
	"""
	Run simulation
	"""
	def run(self):
		costbrownenergy = 0.0
		costbrownpower = 0.0
		peakbrown = 0.0
		peakbrownaccountingtime = 0
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
			
			# Apply GreenSwitch policy
			solver = ParasolModel()
			solver.options.optCost = 1.0
			# Load
			solver.options.loadDelay = self.workload.deferrable
			solver.options.prevLoad = prevload
			solver.options.minSize = self.calculateITPower(self.workload.minimum, minimum=True)
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
				reqNodes = self.workload.getLoad(time + predhour*60*60)
				loadPower = self.calculateITPower(reqNodes)
				coolingPower = self.infra.cooling.getPower(self.location.getTemperature(time + predhour*60*60))
				w = loadPower + coolingPower
				g = self.location.getSolar(time + predhour*60*60) * self.infra.solar.capacity * self.infra.solar.efficiency
				b = self.location.getBrownPrice(time + predhour*60*60)
				greenAvail.append(TimeValue(predhour*60*60, g))
				brownPrice.append(TimeValue(predhour*60*60, b))
				worklPredi.append(TimeValue(predhour*60*60, w))
			
			# Generate solution
			#peakbrown = 0.0
			obj, sol = solver.solvePeak(greenAvail=greenAvail, brownPrice=brownPrice, load=worklPredi, previousPeak=0.95*peakbrown, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
			
			# Check if GreenSwitch gives a solution
			if sol == None:
				print "No solution at", timeStr(time)
				# Calculate workload: Get the number of nodes required
				reqNodes = self.workload.getLoad(time)
				loadPower = self.calculateITPower(reqNodes)
				coolingPower = self.infra.cooling.getPower(self.location.getTemperature(time + predhour*60*60))
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
				# Calculate brown power and net metering
				brownpower = sol['BattBrown[0]'] + sol['LoadBrown[0]']
				netpower = sol['NetGreen[0]']
				# Battery
				batdischarge = sol['LoadBatt[0]']
				batcharge = sol['BattBrown[0]'] + sol['BattGreen[0]']
				batpower = self.infra.battery.efficiency * batcharge - batdischarge
				battery += (TIMESTEP/3600.0) * batpower
				# Load
				reqNodes = self.workload.getLoad(time)
				loadPower = self.calculateITPower(reqNodes)
				coolingPower = self.infra.cooling.getPower(self.location.getTemperature(time + predhour*60*60))
				workload = loadPower + coolingPower
				execload = round(sol['LoadBatt[0]'] + sol['LoadGreen[0]'] + sol['LoadBrown[0]'], 4)
				
				#print timeStr(time), prevload, workload, execload, sol['LoadBatt[0]'], sol['LoadGreen[0]'], sol['LoadBrown[0]']
				# Delay load
				if self.workload.deferrable:
					# Delayed load = Current workload - executed load
					prevload += workload - execload
				# State
				if sol['BattBrown[0]'] + sol['BattGreen[0]'] > 0:
					stateChargeBattery = True
				else:
					stateChargeBattery = False
				if sol['NetGreen[0]'] > 0:
					stateNetMeter = True
				else:
					stateNetMeter = False
			
			# Peak brown power
			if brownpower > peakbrown:
				peakbrown = brownpower
			
			# DEBUG
			#print timeStr(time), sol['PeakBrown'], peakbrown
			#print timeStr(time), '\t%.1f'%brownpower, '\t%.1f'%greenpower, '\t%.1f'%netpower, '\t%.1f'%batcharge, '\t%.1f'%batdischarge, '\t%.1f' % (100.0*solver.options.batIniCap/solver.options.batCap), '\t%.1f' % (solver.options.previousPeak)
			#print '%10s' % timeStr(time), '\t%6.1f' % workload, '\t%6.1f' % coolingpower, '\t%6.1f' % execload, '\t%6.1f' % (execload-workload), '\t', prevload
			
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
			
			# Logging
			if fout != None:
				fout.write('%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n' % (time, brownenergyprice, greenpower, netpower, brownpower, batcharge, batdischarge, battery, workload, coolingpower, execload, prevload))

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
	parser.add_option('--nosolar',        dest='nosolar',   action="store_true", help='specify the infrastructure has no solar')
	parser.add_option('--nobattery',      dest='nobattery', action="store_true", help='specify the infrastructure has no batteries')
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
	simulator.infra.printSummary()
	
	# Run simulation
	simulator.run()
