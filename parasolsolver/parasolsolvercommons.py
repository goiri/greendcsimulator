#!/usr/bin/env python

MAX_SOLAR_POWER = 3200

class SolverOptions:
	def __init__(self):
		#self.output = None
		self.debug = 0
		self.output = None
		self.report = None
		
		self.slotLength = 3600 # Seconds
		
		self.timeLimit = 0 # seconds
		#self.maxTime = 48 # hours
		self.maxTime = 24 # hours
		self.minSize = 0 # Watts (e.g., covering subset)
		self.maxSize = 2500 # Watts
		
		# Load
		self.prevLoad = 0.0
		self.loadDelay = False
		self.compression = 1.0
		
		# Net metering
		self.netMeter = 0.0 # 0% of the grid price
		
		# Peak cost
		self.peakCost = None # $15/kW
		self.previousPeak = 0.0
		
		# Battery
		self.batIniCap = 32*1000 # Wh
		self.batCap =  32*1000 # Wh
		#self.batChargeRate = 4400 # W
		self.batChargeRate = 8000 # W
		self.batDischargeMax = None # % maximum depth of discharge: 40% -> 0.4
		self.batDischargeProtection = 0.15 + 0.06 # % maximum depth of discharge: 15% + 6% = 21%
		self.batEfficiency = 0.9 # % efficiency

		# Optimization
		self.optCost = 0.0
		self.optBat = 0.0
		self.optBatCap = 0.0
		self.optBatCapEnd = 0.0
		self.optPrior = 0.0
		self.optSlowdown = 0.0
		self.optLoad = 0.0
		self.optPerf = 0.0

class Battery:
	def __init__(self, cap, factor=1.0):
		# Energy Wh
		self.stored  = 0.0
		self.cap = cap
		self.factor = factor
	
	def addEnergy(self, add):
		ret = 0.0
		self.stored += self.factor * add
		if self.stored > self.cap:
			ret = (self.stored - self.cap) * self.factor
			self.stored = self.cap
		return ret
		
	def remEnergy(self, rem):
		self.stored -= rem
	
	def getFreeCapacity(self):
		return self.cap-self.stored

# TimeValue
class TimeValue:
	def __init__(self):
		self.t = None
		self.v = None
		
	def __init__(self, t, v):
		self.t = parseTime(t)
		self.v = v
		
	def __lt__(self, other):
		return parseTime(self.t)<parseTime(other.t)
		
	def __str__(self):
		return str(self.t)+" => "+str(self.v)

class Job:
	def __init__(self, id, priority, length, power):
		self.id = id
		self.priority = priority
		self.length = length
		self.power = power
	
	def __str__(self):
		return self.id + " " + str(self.priority) + " " + toTimeString(self.length) + " " + str(self.power)+"W" 
# Extra functions
# Get the available green power
def readGreenAvailFile(filename):
	ret = []
	file = open(filename, 'r')
	for line in file:
		if line != '' and line.find("#")!=0 and line != '\n':
			lineSplit = line.strip().expandtabs(1).split(' ')
			t=lineSplit[0]
			p=float(lineSplit[1])
			# Apply scale factor TODO
			p = (p/2300.0)*MAX_SOLAR_POWER
			
			ret.append(TimeValue(t,p))
	file.close()
	return ret

# Get the cost of the brown energy
def readDataTimeValue(filename):
	ret = []
	file = open(filename, 'r')
	for line in file:
		if line != '' and line != '\n' and line.find("#")!=0:
			lineSplit = line.strip().expandtabs(1).split(' ')
			t=lineSplit[0]
			p=float(lineSplit[1])
			ret.append(TimeValue(t,p))
	file.close()
	return ret
	
def readWorkload(filename):
	ret = []
	file = open(filename, 'r')
	for line in file:
		if line != '' and line != '\n' and line.find("#")!=0:
			lineSplit = line.strip().expandtabs(1).split(' ')
			# Id Priority Length Power
			id = lineSplit[0]
			priority = int(lineSplit[1])
			length = parseTime(lineSplit[2])
			power = parsePower(lineSplit[3])
			ret.append(Job(id, priority, length, power))
	file.close()
	return ret

# Time in/out management
# Aux function to parse a time data
def parseTime(time):
	ret = 0
	if isinstance(time, str):
		aux = time.strip()
		if aux.find('d')>=0:
			index = aux.find('d')
			ret += 24*60*60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('h')>=0:
			index = aux.find('h')
			ret += 60*60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('m')>=0:
			index = aux.find('m')
			ret += 60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('s')>=0:
			index = aux.find('s')
			ret += int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		else:
			ret += int(aux)
	else:
		ret = time
	return ret
	
def parseSize(size):
	ret = 0
	if isinstance(size, str):
		aux = size.strip()
		if aux.find('GB')>=0:
			index = aux.find('GB')
			ret += 1024*1024*1024*int(aux[0:index])
			if index+2<len(aux):
				ret += parseSize(aux[index+2:])
		elif aux.find('MB')>=0:
			index = aux.find('MB')
			ret += 1024*1024*int(aux[0:index])
			if index+2<len(aux):
				ret += parseSize(aux[index+2:])
		elif aux.find('KB')>=0:
			index = aux.find('KB')
			ret += 1024*int(aux[0:index])
			if index+2<len(aux):
				ret += parseSize(aux[index+2:])
		elif aux.find('B')>=0:
			index = aux.find('B')
			ret += int(aux[0:index])
			if index+1<len(aux):
				ret += parseSize(aux[index+1:])
		else:
			ret += int(aux)
	else:
		ret = size
	return ret

def parsePower(power):
	ret = 0
	if isinstance(power, str):
		aux = power.strip()
		if aux.find('kW')>=0:
			index = aux.find('kW')
			ret += 1000*int(aux[0:index])
			if index+2<len(aux):
				ret += parsePower(aux[index+2:])
		elif aux.find('KW')>=0:
			index = aux.find('KW')
			ret += 1000*int(aux[0:index])
			if index+2<len(aux):
				ret += parsePower(aux[index+2:])
		elif aux.find('W')>=0:
			index = aux.find('W')
			ret += int(aux[0:index])
			if index+1<len(aux):
				ret += parseSize(aux[index+1:])
	return ret
	
def toSeconds(td):
	ret = td.seconds
	ret += 24*60*60*td.days
	if td.microseconds > 500*1000:
		ret += 1
	return ret

# From time to string
def toTimeString(time):
	surplus=time%1
	time = int(time)
	ret = ""
	# Day
	aux = time/(24*60*60)
	if aux>=1.0:
		ret += str(int(aux))+"d"
		time = time - aux*(24*60*60)
	# Hour
	aux = time/(60*60)
	if aux>=1.0:
		ret += str(int(aux))+"h"
		time = time - aux*(60*60)
	# Minute
	aux = time/(60)
	if aux>=1.0:
		ret += str(int(aux))+"m"
		time = time - aux*(60)
	# Seconds
	if time>=1.0:
		ret += str(time)+"s"
	
	if ret == "":
		ret = "0"
	# Add surplus
	if surplus>0.0:
		ret+=" +%.2f" % (surplus)
	return ret

def toEnergyString(energy):
	if energy >= 3600*1000:
		return "%.3f kWh" % (energy/(3600.0*1000))
	if energy >= 3600:
		return "%.3f Wh" % (energy/3600.0)
	elif energy >= 1:
		return "%.3f J" % (energy)
	else:
		# Milliseconds
		energy = energy*1000
		if energy >= 1:
			return "%.3f mJ" % (energy)
		else:
			# Microseconds
			return "%.3f uJ" % (energy*1000)

def toSizeString(size):
	if size > 1024*1024*1024:
		return "%.2fGB" % (float(size)/(1024*1024*1024))
		#return str(size/(1024*1024*1024))+"GB"+toSizeString(size%(1024*1024*1024))
	if size > 1024*1024:
		return "%.2fMB" % (float(size)/(1024*1024))
		#return str(size/(1024*1024))+"MB"+toSizeString(size%(1024*1024))
	if size > 1024:
		return str(size/(1024))+"KB"+toSizeString(size%(1024))
	if size == 0:
		return ""
	else:
		return str(size)+"B"
