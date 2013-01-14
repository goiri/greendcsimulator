#!/usr/bin/env python2.7

from conf import *
from commons import *
from infrastructure import *
from location import *
from workload import *

class Simulator:
	def __init__(self, infrafile, locationfile, workloadfile):
		self.infra = Infrastructure(infrafile)
		self.location = Location(locationfile)
		self.workload = Workload(workloadfile)
	
	def run(self):
		costbrownenergy = 0.0
		costbrownpower = 0.0
		peakbrown = 0.0
		peakbrownaccountingtime = 0
		
		# Datacenter
		# Location traces
		# Workload
		print 'Simulation period: %s' % (timeStr(SIMULATIONTIME))
		for t in range(0, SIMULATIONTIME/TIMESTEP):
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
			
			# Policy
			# Calculate brown power and net metering
			brownpower = workload + coolingpower - greenpower
			netpower = 0.0
			if brownpower < 0.0:
				netpower = -1.0*brownpower
				brownpower = 0.0
			# Peak brown
			if brownpower > peakbrown:
				peakbrown = brownpower
			
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
				peakbrown = 0
			
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
	# Use regular parasol infrastructure
	simulator = Simulator(DATA_PATH+'parasol.infra', DATA_PATH+'parasol.location', DATA_PATH+'fixed.workload')
	simulator.run()
	# Use parasol without green or batteries
	simulator = Simulator(DATA_PATH+'brownparasol.infra', DATA_PATH+'parasol.location', DATA_PATH+'fixed.workload')
	simulator.run()
	