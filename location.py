#!/usr/bin/env python2.7

from conf import *
from commons import *

from operator import itemgetter
from datetime import datetime

from timelist import TimeList

"""
Defines a location.
"""
class Location:
	def __init__(self, filename=None):
		self.name = None
		self.lat = None
		self.lng = None
		# Solar
		self.solar = None
		self.solarefficiency = 1.0
		self.solarcapacity = 1.0
		self.solaroffset = 0.0
		# Wind
		self.wind =  None
		self.windefficiency = 1.0
		self.windcapacity = 1.0
		self.windoffset = 0.0
		# Temperature
		self.temperature = None
		self.temperatureoffset = 0.0
		# Brown
		self.brownenergyprice = None
		self.brownpowerprice = None
		self.netmetering = None
		# Read current location
		self.filename = filename
		self.read(filename)
		
	def read(self, filename=None):
		if filename != None:
			with open(filename, 'r') as f:
				for line in f.readlines():
					# Clean line
					line = cleanLine(line)
					# Parse line
					if line != '' and line.find('=') >= 0:
						key, value = line.split('=')
						key = key.strip()
						value = value.strip()
						if key.startswith('latitude') or key.startswith('lat'):
							self.lat = float(value)
						elif key.startswith('longitude') or key.startswith('lng'):
							self.lng = float(value)
						elif key.startswith('solar.'):
							if key.startswith('solar.data'):
								split = value.split(',')
								if len(split) > 0:
									filename = split[0]
									location = None
									if len(split) >= 2:
										location = split[1]
									if len(split) >= 3:
										self.solaroffset = parseTime(split[2])
									# Read data
									self.solar = self.readValues(filename, location)
							elif key.startswith('solar.capacity'):
								self.solarcapacity = float(value)
							elif key.startswith('solar.efficiency'):
								self.solarefficiency = float(value)
							elif key.startswith('solar.offset'):
								self.solaroffset = parseTime(value)
						elif key.startswith('wind.'):
							if key.startswith('wind.data'):
								split = value.split(',')
								if len(split) > 0:
									filename = split[0]
									location = None
									if len(split) >= 2:
										location = split[1]
									if len(split) >= 3:
										self.windoffset = parseTime(split[2])
									# Read data
									self.wind = self.readValues(filename, location)
							elif key.startswith('wind.capacity'):
								self.windcapacity = float(value)
							elif key.startswith('wind.efficiency'):
								self.windefficiency = float(value)
							elif key.startswith('wind.offset'):
								self.windoffset = parseTime(value)
						elif key.startswith('temperature'):
							# Read file with the temperature
							#self.temperature = self.readValues(value)
							split = value.split(',')
							filename = split[0]
							location = None
							if len(split) >= 2:
								location = split[1]
							if len(split) >= 3:
								self.temperatureoffset = parseTime(split[2])
							# Read data
							if location == None:
								self.temperature = self.readValues(filename)
							else:
								self.temperature = self.readLocationData(filename, location)
						elif key.startswith('brown.'):
							if key.startswith('brown.energy'):
								# Read file with the brown energy price
								self.brownenergyprice = self.readValues(value)
								self.brownenergyprice.continous = False
							elif key.startswith('brown.power'):
								# Read file with the temperature
								self.brownpowerprice = self.readValues(value)
								self.brownpowerprice.continous = False
							elif key.startswith('brown.netmetering'):
								# Read file with the temperature
								self.netmetering = float(value)
	
	def readPlacementData(self, filename, locationname):
		#ret = []
		ret = TimeList()
		with open(filename, 'r') as f:
			self.name = locationname
			token  = "NONE"
			ltoken = "NONE"
			for line in f.readlines():
				if line.strip()=="":
					continue
				line = line.lstrip()
				line = line.rstrip()
				line = line.lstrip('\t')
				aux = line.split()

				if aux[0]==';':
					token = "NONE"
					ltoken = "NONE"
				elif aux[0][0]=='[':
					aux2 = aux[0].strip('[')
					ltoken = aux2.strip(',*,*]:')
					ltoken = ltoken.upper()
				elif aux[len(aux)-1]==":=":
					continue
				else:
					tindex = aux[0]
					m = int(tindex[1:3])
					h = int(tindex[3:5])
					if ltoken == locationname:
						i1 = 1
						for i in range(1, 31+1):
							if float(aux[i1]) > 1.0:
								aux[i1] = 1.0
							d = i
							seconds = (m-1)*31*24*60*60 + (d-1)*24*60*60 + (h-1)*60*60
							value = float(aux[i1])
							#ret.append((seconds, value))
							ret[seconds] = value
							i1 += 1
		
		# Sort it and return
		#return sorted(ret, key=itemgetter(0))
		return ret

	def readLocationData(self, filename, location, col=5):
		#ret = []
		ret = TimeList()
		with open(filename, 'r') as f:
			for line in f.readlines():
				# Clean line
				line = cleanLine(line)
				lineSplit = line.split(' ')
				auxlocation = lineSplit[0]
				if location == auxlocation:
					month = int(lineSplit[1])
					day = int(lineSplit[2])
					hour = int(lineSplit[3])
					if hour == 24:
						day += 1
						hour = 0
					#td = datetime(2013, month, day, hour) - datetime(2013, 1, 1, 0)
					#seconds = td.days*24*60*60 + td.seconds
					seconds = (month-1)*31*24*60*60 + (day-1)*24*60*60 + hour*60*60
					value = float(lineSplit[col])
					#ret.append((seconds, v))
					ret[seconds] = value
		return ret

	def readValues(self, filename=None, location=None):
		if location != None:
			return self.readPlacementData(filename, location)
		else:
			#ret = []
			ret = TimeList()
			if filename == '':
				# Default value
				#ret = TimeValue[(0, 0.0)]
				ret[0] = 0.0
			elif filename != None:
				with open(filename, 'r') as f:
					for line in f.readlines():
						# Clean line
						line = cleanLine(line)
						if line != '':
							t, v = line.split(' ')
							t = parseTime(t)
							v = float(v)
							#ret.append((t, v))
							ret[t] = v
			return ret

	def getTemperature(self, time):
		offsettime = time - self.temperatureoffset
		'''
		ret = 0.0
		if offsettime <= self.temperature[0][0]:
			t, temperature = self.temperature[0]
			ret = temperature
		elif offsettime >= self.temperature[-1][0]:
			t, temperature = self.temperature[-1]
			ret = temperature
		else:
			for i in range(0, len(self.temperature)):
				if offsettime >= self.temperature[i][0] and offsettime < self.temperature[i+1][0]:
					ret = interpolate(self.temperature[i], self.temperature[i+1], offsettime)
					break
		return ret
		'''
		return self.temperature[offsettime]
		
	def getSolar(self, time):
		offsettime = time - self.solaroffset
		return (self.solar[offsettime]/self.solarefficiency)/self.solarcapacity
		
	def getWind(self, time):
		offsettime = time - self.windoffset
		return (self.wind[offsettime]/self.solarefficiency)/self.solarcapacity
	
	def getBrownPrice(self, time):
		offsettime = time
		return self.brownenergyprice[offsettime]
		

if __name__ == "__main__":
	location = Location(DATA_PATH+'parasol.location')
	# Check the first day
	for t in range(0, parseTime('1d')/TIMESTEP):
		time = t*TIMESTEP
		print timeStr(time), '\t', ('%.2f' % location.getBrownPrice(time)), '\t', ('%.2f' % (location.getSolar(time)*3200*0.97)), '\t', ('%.2f' % location.getTemperature(time))
	
	SOLAR_DATA = "/net/wonko/home/jlberral/solarpower/test391-full/11-alfa.data"
	WIND_DATA =  "/net/wonko/home/jlberral/solarpower/test391-full/12-beta.data"
	
	for datafile in [SOLAR_DATA, WIND_DATA]:
		print "Data:", datafile
		for locationname in ["BERLIN", "NEWARK_INTERNATIONAL_ARPT", "QUITO", "BARCELONA", "MOUNT_WASHINGTON", "HARARE", "NEW_YORK_CENTRAL_PRK_OBS_BELV"]:
			avg = 0.0
			num = 0.0
			for t, v in location.readPlacementData(datafile, locationname):
				#print timeStr(t), v
				avg += v
				num += 1
			print "%s %.1f%%" % (locationname.replace('_', ' ').title(), 100.0*avg/num)
