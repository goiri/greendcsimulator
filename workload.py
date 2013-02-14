#!/usr/bin/env python2.7

from commons import *
from timelist import TimeList

class Workload:
	def __init__(self, filename=None):
		self.deferrable = False
		self.minimum = 0.0
		self.repeat = False
		self.scale = 1.0
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
					elif line != '':
						t, v = line.split(' ')
						t = parseTime(t)
						v = float(v)
						#ret.append((t, v))
						ret[t] = v
			if self.repeat:
				# Repeat five years
				torepeat = list(ret.list)
				last = ret.list[-1][0]
				for i in range(0, 5*365):
					for t, load in torepeat:
						#ret.append((last+t, load))
						ret[last+t] = load
					last = ret.list[-1][0]
		return ret
	
	def getLoad(self, time):
		"""
		if time <= self.load[0][0]:
			t, load = self.load[0]
			return load*self.scale
		elif time >= self.load[-1][0]:
			t, load = self.load[-1]
			return load*self.scale
		else:
			for i in range(0, len(self.load)):
				if time >= self.load[i][0] and time < self.load[i+1][0]:
					return interpolate(self.load[i], self.load[i+1], time)*self.scale
		return None
		"""
		return self.load[time]*self.scale

if __name__ == "__main__":
	load = Workload('fixed.workload')
