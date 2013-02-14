#!/usr/bin/env python2.7

from commons import interpolate

"""
Class to implement a series of values in time
"""
class TimeList:
	def __init__(self, continous=True):
		self.list = [] # [(time, value)
		self.continous = continous

	def __str__(self):
		#for t, v in 
		#return ','.join(self.list)
		return str(self.list)
	
	def __len__(self):
		return len(self.list)
	
	def __contains__(self, time):
		ret = False
		pos = self.indexOf(time)
		if self.list[pos][0] == time:
			ret = True
		return ret
	
	def __getitem__(self, time):
		if time <= self.list[0][0]:
			return self.list[0][1]
		if time >= self.list[-1][0]:
			return self.list[-1][1]
		# Search for the spot
		start = 0
		end = len(self.list)
		while end-start > 1:
			mid = start + (end-start)/2
			if time < self.list[mid][0]:
				end = mid
			else:
				start=mid
		if self.continous:
			p1 = self.list[start]
			p2 = self.list[end]
			return interpolate(p1, p2, time)
		else:
			return self.list[start][1]
	
	def __setitem__(self, time, value):
		if len(self.list)==0 or time > self.list[-1][0]:
			self.list.append((time, value))
		else:
			pos = self.indexOf(time)
			self.list.insert(pos+1, (time, value))
	
	def __delitem__(self, time):
		pos = self.indexOf(time)
		if self.list[pos][0] == time:
			self.list.pop(pos)
		
	def indexOf(self, time):
		if time <= self.list[0][0]:
			return 0
		if time >= self.list[-1][0]:
			return len(self.list)-1
		# Search for the spot
		start = 0
		end = len(self.list)
		while end-start > 1:
			mid = start + (end-start)/2
			if time < self.list[mid][0]:
				end = mid
			else:
				start=mid
		return start

if __name__ == "__main__":
	list = TimeList(continous=False)
	
	for t in range(2, 10):
		list[t*5] = t*2

	print list
	
	print 5, '=', list[5], list.indexOf(5)
	print 17, '=', list[17], list.indexOf(17)
	print 25, '=', list[25], list.indexOf(25)
	print 27, '=', list[27], list.indexOf(27)
	print 27.5, '=', list[27.5], list.indexOf(27.5)
	print 48, '=', list[48], list.indexOf(48)

	list[0] = 10
	list[27.5] = 10
	list[50] = 10
	print list
	print (5 in list)
	print (10 in list)
	del list[10]
	del list[40]
	print list
	print (10 in list)
	print list[7.5]
	