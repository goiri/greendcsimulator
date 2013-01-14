#!/usr/bin/env python2.7

from commons import *

class Workload:
	def __init__(self, filename=None):
		self.load = self.readValues(filename)
		
	def readValues(self, filename=None):
		ret = []
		if filename == '':
			# Default value
			ret = (0, 0.0)
		elif filename != None:
			with open(filename, 'r') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					if line != '':
						t, v = line.split(' ')
						t = parseTime(t)
						v = float(v)
						ret.append((t, v))
		return ret
	
	def getLoad(self, time):
		if time <= self.load[0][0]:
			t, load = self.load[0]
			return load
		elif time >= self.load[-1][0]:
			t, load = self.load[-1]
			return load
		else:
			for i in range(0, len(self.load)):
				if time >= self.load[i][0] and time < self.load[i+1][0]:
					return interpolate(self.load[i], self.load[i+1], time)
		return None

if __name__ == "__main__":
	load = Workload('fixed.workload')
