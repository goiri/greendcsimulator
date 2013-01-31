#!/usr/bin/python2.7

import os

from operator import itemgetter

from commons import *
from conf import *

TOTAL_YEARS = 10

def cmpsetup(x, y):
	if x.turnoff == y.turnoff:
		if x.deferrable == y.deferrable:
			if x.battery == y.battery:
				return x.solar - y.solar
			else:
				return x.battery - y.battery
		else:
			return x.deferrable - y.deferrable
	else:
		return x.turnoff - y.turnoff

class Scenario:
	def __init__(self, netmeter=0, period=None, workload=None):
		self.netmeter = netmeter
		self.period = period
		self.workload = workload
	
	def __str__(self):
		return str(self.netmeter) + '-' + str(self.period)  + '-' + str(self.workload)
	
	def __hash__(self):
		return hash(str(self))
	
	def __eq__(self, other):
		return (self.netmeter, self.period, self.workload) == (other.netmeter, other.period, other.workload)

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

class Setup:
	def __init__(self, solar=0.0, battery=0.0, deferrable=False, turnoff=False):
		self.solar = solar
		self.battery = battery
		self.deferrable = deferrable
		self.turnoff = turnoff

class Result:
	def __init__(self, cost, setup):
		self.setup = setup
		self.cost = cost

def getBarChart(vals, maxval, width=100, height=15, color='blue'):
	out = ''
	out += '<table border="0" cellspacing="0" cellpadding="0">'
	out += '<tr height="%d">' % height
	colors = [color, 'yellow', 'red', 'green', 'orange', 'black', 'blue']
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

# Immutable
#   Net metering
#   Period
#   Workload

# Parsing
if __name__ == "__main__":
	with open(LOG_PATH+'summary.html', 'w') as fout:
		fout.write('<html>\n')
		fout.write('<head>\n')
		fout.write('<title>Green Datacenter Simulator results</title>\n')
		fout.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
		fout.write('</head>\n')
		
		# Check files
		results = {}
		for filename in sorted(os.listdir(LOG_PATH)):
			#print LOG_PATH+filename
			if filename.endswith('.log'):
				# Get data from filename
				split = filename[:-4].split('-')
				split.pop(0)
				battery = int(split.pop(0))
				solar = int(split.pop(0))
				period = parseTime(split.pop(0))
				# Net metering
				netmeter = 0.0
				if split[0].startswith('net'):
					netmeter = float(split.pop(0)[4:])
				# Workload
				workload = split.pop(0)
				# Read the rest of the values
				delay = False
				alwayson = False
				while len(split) > 0:
					value = split.pop(0)
					if value == 'on':
						alwayson = True
					elif value == 'delay':
						delay = True
					else:
						print 'Unknown value:', value
				# Open file and read results
				costenergy = 0.0
				costpeak = 0.0
				costcapex = 0.0
				with open(LOG_PATH+filename) as f:
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
				# Store results
				scenario = Scenario(netmeter=netmeter, period=period, workload=workload)
				cost = Cost(energy=costenergy, peak=costpeak, capex=costcapex)
				setup = Setup(solar=solar, battery=battery, deferrable=delay, turnoff=not alwayson)
				#results[scenario] = Result(setup, cost)
				if scenario not in results:
					results[scenario] = []
				results[scenario].append((setup, cost))
		
		# Print results
		fout.write('<body>\n')
		fout.write('<table>\n')
		fout.write('<tr>\n')
		fout.write('<th colspan="7">Setup</th>\n')
		fout.write('<th colspan="7">Cost</th>\n')
		fout.write('</tr>\n')
		fout.write('<tr>\n')
		# Setup
		fout.write('<th width="90px">Solar</th>\n')
		fout.write('<th width="90px">Battery</th>\n')
		fout.write('<th width="90px">Net metering</th>\n')
		fout.write('<th width="90px">Period</th>\n')
		fout.write('<th width="90px">Workload</th>\n')
		fout.write('<th width="90px">Deferrable</th>\n')
		fout.write('<th width="90px">Turn on/off</th>\n')
		# Cost
		fout.write('<th width="90px">Energy</th>\n')
		fout.write('<th width="90px">Peak</th>\n')
		fout.write('<th width="150px" colspan="2">OPEX</th>\n')
		fout.write('<th width="90px">CAPEX</th>\n')
		fout.write('<th width="150px" colspan="2">Total (1 year)</th>\n')
		fout.write('<th width="150px" colspan="2">Total (%d years)</th>\n' % TOTAL_YEARS)
		fout.write('<th width="90px">Savings</th>\n')
		fout.write('<th width="90px">Ammortization</th>\n')
		fout.write('</tr>\n')
		for scenario in results:
			try:
				# Get baseline
				basesetup, basecost = sorted(results[scenario], key=itemgetter(0), cmp=cmpsetup)[0]
				# Show result
				for setup, cost in sorted(results[scenario], key=itemgetter(0), cmp=cmpsetup):
					fout.write('<tr>\n')
					# Setup
					if setup.solar == 0:
						fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
					else:
						fout.write('<td align="right">%s</td>\n' % powerStr(setup.solar))
					if setup.battery == 0:
						fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
					else:
						fout.write('<td align="right">%s</td>\n' % energyStr(setup.battery))
					fout.write('<td align="right">%.1f%%</td>\n' % (scenario.netmeter*100.0))
					fout.write('<td align="right">%s</td>\n' % timeStr(scenario.period))
					fout.write('<td align="right">%s</td>\n' % scenario.workload.title())
					if setup.deferrable:
						fout.write('<td align="center"><font color="green">&#10003;</font></td>\n')
					else:
						fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
					if setup.turnoff:
						fout.write('<td align="center"><font color="green">&#10003;</font></td>\n')
					else:
						fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
						
					# Costs
					fout.write('<td align="right">%s</td>\n' % costStr(cost.energy))
					fout.write('<td align="right">%s</td>\n' % costStr(cost.peak))
					fout.write('<td align="right">%s</td>\n' % costStr(cost.getOPEX()))
					fout.write('<td>\n')
					fout.write(getBarChart([cost.energy, cost.peak], 2.5*1000, width=100))
					fout.write('</td>\n')
					fout.write('<td align="right">%s</td>\n' % costStr(cost.getCAPEX()))
					# Total cost
					fout.write('<td align="right">%s</td>\n' % costStr(cost.getTotal()))
					fout.write('<td>\n')
					fout.write(getBarChart([cost.energy, cost.peak, cost.capex], 26*1000, width=150))
					fout.write('</td>\n')
					# Total in N years
					fout.write('<td align="right">%s</td>\n' % costStr(cost.getOPEX()*TOTAL_YEARS + cost.getCAPEX()))
					fout.write('<td>\n')
					fout.write(getBarChart([cost.energy*TOTAL_YEARS, cost.peak*TOTAL_YEARS, cost.capex], 42*1000, width=150))
					fout.write('</td>\n')
					
					# Calculate ammortization
					# Saving compare to baseline
					saveopexyear = basecost.getOPEX() - cost.getOPEX()
					savecapex =  cost.getCAPEX() - basecost.getCAPEX()
					ammortization = 0.0
					if saveopexyear != 0.0:
						ammortization = float(savecapex)/float(saveopexyear)
					fout.write('<td align="right">%s</td>\n' % costStr(saveopexyear))
					if saveopexyear < 0:
						fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
					elif saveopexyear == 0:
						fout.write('<td align="center"></td>\n')
					else:
						fout.write('<td align="right">%.1f years</td>\n' % ammortization)
					fout.write('<tr/>\n')
			except Exception, e:
				print 'Error:', e
		fout.write('</table>\n')
		fout.write('</body>\n')
		fout.write('</html>\n')
		