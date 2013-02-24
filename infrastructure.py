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
	def __init__(self, capacity=0, efficiency=0.85, batterylifetimedata='data/leadacid.battery'):
		self.capacity = capacity # Wh
		self.efficiency = efficiency # %
		self.batterylifetime = None
		if batterylifetimedata != None:
			self.batterylifetime = self.readBatteryLifetimeProfile(batterylifetimedata)
	
	"""
	Get the file with the battery lifetime
	"""
	def readBatteryLifetimeProfile(self, batterylifetimedata):
		ret = []
		with open(batterylifetimedata, 'r') as fin:
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
		for auxdod, auxcycles in self.batterylifetime:
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
class Rack:
	def __init__(self):
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

class IT:
	def __init__(self):
		self.racks = {}
		
	def getNumServers(self):
		numServers = 0
		for rackId in sorted(self.racks.keys()):
			for serverId in self.racks[rackId].servers:
				numServers += 1
		return numServers
	
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
			# Add switch power
			rackUtilization = 1.0
			if reqServers < len(self.racks[rackId].servers):
				rackUtilization = math.ceil(reqServers) / float(len(self.racks[rackId].servers))
			powerSwitchIdle = self.racks[rackId].switch.poweridle
			powerSwitchPeak = self.racks[rackId].switch.powerpeak
			power += powerSwitchIdle + rackUtilization*(powerSwitchPeak - powerSwitchIdle)
			
			# Walk the servers in the rack
			for serverId in self.racks[rackId].servers:
				# Add server power
				if reqServers >= 1:
					power += self.racks[rackId].servers[serverId].powerpeak
					reqServers -= 1
					auxminimum -= 1
				elif reqServers > 0:
					power += self.racks[rackId].servers[serverId].poweridle + reqServers*(self.racks[rackId].servers[serverId].powerpeak-self.racks[rackId].servers[serverId].poweridle)
					reqServers -= 1
					auxminimum -= 1
				elif auxminimum > 0:
					power += self.racks[rackId].servers[serverId].poweridle
					auxminimum -= 1
				elif turnoff == False:
					power += self.racks[rackId].servers[serverId].poweridle
				else:
					power += self.racks[rackId].servers[serverId].powers3
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
			return self.pue[temperatures[0]]
		elif temperature > temperatures[-1]:
			return self.pue[temperatures[-1]]
		elif temperature in temperatures:
			return self.pue[temperature]
		else:
			# Walk the list to find the right PUE
			for i in range(0, len(temperatures)):
				if temperature < temperatures[i]:
					p1 = (temperatures[i-1],self.pue[temperatures[i-1]])
					p2 = (temperatures[i],  self.pue[temperatures[i]])
					return interpolate(p1, p2, temperature)
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
						# Cooling
						elif key.startswith('cooling'):
							self.cooling.read(value)
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
		# Initialize everything
		for rackId in self.it.racks:
			self.it.racks[rackId].initServers()
	
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
			print '\t\t', rackId, len(self.it.racks[rackId].servers), 'servers'

# Main program
if __name__ == "__main__":
	infra = Infrastructure('data/parasol.infra')
	
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
	