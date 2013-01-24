#!/usr/bin/env python2.7

from conf import *
from commons import *

from operator import itemgetter

class Location:
	def __init__(self, filename=None):
		self.lat = None
		self.lng = None
		self.solar = None
		self.wind =  None
		self.temperature = None
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
								self.solar = self.readValues(value)
							elif key.startswith('solar.capacity'):
								capacity = float(value)
								for i in range(0, len(self.solar)):
									t, v = self.solar[i]
									self.solar[i] = (t, v/capacity)
							elif key.startswith('solar.efficiency'):
								efficiency = float(value)
								for i in range(0, len(self.solar)):
									t, v = self.solar[i]
									self.solar[i] = (t, v/efficiency)
							elif key.startswith('solar.offset'):
								offset = parseTime(value)
								for i in range(0, len(self.solar)):
									t, v = self.solar[i]
									self.solar[i] = (t+offset, v)
						elif key.startswith('wind.'):
							# Read file with the wind
							self.wind = self.readValues(value)
						elif key.startswith('temperature'):
							# Read file with the temperature
							self.temperature = self.readValues(value)
						elif key.startswith('brown.'):
							if key.startswith('brown.energy'):
								# Read file with the temperature
								self.brownenergyprice = self.readValues(value)
							elif key.startswith('brown.power'):
								# Read file with the temperature
								self.brownpowerprice = float(value)
							elif key.startswith('brown.netmetering'):
								# Read file with the temperature
								self.netmetering = float(value)

	def readPlacementData(self, filename, locationname):
		ret = []
		with open(filename, 'r') as f:
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
							ret.append((seconds, value))
							i1 += 1
		# Sort it and return
		return sorted(ret, key=itemgetter(0))

	def readValues(self, filename=None):
		if filename.find(",")>=0:
			auxfilename, auxlocation = filename.split(",")
			return self.readPlacementData(auxfilename, auxlocation)
		else:
			ret = []
			if filename == '':
				# Default value
				ret = [(0, 0.0)]
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

	def getTemperature(self, time):
		if time <= self.temperature[0][0]:
			t, temperature = self.temperature[0]
			return temperature
		elif time >= self.temperature[-1][0]:
			t, temperature = self.temperature[-1]
			return temperature
		else:
			for i in range(0, len(self.temperature)):
				if time >= self.temperature[i][0] and time < self.temperature[i+1][0]:
					return interpolate(self.temperature[i], self.temperature[i+1], time)
		return None
		
	def getSolar(self, time):
		if len(self.solar) == 0:
			return 0.0
		else:
			if time <= self.solar[0][0]:
				t, solar = self.solar[0]
				return solar
			elif time >= self.solar[-1][0]:
				t, solar = self.solar[-1]
				return solar
			else:
				for i in range(0, len(self.solar)):
					if time >= self.solar[i][0] and time < self.solar[i+1][0]:
						return interpolate(self.solar[i], self.solar[i+1], time)
		
	def getWind(self, time):
		if len(self.wind) == 0:
			return 0.0
		else:
			if time <= self.wind[0][0]:
				t, wind = self.wind[0]
				return wind
			elif time >= self.wind[-1][0]:
				t, wind = self.wind[-1]
				return wind
			else:
				for i in range(0, len(self.wind)):
					if time >= self.wind[i][0] and time < self.wind[i+1][0]:
						return interpolate(self.wind[i], self.wind[i+1], time)
	
	def getBrownPrice(self, time):
		for i in range(0, len(self.brownenergyprice)):
			t, v = self.brownenergyprice[i]
			if time >= self.brownenergyprice[i][0] and time < self.brownenergyprice[i+1][0]:
				return self.brownenergyprice[i][1]
		return None
		

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