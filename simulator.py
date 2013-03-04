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
* On/off peak prices around the world are tricky. We dont have summar/winter pricings
TEST list:
* Compression of the load when it is deferred
* New proposal for peak power and energy accounting
"""
class Simulator:
	def __init__(self, infrafile, locationfile, workloadfile, period=SIMULATIONTIME, turnoff=True):
		self.infra = Infrastructure(infrafile)
		self.location = Location(locationfile)
		self.workload = Workload(workloadfile)
		self.period = period
		# turn on/off servers
		self.turnoff = turnoff
		# Policy
		self.greenswitch = True
		# Battery management
		self.batteryManagement = True
	
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
		# Cooling
		if self.infra.cooling.coolingtype != None:
			filename += '-cool'+self.infra.cooling.coolingtype
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
		prevLoad = 0.0
		prevNodes = 0.0
		# We start with full capacity
		batlevel = 100.0 # Fully charge
		prevbatlevel = 100.0 # Fully charge
		battery = batlevel/100.0 * self.infra.battery.capacity # Wh
		# Battery
		batcharge = 0.0
		batdischarge = 0.0
		# Battery status
		batchargingstatus = False
		batdischargingstatus = True
		batcyclestartlevel = 100.0
		# Battery stats
		batnumdischarges = 0 # How many discharges
		battotaldischarge = 0.0 # Total DoD (%)
		batmaxdischarge = 0.0 # Maximum DoD (%)
		batlifetime = 0.0 # Lifetime (%)
		# State
		stateChargeBattery = False
		stateNetMeter = False
		
		# Get the number of servers available
		numServers = self.infra.it.getNumServers()
		
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
		
		# Use GreenSwitch policy
		solver = ParasolModel()
		solver.options.optCost = 1.0
		# Load
		solver.options.loadDelay = self.workload.deferrable
		solver.options.compression = self.workload.compression
		'''
		if solver.options.loadDelay:
			solver.options.minSize = self.infra.it.getPower(self.workload.minimum, minimum=self.workload.minimum, turnoff=self.turnoff)
		else:
			solver.options.minSize = self.infra.it.getPower(0, minimum=self.workload.minimum, turnoff=self.turnoff)
		'''
		solver.options.minSize = self.infra.it.getPower(0, minimum=self.workload.minimum, turnoff=self.turnoff)
		solver.options.maxSize = self.infra.it.getMaxPower()
		# Power infrastructure costs
		solver.options.netMeter = self.location.netmetering
		# Battery
		solver.options.batEfficiency = self.infra.battery.efficiency
		solver.options.batCap = self.infra.battery.capacity
		solver.options.batDischargeMax = 0.20 # 20% DoD
		# Set initial DoD based on 1 discharge per day
		if self.batteryManagement:
			start = 0.0
			end = 70.0
			while end-start > 0.1:
				mid = start+(end-start)/2.0
				cycles = self.infra.battery.getBatteryCycles(mid)
				lifetimeyear = (100.0/cycles) * 365
				if lifetimeyear > 20.0:
					end = mid
				else:
					start = mid
			solver.options.batDischargeMax = mid/100.0
			if solver.options.batDischargeMax > 0.70:
				solver.options.batDischargeMax = 0.70
		
		# Simulation core
		# Iterate the maximum time (PERIOD) in steps (TIMESTEP)
		for t in range(0, self.period/TIMESTEP):
			# Collect current data
			time = t*TIMESTEP
			brownenergyprice = self.location.getBrownPrice(time)
			temperature = self.location.getTemperature(time)
			#coolingpower = self.infra.cooling.getPower(temperature)
			pue = self.infra.cooling.getPUE(temperature)
			
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
				# Update GreenSwitch policy parameters
				solver.options.prevLoad = prevLoad
				solver.options.previousPeak = peakbrown
				#solver.options.previousPeak = 0.95*peakbrown
				#solver.options.previousPeak = 0.85*peakbrown
				#solver.options.previousPeak = 0.0
				solver.options.peakCost = self.location.brownpowerprice[time]
				# Battery
				solver.options.batIniCap = battery
				# Covering subset workload
				reqNodes = self.workload.getLoad(time)*numServers
				coveringPower = self.infra.it.getPower(reqNodes, minimum=self.workload.minimum, turnoff=self.turnoff) + prevLoad/solver.options.compression
				# All the covering subset running
				if coveringPower > self.infra.it.getPower(self.workload.minimum, minimum=self.workload.minimum, turnoff=self.turnoff):
					coveringPower = self.infra.it.getPower(self.workload.minimum, minimum=self.workload.minimum, turnoff=self.turnoff)
				# All the covering subset idle
				if coveringPower < self.infra.it.getPower(0, minimum=self.workload.minimum, turnoff=self.turnoff):
					coveringPower = self.infra.it.getPower(0, minimum=self.workload.minimum, turnoff=self.turnoff)
				solver.options.minSizeIni = coveringPower
				
				# Fill data with actual values and predictions
				greenAvail = []
				brownPrice = []
				puePredi = []
				worklPredi = []
				for predhour in range(0, SCHEDULING_WINDOW):
					# Current values
					if predhour == 0:
						# Green available
						greenAvail.append(TimeValue(0, greenpower))
						# Brown price
						b = self.location.getBrownPrice(time)
						brownPrice.append(TimeValue(0, b))
						# PUE
						temperature = self.location.getTemperature(time)
						pue = self.infra.cooling.getPUE(temperature)
						puePredi.append(TimeValue(0, pue))
						# Workload
						reqNodes = self.workload.getLoad(time)*numServers
						loadPower = self.infra.it.getPower(reqNodes, minimum=self.workload.minimum, turnoff=self.turnoff)
						#coolingPower = self.infra.cooling.getPower(temperature)						
						w = loadPower #+ coolingPower
						worklPredi.append(TimeValue(0, w))
					# Predicted values
					else:
						predseconds = predhour*60*60
						# Green availability prediction: right now is perfect knowledge
						g = self.location.getSolar(time + predseconds) * self.infra.solar.capacity * self.infra.solar.efficiency
						greenAvail.append(TimeValue(predseconds, g))
						# Brown price prediction
						b = self.location.getBrownPrice(time + predseconds)
						brownPrice.append(TimeValue(predseconds, b))
						# PUE
						temperature = self.location.getTemperature(time + predseconds)
						pue = self.infra.cooling.getPUE(temperature)
						puePredi.append(TimeValue(predseconds, pue))
						# Actual workload
						#reqNodes = self.workload.getLoad(time + predseconds)
						# Workload average based on prediction
						reqNodes = 0.0
						for i in range(0, int(60.0*60.0/TIMESTEP)):
							reqNodes += self.workload.getLoad(time + predseconds + i*TIMESTEP, )*numServers
						reqNodes = float(reqNodes)/(60.0*60.0/TIMESTEP)
						loadPower = self.infra.it.getPower(reqNodes, minimum=self.workload.minimum, turnoff=self.turnoff)
						#coolingPower = self.infra.cooling.getPower(temperature)
						w = loadPower #+ coolingPower
						# TODO Workload prediction
						#w = 1000.0
						worklPredi.append(TimeValue(predseconds, w))
				
				# Generate solution
				obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, pue=puePredi, load=worklPredi, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
			
			# Initialize
			brownpower = 0.0
			netpower = 0.0
			batcharge = 0.0
			batdischarge = 0.0
			# Check if we have a GreenSwitch solution
			if sol == None:
				if self.greenswitch:
					print "No solution at", timeStr(time)
				# Calculate workload: Get the number of nodes required
				reqNodes = self.workload.getLoad(time)*numServers
				workload = self.infra.it.getPower(reqNodes, minimum=self.workload.minimum, turnoff=self.turnoff)
				temperature = self.location.getTemperature(time)
				#coolingPower = self.infra.cooling.getPower(temperature)
				pue = self.infra.cooling.getPUE(temperature)
				# Use brown
				brownpower = workload*pue - greenpower
				if brownpower < 0.0:
					netpower = -1.0*brownpower
					brownpower = 0.0
				# Use batteries if we can
				if brownpower > 0.0:
					if solver.options.batCap > 0.0:
						# Calculate the battery percentage we can discharge
						batdischargeavail = (solver.options.batIniCap/solver.options.batCap) - (1.0-solver.options.batDischargeMax)
						# Transform it into power (% -> Wh -> W)
						batdischargeavail = batdischargeavail * solver.options.batCap * (3600.0/TIMESTEP)
						# Check negative
						if batdischargeavail < 0.0:
							batdischargeavail = 0.0
						# Brown power -> Battery discharge
						batdischarge = batdischargeavail
						if brownpower < batdischarge:
							batdischarge = brownpower
						# Update brown power
						brownpower -= batdischarge
				# Load
				execload = workload
			else:
				# Load
				reqNodes = self.workload.getLoad(time)*numServers
				workload = self.infra.it.getPower(reqNodes, minimum=self.workload.minimum, turnoff=self.turnoff)
				# Cooling
				temperature = self.location.getTemperature(time)
				pue = self.infra.cooling.getPUE(temperature)
				#coolingPower = self.infra.cooling.getPower(temperature)
				# Get solution from solver
				execload = sol['Load[0]']
				#execload = round(sol['Load[0]'], 4)
				#execload = round((sol['LoadBatt[0]'] + sol['LoadGreen[0]'] + sol['LoadBrown[0]'])/pue, 4)
				
				# Calculate brown power and net metering
				brownpower = sol['BattBrown[0]'] + sol['LoadBrown[0]']
				netpower = sol['NetGreen[0]']
				# Battery
				batdischarge = sol['LoadBatt[0]']
				batcharge = sol['BattBrown[0]'] + sol['BattGreen[0]']
				load = sol['LoadBrown[0]'] + sol['LoadGreen[0]'] + sol['LoadBatt[0]']
								
				# Delay load
				if self.workload.deferrable:
					# Delayed load = Current workload - executed load
					difference = (workload - execload)*(TIMESTEP/(60.0*60.0))
					if difference >= 0.0:
						prevLoad += difference
					else:
						# Depending on the workload, we may compress the load when delaying
						prevLoad += difference*self.workload.compression
					if prevLoad < 0:
						prevLoad = 0.0
				
				# Fix solution to match the actual system (Parasol)
				'''
				# Sometimes the solver says to run more than the load we have there
				if execload > workload+prevLoad:
					print 'We are running more than what we actually have'
					print execload, workload, prevLoad # TODO
					surplus = execload - (workload+prevLoad)
					execload -= surplus
					brownpower -= surplus
					if brownpower < 0.0:
						batdischarge += brownpower
						if batdischarge < 0.0:
							if batcharge > 0.0:
								batcharge += -batdischarge
							else:
								netpower += -batdischarge
							batdischarge = 0.0
						brownpower = 0.0
				print execload, workload, prevLoad # TODO
				'''
				# If we charge, we cannot do net metering at the same time
				if batcharge > 0.0 and netpower > 0.0:
					'''
					print 'Error: charging battery and net metering at the same time.'
					print 'Time:', timeStr(time)
					print 'Battery: %.1f%%' % (100.0*battery/solver.options.batCap)
					print 'Battery charge: %.1fW' % batcharge
					print 'Net metering: %.1fW' % netpower
					'''
					batcharge += netpower
					netpower = 0.0
				# If we are using less than what the solver gave us, adjust it
				inPower = greenpower + brownpower + batdischarge
				outPower = execload*pue + netpower + batcharge
				if abs(inPower-outPower) > 1.0:
					print timeStr(time), 'We have a disadjustment'
					print '  IN:  %.1fW' % (greenpower + brownpower + batdischarge)
					print '  OUT: %.1fW' % (execload*pue + netpower + batcharge)
					print '  Green: %.1fW' % greenpower
					print '  Brown: %.1fW' % brownpower
					print '  BDisc: %.1fW' % batdischarge
					print '  ='
					print '  NetMe: %.1fW' % netpower
					print '  BChar: %.1fW' % batcharge
					print '  Load:  %.1fW = %.1fW*%.2f' % (execload*pue, execload, pue)
					if brownpower > 0.0:
						brownpower = execload*pue + netpower + batcharge - greenpower - batdischarge
						if brownpower < 0.0:
							brownpower = 0.0
						print 'Adjust brown: %.1fW' % brownpower 
					if batdischarge > 0.0:
						batdischarge = execload*pue + netpower + batcharge - greenpower - brownpower
						if batdischarge < 0.0:
							batdischarge = 0.0
						print 'Adjust battery discharge: %.1fW' % batdischarge 
					# Surplus green
					if batdischarge == 0.0 and brownpower == 0.0:
						# If we are charging, charge more
						if batcharge > 0.0 or stateChargeBattery:
							batcharge = greenpower - execload*pue
							print 'Adjust battery charge: %.1fW' % batcharge 
						# Otherwise, just net meter
						else:
							netpower = greenpower - execload*pue
							print 'Adjust net metering: %.1fW' % netpower
					
					print 'Solution at', timeStr(time), 'was:'
					print ' Green     ', greenAvail[0]
					print ' Workload  ', worklPredi[0]
					print ' PUE       ', puePredi[0]
					print ' Brown     ', brownPrice[0]
					print ' Load      ', sol['Load[0]']
					print ' Workload  ', sol['Workload[0]']
					print ' BPrice    ', sol['BrownPrice[0]']
					
					print ' LoadBrown ', sol['LoadBrown[0]']
					print ' LoadBatt  ', sol['LoadBatt[0]']
					print ' LoadGreen ', sol['LoadGreen[0]']
					
					print ' PrevLoad  ',  prevLoad
					
					print ' BattBrown ',  sol['BattBrown[0]']
					print ' BattGreen ',  sol['BattGreen[0]']
					print ' CapBattery',  sol['CapBattery[0]']
					
					print ' NetGreen  ',  sol['NetGreen[0]']
					
					print ' PeakBrown ',  sol['PeakBrown']
			
			'''
			if timeStr(time) == '2d15h45m':
				print 'Input at', timeStr(time), 'was:'
				print ' Green    ', greenAvail[0]
				print ' Workload ', worklPredi[0]
				print ' PUE      ', puePredi[0]
				print ' Brown    ', brownPrice[0]
				
				print 'Brown'
				for tv in brownPrice:
					print 'TimeValue(%d, %f), ' % (tv.t, tv.v)
				print 'Green'
				for tv in greenAvail:
					print 'TimeValue(%d, %f), ' % (tv.t, tv.v)
				print 'PUE'
				for tv in puePredi:
					print 'TimeValue(%d, %f), ' % (tv.t, tv.v)
				print 'Workload'
				for tv in worklPredi:
					print 'TimeValue(%d, %f), ' % (tv.t, tv.v)
				print stateChargeBattery
				print stateNetMeter
				
				print 'Options'
				print solver.options.optCost
				print solver.options.loadDelay
				print solver.options.compression
				print solver.options.minSize
				print solver.options.maxSize
				print solver.options.netMeter
				print solver.options.batEfficiency
				print solver.options.batCap
				print solver.options.batDischargeMax
				print solver.options.prevLoad
				print solver.options.previousPeak
				print solver.options.peakCost
				print solver.options.batIniCap
				print solver.options.batDischargeMax
				print solver.options.minSizeIni
			'''
			
			# Charge/discharge battery
			battery += ((self.infra.battery.efficiency * batcharge) - batdischarge) * (TIMESTEP/3600.0)
			if battery > self.infra.battery.capacity:
				battery = self.infra.battery.capacity
			if battery < solver.options.batCap*solver.options.batDischargeProtection:
				print 'Error: The battery was discharged further than the protection limit.'
				battery = solver.options.batCap*solver.options.batDischargeProtection
			
			# Account battery lifetime
			if self.infra.battery.capacity > 0.0:
				# Start charging cycle
				batlevel = 100.0 * battery / self.infra.battery.capacity
				if batcharge > 0.0 and not batchargingstatus:
					batchargingstatus = True
					batdischargingstatus = False
					# Account previous discharge
					batlevel0 = batcyclestartlevel
					batlevel1 = prevbatlevel
					# A discharge of more than 0.1%
					if batlevel0 - batlevel1 > 0.1:
						batnumdischarges += 1
						battotaldischarge += batlevel0 - batlevel1
						if batlevel0 - batlevel1 > batmaxdischarge:
							batmaxdischarge = batlevel0 - batlevel1
						# Account lifetime
						dod = batlevel0 - batlevel1
						cycles = self.infra.battery.getBatteryCycles(dod)
						if cycles > 0.0:
							batlifetime += 100.0/cycles
					#print '%s: %.2f%% -> %.2f%%: %.3f%%' % (timeStr(time), batlevel0, batlevel1, batlifetime)
				# Start discharging cycle
				elif batdischarge > 0.0 and not batdischargingstatus:
					batchargingstatus = False
					batdischargingstatus = True
					batcyclestartlevel = batlevel
				# Store previous value
				prevbatlevel = batlevel
			
				# Change DoD based on battery lifetime projections (every 5 days)
				if self.batteryManagement and time>0 and time%parseTime('5d') == 0:
					# Calculate battery lifetime by this time
					projbatlifetime = 100.0*time/(self.infra.battery.lifetimemax*365*24*60*60)
					if batlifetime < projbatlifetime:
						solver.options.batDischargeMax += 5/100.0 # Increase 5%
					elif batlifetime > projbatlifetime:
						solver.options.batDischargeMax -= 5/100.0 # Decrease 5%
					# Adjust margins
					if solver.options.batDischargeMax > 0.50:
						solver.options.batDischargeMax = 0.50
					if solver.options.batDischargeMax < 0.00:
						solver.options.batDischargeMax = 0.00
			
			# Update state
			if batcharge > 0.0:
				stateChargeBattery = True
			else:
				stateChargeBattery = False
			if netpower > 0.0:
				stateNetMeter = True
			else:
				stateNetMeter = False
			
			# Check peak brown power
			if brownpower > peakbrown:
				peakbrown = brownpower
			
			# Account operational costs
			# Grid electricity
			costbrownenergy += (TIMESTEP/SECONDS_HOUR) * brownpower/1000.0 * brownenergyprice # (seconds -> hours) * kW * $/kWh
			# Net metering
			costbrownenergy -= (TIMESTEP/SECONDS_HOUR) * netpower/1000.0 *   brownenergyprice * self.location.netmetering # (seconds -> hours) * kW * $/kWh * %
			
			'''
			print timeStr(time), (startdate + timedelta(seconds=time)).month
			print 'Brown:', brownpower, brownenergyprice, (TIMESTEP/SECONDS_HOUR) * brownpower/1000.0 * brownenergyprice # (seconds -> hours) * kW * $/kWh
			print 'Net:',   netpower, brownenergyprice, (TIMESTEP/SECONDS_HOUR) * netpower/1000.0 * brownenergyprice * self.location.netmetering # (seconds -> hours) * kW * $/kWh * %
			print 'Peak:',  peakbrown, self.location.brownpowerprice[time+24*60*60], self.location.brownpowerprice[time+24*60*60] * peakbrown/1000.0
			print 'Energy cost:', costbrownenergy
			print 'Power cost: ', costbrownpower
			'''
			
			# Peak power accounting every month
			if (startdate + timedelta(seconds=time)).month != currentmonth:
				costbrownpower += self.location.brownpowerprice[time+24*60*60] * peakbrown/1000.0
				# Reset accounting
				peakbrown = 0.0
				currentmonth = (startdate + timedelta(seconds=time)).month
			
			# Logging
			if fout != None:
				fout.write('%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n' % (time, brownenergyprice, greenpower, netpower, brownpower, batcharge, batdischarge, battery, workload, execload*(pue-1.0), execload, prevLoad))
				fout.flush()
		
		# Account for the last month
		costbrownpower += self.location.brownpowerprice[time+24*60*60] * peakbrown/1000.0
		
		# Infrastructure cost (lifetime)
		costinfrastructure = 0.0
		costinfrastructure += self.infra.solar.capacity * self.infra.solar.price # Solar
		costinfrastructure += self.infra.wind.capacity * self.infra.wind.price # Wind
		costinfrastructure += self.infra.battery.capacity * self.infra.battery.price * TOTAL_YEARS/self.infra.battery.lifetimemax # Battery
		
		# Infrastructure cost (first)
		costinfrastructurefirst = 0.0
		costinfrastructurefirst += self.infra.solar.capacity * self.infra.solar.price # Solar
		costinfrastructurefirst += self.infra.wind.capacity * self.infra.wind.price # Wind
		costinfrastructurefirst += self.infra.battery.capacity * self.infra.battery.price # Battery
		
		# Summary
		print '$%.2f + $%.2f + $%.2f = $%.2f' % (costbrownenergy, costbrownpower, costinfrastructure, costbrownenergy+costbrownpower+costinfrastructure)
		# Log file
		if fout != None:
			fout.write('# Summary:\n')
			fout.write('# Brown energy: $%.2f\n' % (costbrownenergy))
			fout.write('# Peak brown power: $%.2f\n' % (costbrownpower))
			fout.write('# Infrastructure: $%.2f ($%.2f)\n' % (costinfrastructure, costinfrastructurefirst))
			fout.write('# Battery number discharges: %d\n' % (batnumdischarges))
			fout.write('# Battery max discharge: %.2f%%\n' % (batmaxdischarge))
			fout.write('# Battery total discharge: %.2f%%\n' % (battotaldischarge))
			fout.write('# Battery lifetime: %.2f%%\n' % (batlifetime))
			fout.write('# Total: $%.2f\n' % (costbrownenergy+costbrownpower+costinfrastructure))
			fout.close()

if __name__ == "__main__":
	parser = OptionParser(usage="usage: %prog [options] filename", version="%prog 1.0")
	# Data files
	parser.add_option('-w', '--workload', dest='workload',  help='specify the workload file',               default=DATA_PATH+'workload/variable.workload')
	parser.add_option('-l', '--location', dest='location',  help='specify the location file',               default=DATA_PATH+'locations/parasol.location')
	parser.add_option('-i', '--infra',    dest='infra',     help='specify the infrastructure file',         default=DATA_PATH+'parasol.infra')
	# Period
	parser.add_option('-p', '--period',   dest='period',    help='specify the infrastructure file', default='1y')
	# Infrastructure options
	parser.add_option('-s', '--solar',    dest='solar',     type="float", help='specify the infrastructure has solar', default=None)
	parser.add_option('-b', '--battery',  dest='battery',   type="float", help='specify the infrastructure has batteries', default=None)
	parser.add_option('--nosolar',        dest='nosolar',   action="store_true",  help='specify the infrastructure has no solar')
	parser.add_option('--nobattery',      dest='nobattery', action="store_true",  help='specify the infrastructure has no batteries')
	parser.add_option('-c', '--cooling',  dest='cooling',   help='specify the cooling infrastructure file', default=None)
	#parser.add_option('--offset',         dest='offset',    type="string", help='specify offset', default=None)
	parser.add_option('--solardata',      dest='solardata', type="string", help='specify offset', default=None)
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
	if options.netmeter != None:
		simulator.location.netmetering = options.netmeter
	if options.cooling != None:
		simulator.infra.cooling.read(options.cooling)
	# Solar (e.g. validation)
	if options.solardata != None:
		simulator.location.solar = simulator.location.readValues(options.solardata)
		simulator.location.solarcapacity = 3200.0
		simulator.location.solarefficiency = 0.97
		simulator.location.solaroffset = 0.0
	# Policy
	if options.delay == True:
		simulator.workload.deferrable = True
	if options.greenswitch == False:
		simulator.greenswitch = False
	
	simulator.infra.printSummary()
	
	# Run simulation
	simulator.run()
