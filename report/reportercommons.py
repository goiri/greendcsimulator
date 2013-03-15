#!/usr/bin/python2.7

import sys
sys.path.append('..')
from commons import *

def getHeader(title="Green Datacenter Simulator results"):
	# Header
	ret = '<html>\n'
	ret += '<head>\n'
	ret += '  <title>%s</title>\n' % title
	ret += '  <link rel="stylesheet" type="text/css" href="style.css"/>\n'
	ret += '</head>\n'
	ret += '<body>\n'
	return ret


def getFooter():
	# Footer
	ret = '</body>\n'
	ret += '</html>\n'
	return ret

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
Defines the scenario to evaluate the datacenter
"""
class Scenario:
	def __init__(self, netmeter=0, period=None, workload=None):
		self.netmeter = netmeter
		self.period = period
		self.workload = workload
	
	def __str__(self):
		out = ''
		#out += '%.1f%%' % (self.netmeter*100.0)
		out += '%.1f' % (self.netmeter*100.0)
		out += '-%s' % timeStr(self.period)
		out += '-%s' % self.workload.title()
		return out
	
	def __cmp__(self, other):
		if other == None:
			return 1
		else:
			if self.workload == other.workload:
				if self.netmeter == other.netmeter:
					return self.period - other.period
				else:
					return self.netmeter - other.netmeter
			else:
				return cmp(self.workload, other.workload)
	
	def __hash__(self):
		return hash(str(self))

"""
Defines the setup of the datacenter.
"""
class Setup:
	def __init__(self, itsize=0.0, solar=0.0, battery=0.0, location=None, deferrable=False, turnoff=False, greenswitch=True, cooling=None):
		self.location = location
		self.itsize = itsize
		self.solar = solar
		self.battery = battery
		self.deferrable = deferrable
		self.turnoff = turnoff
		self.greenswitch = greenswitch
		self.cooling = cooling
	
	def __cmp__(self, other):
		if other == None:
			return 1
		elif self.itsize != other.itsize:
			return self.itsize - other.itsize
		elif self.cooling != other.cooling:
			return cmp(self.cooling, other.cooling)
		elif self.location != other.location:
			return cmp(self.location, other.location)
		elif self.turnoff != other.turnoff:
			return self.turnoff - other.turnoff
		elif self.deferrable != other.deferrable:
			return self.deferrable - other.deferrable
		elif self.battery != other.battery:
			return self.battery - other.battery
		else:
			return self.solar - other.solar
	
	def __str__(self):
		out = ''
		out += '%s' % self.location.replace('_', ' ').title()[0:20]
		out += ' IT:%s' % powerStr(self.itsize)
		out += ' Sun:%s' % powerStr(self.solar)
		out += ' Bat:%s' % energyStr(self.battery)
		return out

"""
Defines the costs related with operating a datacenter.
"""
class Cost:
	def __init__(self, energy=0.0, peak=0.0, capex=0.0, building=0.0):
		self.capex = capex # Batteries + Solar + Wind + Building
		self.building = building # Datacenter building
		self.energy = energy # Energy
		self.peak = peak # Peak power
	
	def getTotal(self, years=1):
		return self.getCAPEX() + self.getOPEX(years)
	
	def getOPEX(self, years=1):
		return years*(self.energy + self.peak)
	
	def getCAPEX(self):
		return self.capex
	
	def __cmp__(self, other):
		if other == None:
			return 1
		else:
			return self.getTotal()-other.getTotal()
	
	def __str__(self):
		out = ''
		out += '%s' % costStr(self.capex)
		out += ' + %s' % costStr(self.peak)
		out += ' + %s' % costStr(self.energy)
		return out

"""
Result for an experiment
"""
class Result:
	def __init__(self, peakpower = 0.0):
		self.peakpower = peakpower

"""
Defines an experiment
"""
class Experiment:
	# Initialize
	def __init__(self, scenario=None, setup=None, cost=None, result=None, batterylifetime=None, progress=0.0):
		self.scenario = scenario
		self.setup = setup
		self.cost = cost
		self.result = result
		self.batterylifetime = batterylifetime
		self.progress = progress
		self.errors = 0
	
	# Read experiment from filename
	@classmethod
	def fromfilename(self, filename):
		# Empty experiment
		ret = Experiment()
		# Clean prefix
		if filename.find('/') >= 0:
			filename = filename[filename.rfind('/')+1:]
		# Clean suffix
		if filename.endswith('.log') or filename.endswith('.png'):
			filename = filename[:-4]
		if filename.endswith('.html'):
			filename = filename[:-5]
		# Split
		split = filename.split('-')
		if split[0] == 'result':
			split.pop(0)
		itsize = float(split.pop(0))
		battery = int(split.pop(0))
		solar = int(split.pop(0))
		period = parseTime(split.pop(0))
		# Net metering
		netmeter = 0.0
		if split[0].startswith('net'):
			netmeter = float(split.pop(0)[len('net'):])
		# Workload
		workload = split.pop(0)
		# Location
		location = split.pop(0)
		# Read the rest of the values
		delay = False
		alwayson = False
		greenswitch = True
		cooling = None
		while len(split) > 0:
			value = split.pop(0)
			if value == 'on':
				alwayson = True
			elif value == 'delay':
				delay = True
			elif value == 'nogreenswitch':
				greenswitch = False
			elif value.startswith('cool'):
				cooling = value[len('cool'):]
			else:
				print 'Unknown value:', value
		# Update information
		ret.scenario = Scenario(netmeter=netmeter, period=period, workload=workload)
		ret.setup =    Setup(itsize=itsize, solar=solar, battery=battery, location=location, cooling=cooling, deferrable=delay, turnoff=not alwayson, greenswitch=greenswitch)
		
		return ret

	# Check if the experiment has finished
	def isComplete(self):
		return self.progress == 100.0
	
	# Get the filename related to the current setup
	def getFilename(self):
		filename = 'result'
		# IT size
		filename += '-%.1f' % self.setup.itsize
		# Solar
		filename += '-%d' % self.setup.battery
		# Battery
		filename += '-%d' % self.setup.solar
		# Period
		filename += '-%s' % timeStr(self.scenario.period)
		# Net metering
		if self.scenario.netmeter > 0.0:
			filename += '-net%.2f' % self.scenario.netmeter
		# Workload
		filename += '-%s' % self.scenario.workload
		# Location
		filename += '-%s' % self.setup.location
		# Cooling
		if self.setup.cooling != None and self.setup.cooling.lower() != 'none':
			filename += '-cool'+self.setup.cooling
		# Delay
		if self.setup.deferrable == True:
			filename += '-delay'
		# Always on
		if self.setup.turnoff == False:
			filename += '-on'
		# GreenSwitch
		if self.setup.greenswitch == False:
			filename += '-nogreenswitch'
		return filename
	
	# String for the experiment
	def __str__(self):
		return str(self.scenario)+'-'+str(self.setup)+'-'+str(self.cost)
	
	# Compare the experiment with another one
	def __cmp__(self, other):
		if other==None:
			return 1
		elif self.scenario != other.scenario:
			return self.scenario.__cmp__(other.scenario)
		elif self.setup != other.setup:
			return self.setup.__cmp__(other.setup)
		else:
			return self.cost.__cmp__(other.cost)
