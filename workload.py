#!/usr/bin/env python2.7

from commons import *
from timelist import TimeList

class Workload:
	def __init__(self, filename=None):
		self.minimum = 0.0
		self.scale = 1.0
		self.repeat = False
		self.deferrable = False
		self.compression = 1.0
		self.filename = filename
		self.load = self.readValues(filename)
	
	def readValues(self, filename=None):
		#ret = []
		ret = TimeList()
		if filename == '':
			# Default value
			#ret = (0, 0.0)
			ret[0] = 0.0
		elif filename != None:
			with open(filename, 'r') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					if line.find('=') > 0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						if key.startswith('workload.deferrable'):
							if value.lower() == 'false':
								self.deferrable = False
							else:
								self.deferrable = True
						elif key.startswith('workload.repeat'):
							if value.lower() == 'false':
								self.repeat = False
							else:
								self.repeat = True
						elif key.startswith('workload.minimum'):
							self.minimum = float(value)
						elif key.startswith('workload.scale'):
							self.scale = float(value)
						elif key.startswith('workload.compression'):
							self.compression = float(value)
					elif line != '':
						t, v = line.split(' ')
						t = parseTime(t)
						v = float(v)
						#ret.append((t, v))
						ret[t] = v
			if self.repeat:
				# Repeat to make it 2 years
				torepeat = list(ret.list)
				last = ret.list[-1][0]
				while last < 2*365*24*60*60:
					for t, load in torepeat:
						#ret.append((last+t, load))
						ret[last+t] = load
					last = ret.list[-1][0]
		return ret
	
	def getLoad(self, time):
		return self.load[time]/self.scale

if __name__ == "__main__":
	load = Workload('fixed.workload')
