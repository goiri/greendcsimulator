#!/usr/bin/env python2.7

from conf import *
from commons import *

# Green sources
class SolarPanels:
	def __init__(self, capacity=0, efficiency=0.97, price=0.0):
		self.capacity = capacity # W
		self.efficiency = efficiency # %
		self.price = price # %

class WindTurbines:
	def __init__(self, capacity=0, efficiency=0.97, price=0.0):
		self.capacity = capacity # W
		self.efficiency = efficiency # %
		self.price = price # %

# Energy storage
class Batteries:
	def __init__(self, capacity=0, efficiency=0.85, lifetimemax=4.0, lifetimedata='data/leadacid.battery'):
		self.capacity = capacity # Wh
		self.efficiency = efficiency # %
		self.lifetimemax = lifetimemax
		self.lifetime = None
		if lifetimedata != None:
			self.lifetime = self.readBatteryLifetimeProfile(lifetimedata)
	
	"""
	Get the file with the battery lifetime
	"""
	def readBatteryLifetimeProfile(self, lifetimedata):
		ret = []
		with open(lifetimedata, 'r') as fin:
			for line in fin.readlines():
				# Clean line
				line = cleanLine(line)
				if line != '':
					dod, cycles = line.split(' ')
					ret.append((float(dod), float(cycles)))
		return ret

	"""
	Get the cycles that can be made with a given Depth of Discharge
	"""
	def getBatteryCycles(self, dod):
		prevauxdod = None
		prevcycles = None
		for auxdod, auxcycles in self.lifetime:
			if dod == auxdod:
				return auxcycles
			elif dod < auxdod:
				# First value
				if dod < 0.1:
					return 0.0
				elif prevauxdod == None:
					# If it is the first value, we asume it's linear from 0
					return auxcycles * float(auxdod)/float(dod)
				else:
					p1 = (prevauxdod, prevcycles)
					p2 = (auxdod, auxcycles)
					return interpolate(p1, p2, dod)
			prevauxdod = auxdod
			prevcycles = auxcycles
		return 0.0
	
	"""
	Get what percentage of the battery has been used
	@return Percentage (%). The maximum would be 100.
	"""
	def getPercentageBattery(self, dod):
		cycles = self.getBatteryCycles(dod)
		return 100.0/cycles

# IT equipment
class Server:
	def __init__(self, powers3=1, poweridle=75, powerpeak=150):
		self.powers3 = powers3
		self.poweridle = poweridle
		self.powerpeak = powerpeak

	# Get a server configuration from its type
	def read(self, servertype):
		if servertype != None:
			with open(DATA_PATH+servertype.lower()+'.server') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					# Parse line
					if line != '' and line.find('=') >= 0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						if key.startswith('power.'):
							if key.startswith('power.s3'):
								self.powers3 = float(value)
							elif key.startswith('power.idle'):
								self.poweridle = float(value)
							elif key.startswith('power.peak'):
								self.powerpeak = float(value)
class Switch:
	def __init__(self, poweridle=25, powerpeak=50):
		self.poweridle = poweridle
		self.powerpeak = powerpeak
	
	# Get a switch configuration from its type
	def read(self, switchtype):
		if switchtype != None:
			with open(DATA_PATH+switchtype.lower()+'.switch') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					# Parse line
					if line != '' and line.find('=') >= 0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						if key.startswith('power.'):
							if key.startswith('power.s3'):
								self.powers3 = float(value)
							elif key.startswith('power.idle'):
								self.poweridle = float(value)
							elif key.startswith('power.peak'):
								self.powerpeak = float(value)

# Model an IT rack with one switch and multiple servers
class Rack:
	def __init__(self):
		self.number = 1
		self.servernum = 0
		self.servertype = None
		self.servers = {}
		self.switch = None
	
	# Initialize the servers
	def initServers(self):
		for i in range(0, self.servernum):
			if self.servertype != None:
				server = Server()
				server.read(self.servertype)
				self.servers[i] = server
	
	# Get the number of servers of a rack
	def getNumServers(self):
		return len(self.servers)
	
	# Get the power consumption of a rack depending on the number of servers used
	def getPower(self, numServers, minimum=0, turnoff=True):
		power = 0.0
		auxminimum = minimum
		reqServers = numServers
		
		# Add switch power
		rackUtilization = 1.0
		if reqServers < len(self.servers):
			rackUtilization = math.ceil(reqServers) / float(len(self.servers))
		powerSwitchIdle = self.switch.poweridle
		powerSwitchPeak = self.switch.powerpeak
		power += powerSwitchIdle + rackUtilization*(powerSwitchPeak - powerSwitchIdle)
		
		# Walk the servers in the rack
		for serverId in self.servers:
			# Add server power
			if reqServers >= 1:
				power += self.servers[serverId].powerpeak
				reqServers -= 1
				auxminimum -= 1
			elif reqServers > 0:
				power += self.servers[serverId].poweridle + reqServers*(self.servers[serverId].powerpeak-self.servers[serverId].poweridle)
				reqServers -= 1
				auxminimum -= 1
			elif auxminimum > 0:
				power += self.servers[serverId].poweridle
				auxminimum -= 1
			elif turnoff == False:
				power += self.servers[serverId].poweridle
			else:
				power += self.servers[serverId].powers3
		return power

"""
IT equipment: it includes multiple racks
"""
class IT:
	def __init__(self):
		self.racks = {}
	
	# Get the number of servers in the system
	def getNumServers(self):
		numServers = 0
		for rackId in sorted(self.racks.keys()):
			rackServers = 0
			for serverId in self.racks[rackId].servers:
				rackServers += 1
			numServers += rackServers * self.racks[rackId].number
		return numServers
	
	# Get the power if everything is running full blast
	def getMaxPower(self):
		return self.getPower(self.getNumServers())
	
	"""
	Calculate the load based on the number of servers
	@param numServers Number of servers running.
	@param minimum Minimum number of servers.
	@param turnoff If the server can be turned off.
	"""
	def getPower(self, numServers, minimum=0, turnoff=True):
		power = 0.0
		auxminimum = minimum
		reqServers = numServers
		
		# Account for full 
		maxServers = self.getNumServers()
		if reqServers > maxServers:
			maxPower = self.getMaxPower()
			while reqServers > maxServers:
				reqServers -= maxServers
				power += maxPower
		
		# Walk the racks
		for rackId in sorted(self.racks.keys()):
			# Calculate the number of required racks
			numRackServers = self.racks[rackId].getNumServers()
			reqRacks = float(reqServers)/float(numRackServers)
			if reqRacks > self.racks[rackId].number:
				reqRacks = self.racks[rackId].number
			# Racks at full power
			maxRackPower = self.racks[rackId].getPower(numRackServers, turnoff=turnoff)
			power += math.floor(reqRacks) * maxRackPower
			reqServers -= math.floor(reqRacks) * numRackServers
			auxminimum -= math.floor(reqRacks) * numRackServers
			# If we haven't use all the racks
			if math.floor(reqRacks) < self.racks[rackId].number:
				# The rack in between
				if reqServers > 0:
					power += self.racks[rackId].getPower(reqServers, minimum=auxminimum, turnoff=turnoff)
					reqServers -= reqServers
					auxminimum -= numRackServers
					if auxminimum < 0:
						auxminimum = 0
				# Racks with minimum power
				racksToGo = self.racks[rackId].number - math.ceil(reqRacks)
				if auxminimum > 0:
					power += math.floor(auxminimum/numRackServers) * self.racks[rackId].getPower(0, minimum=numRackServers, turnoff=turnoff)
					auxminimum -= math.floor(auxminimum/numRackServers) * numRackServers
					if auxminimum < numRackServers:
						power += self.racks[rackId].getPower(0, minimum=auxminimum, turnoff=turnoff)
						auxminimum -= auxminimum
					racksToGo -= math.ceil(auxminimum/numRackServers)
				# Racks completely off
				if racksToGo > 0:
					minRackPower = self.racks[rackId].getPower(0, minimum=0, turnoff=turnoff)
					power += racksToGo * minRackPower
			if reqServers < 0:
				reqServers = 0
			if auxminimum < 0:
				auxminimum = 0
		return power
	
	"""
	Calculate how many nodes are up based on power
	"""
	def getNodes(self, power, minimum=0, turnoff=True):
		# Use dicotomic search
		top = self.getNumServers()
		bottom = 0
		while top-bottom > 0.05:
			middle = bottom + (top-bottom)/2.0
			auxpower = self.getPower(middle, minimum=minimum, turnoff=turnoff)
			if power >= auxpower:
				bottom = middle
			else:
				top = middle
		return round(middle, 1)

"""
Model for datacenter cooling system.
"""
class Cooling:
	def __init__(self):
		# Temperature -> Power
		self.power = {}
		self.pue = {}
		self.coolingtype = None
	
	# Get a server configuration from its type
	def read(self, coolingtype):
		if coolingtype != None:
			with open(DATA_PATH+coolingtype.lower()+'.cooling') as f:
				# Clean
				self.power = {}
				self.pue = {}
				self.coolingtype = coolingtype
				# Read lines
				for line in f.readlines():
					line = cleanLine(line)
					# Parse line
					if line != '' and line.find('=') >= 0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						if key.startswith('power.'):
							temperature = float(key[len('power.'):])
							self.power[temperature] = float(value)
						elif key.startswith('pue.'):
							temperature = float(key[len('pue.'):])
							self.pue[temperature] = float(value)
	
	# Get the cooling power for an external temperature
	def getPower(self, temperature):
		temperatures = list(sorted(self.power.keys()))
		if len(temperatures) == 0:
			return 0.0
		elif temperature < temperatures[0]:
			return self.power[temperatures[0]]
		elif temperature > temperatures[-1]:
			return self.power[temperatures[-1]]
		elif temperature in temperatures:
			return self.power[temperature]
		else:
			# Walk the list to find the right power
			for i in range(0, len(temperatures)):
				if temperature < temperatures[i]:
					p1 = (temperatures[i-1],self.power[temperatures[i-1]])
					p2 = (temperatures[i],  self.power[temperatures[i]])
					return interpolate(p1, p2, temperature)
		return 0.0
	
	# Get the datacenter PUE for an external temperature
	def getPUE(self, temperature):
		temperatures = list(sorted(self.pue.keys()))
		if len(temperatures) == 0:
			return 1.0
		elif temperature < temperatures[0]:
			return round(self.pue[temperatures[0]], 3)
		elif temperature > temperatures[-1]:
			return round(self.pue[temperatures[-1]], 3)
		elif temperature in temperatures:
			return round(self.pue[temperature], 3)
		else:
			# Walk the list to find the right PUE
			for i in range(0, len(temperatures)):
				if temperature < temperatures[i]:
					p1 = (temperatures[i-1],self.pue[temperatures[i-1]])
					p2 = (temperatures[i],  self.pue[temperatures[i]])
					return round(interpolate(p1, p2, temperature), 3)
		return 1.0

"""
Define the infrastructure of a green datacenter:
	Solar panels
	Wind turbines
	Batteries
	IT equipment
"""
class Infrastructure:
	# Initialize from file
	def __init__(self, filename=None):
		# Default values
		self.price = None # $/W
		self.solar = SolarPanels()
		self.wind = WindTurbines()
		self.battery = Batteries()
		self.it = IT()
		self.cooling = Cooling()
		# Read data from file
		if filename != None:
			with open(filename, 'r') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					
					# Parse line
					if line!='' and line.find('=')>=0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						# Solar panels
						if key.startswith('solar'):
							if key.startswith('solar.capacity'):
								self.solar.capacity = float(value)
							elif key.startswith('solar.efficiency'):
								self.solar.efficiency = float(value)
							elif key.startswith('solar.price'):
								self.solar.price = float(value)
						# Wind turbines
						elif key.startswith('wind'):
							if key.startswith('wind.capacity'):
								self.wind.capacity = float(value)
							elif key.startswith('wind.efficiency'):
								self.wind.efficiency = float(value)
							elif key.startswith('wind.price'):
								self.wind.price = float(value)
						# Batteries
						elif key.startswith('battery'):
							if key.startswith('battery.capacity'):
								self.battery.capacity = float(value)
							elif key.startswith('battery.efficiency'):
								self.battery.efficiency = float(value)
							elif key.startswith('battery.price'):
								self.battery.price = float(value)
							elif key.startswith('battery.lifetime'):
								self.battery.lifetimemax = float(value)
							elif key.startswith('battery.type'):
								self.battery.readBatteryLifetimeProfile(DATA_PATH+value+'.battery')
						# Cooling
						elif key.startswith('cooling'):
							self.cooling.read(value)
						# Cooling
						elif key.startswith('price'):
							if float(value) > 0.0:
								self.price = float(value)
						# IT
						elif key.startswith('it'):
							# Parse racks
							auxkey = key[key.find('.')+1:]
							rackId = auxkey[:auxkey.find('.')]
							if rackId not in self.it.racks:
								self.it.racks[rackId] = Rack()
							# Servers
							if key.startswith('it.'+rackId+'.server'):
								if key.startswith('it.'+rackId+'.server.num'):
									self.it.racks[rackId].servernum = int(value)
								elif key.startswith('it.'+rackId+'.server.type'):
									self.it.racks[rackId].servertype = value
								else:
									print 'Server', rackId, key, value
							# Switch
							elif key.startswith('it.'+rackId+'.switch'):
								if key.startswith('it.'+rackId+'.switch.type'):
									self.it.racks[rackId].switch = Switch()
									self.it.racks[rackId].switch.read(value)
							# Number
							elif key.startswith('it.'+rackId+'.number'):
								# Copy the rack N times
								self.it.racks[rackId].number = int(value)
								
		# Initialize everything
		for rackId in self.it.racks.keys():
			self.it.racks[rackId].initServers()
			
		# Expand servers
		'''
		for rackId in self.it.racks.keys():
			numRacks = self.it.racks[rackId].number
			if numRacks > 1:
				self.it.racks[rackId].number = 1
				rack = self.it.racks[rackId]
				for i in range(0, numRacks):
					self.it.racks['%s-%05d' % (rackId, i)] = rack
			del self.it.racks[rackId]
		'''
	
	# Intrastructure summary
	def printSummary(self):
		print 'Datacenter infrastructure:'
		if self.solar.capacity > 0:
			print '\tSolar panels: ', powerStr(self.solar.capacity)
		if self.wind.capacity > 0:
			print '\tWind turbines:', powerStr(self.wind.capacity)
		if self.battery.capacity > 0:
			print '\tBatteries:    ', energyStr(self.battery.capacity)
		print '\tIT:'
		for rackId in sorted(self.it.racks):
			print '\t\t', self.it.racks[rackId].number, rackId, 'x', len(self.it.racks[rackId].servers), '=', self.it.racks[rackId].number*len(self.it.racks[rackId].servers), 'servers'

# Main program
if __name__ == "__main__":
	infra = Infrastructure('data/parasol.infra')
	infra.printSummary()
	
	# Testing cooling
	for outtemp in range(15, 38):
		print outtemp, infra.cooling.getPower(outtemp)
	
	print 'Nothing: %.1fW' % infra.it.getPower(0)
	print 'Covering subset: %.1fW' % infra.it.getPower(0, minimum=8)
	print 'Covering subset running 4: %.1fW' % infra.it.getPower(4, minimum=8)
	print 'Covering subset running 8: %.1fW' % infra.it.getPower(8, minimum=8)
	print 'Peak: %.1fW' % infra.it.getPower(64, minimum=8)
	print 'Peak: %.1fW' % infra.it.getMaxPower()
	
	print 'Get nodes number of nodes based on power:'
	power = infra.it.getPower(4, minimum=0)
	print 4, power, infra.it.getNodes(power, minimum=0)
	power = infra.it.getPower(20, minimum=0)
	print 20, power, infra.it.getNodes(power, minimum=0)
	print 64, infra.it.getMaxPower(), infra.it.getNodes(infra.it.getMaxPower(), minimum=0)
	
	# Test large infrastructure
	from datetime import datetime
	
	t0 = datetime.now()
	
	for datafile in ['data/large.infra']:
		infra = Infrastructure(datafile)
		infra.printSummary()
		
		print 'Servers:     ', infra.it.getNumServers()
		print '0 nodes (0): ', infra.it.getPower(0, minimum=0), 'W'
		print '0 nodes (10):', infra.it.getPower(0, minimum=10), 'W'
		print '20 nodes:    ', powerStr(infra.it.getPower(20, minimum=10))
		print '1000 nodes:  ', powerStr(infra.it.getPower(1000, minimum=10))
		print '20000 nodes: ', powerStr(infra.it.getPower(20000, minimum=10))
		print '200000 nodes:', powerStr(infra.it.getPower(200000, minimum=10))
		print '203600 nodes:', powerStr(infra.it.getPower(203600, minimum=10))
		print 'Peak: %s' % powerStr(infra.it.getMaxPower())
		print 'Get nodes number of nodes based on power:'
		for n in [4, 20, 40, 46, 50, 100, 1000]:
			power = infra.it.getPower(n, minimum=0)
			print '%4d => %7.1fW => %4d' % (n, power, infra.it.getNodes(power, minimum=0))
		print infra.it.getNumServers(), infra.it.getMaxPower(), infra.it.getNodes(infra.it.getMaxPower(), minimum=0)
	print datetime.now()-t0
	