#!/usr/bin/env python2.7

import math

SECONDS_HOUR = 60.0*60.0 # seconds in an hour

def cleanLine(line):
	ret = line
	
	# Remove comments
	if ret.find('#')>=0:
		ret = ret[:ret.find('#')]
	# Clean line
	ret = ret.replace('\n', '')
	ret = ret.replace('\t', ' ')
	while ret.find('  ')>=0:
		ret = ret.replace('  ', ' ')
	ret = ret.strip()
	
	return ret

def interpolate(p1, p2, x):
	x1, y1 = p1
	x2, y2 = p2
	m = float(y2-y1)/float(x2-x1)
	b = y1 - m*x1
	return m*x + b

def parseTime(line):
	ret = 0
	if line.startswith('-'):
		ret = -1*parseTime(line[1:])
	elif line.find('y') >= 0:
		val = int(line[:line.find('y')]) * 365 * 24 * 60 * 60
		ret += val + parseTime(line[line.find('y')+len('y'):])
	elif line.find('w') >= 0:
		val = int(line[:line.find('w')]) * 7 * 24 * 60 * 60
		ret += val + parseTime(line[line.find('w')+len('w'):])
	elif line.find('d') >= 0:
		val = int(line[:line.find('d')]) * 24 * 60 * 60
		ret += val + parseTime(line[line.find('d')+len('d'):])
	elif line.find('h') >= 0:
		val = int(line[:line.find('h')]) * 60 * 60
		ret += val + parseTime(line[line.find('h')+len('h'):])
	elif line.find('m') >= 0:
		val = int(line[:line.find('m')]) * 60
		ret += val + parseTime(line[line.find('m')+len('m'):])
	elif line.find('s') >= 0:
		val = int(line[:line.find('s')])
		ret += val + parseTime(line[line.find('s')+len('s'):])
	elif line == ' ' or line == '':
		pass
	else:
		val = int(line)
		ret += val
	return ret

def parsePower(line):
	ret = 0.0
	if line.find('kW')>0:
		ret = float(line.replace('kW', ''))*1000.0
	elif line.find('MW')>0:
		ret = float(line.replace('MW', ''))*1000.0*1000.0
	elif line.find('GW')>0:
		ret = float(line.replace('GW', ''))*1000.0*1000.0*1000.0
	elif line.find('W')>0:
		ret = float(line.replace('W', ''))
	elif line == '-':
		ret = 0.0
	else:
		ret = float(line)
	return ret
	
def parseEnergy(line):
	ret = 0.0
	if line.find('kWh')>0:
		ret = float(line.replace('kWh', ''))*1000.0
	elif line.find('MWh')>0:
		ret = float(line.replace('MWh', ''))*1000.0*1000.0
	elif line.find('GWh')>0:
		ret = float(line.replace('GWh', ''))*1000.0*1000.0*1000.0
	elif line.find('Wh')>0:
		ret = float(line.replace('Wh', ''))
	elif line == '-':
		ret = 0.0
	else:
		ret = float(line)
	return ret

def parseCost(line):
	ret = 0.0
	line = line.strip()
	if line.startswith('$'):
		ret = float(line[1:])
	return ret

def timeStr(time):
	ret = ''
	# Years
	if time >= 365*24*60*60:
		ret += str(time/(365*24*60*60))+'y'
		time -= (time/(365*24*60*60)) * 365*24*60*60
	# Days
	if time >= 24*60*60:
		ret += str(time/(24*60*60))+'d'
		time -= (time/(24*60*60)) * 24*60*60
	# Hours
	if time >= 60*60:
		ret += str(time/(60*60))+'h'
		time -= (time/(60*60)) * 60*60
	# Minutes
	if time >= 60:
		ret += str(time/(60))+'m'
		time -= (time/(60)) * 60
	# Seconds
	if time > 0:
		ret += str(time)+'s'
	
	return ret

def powerStr(power):
	if math.isinf(power):
		return '&infin;W'
	elif power >= 1000*1000*1000*1000:
		return '%.1fTW' % (power/(1000.0*1000.0*1000.0*1000.0))
	elif power >= 1000*1000*1000:
		return '%.1fGW' % (power/(1000.0*1000.0*1000.0))
	elif power >= 1000*1000:
		return '%.1fMW' % (power/(1000.0*1000.0))
	elif power >= 1000:
		return '%.1fkW' % (power/(1000.0))
	else:
		return '%.1fW' % (power)

def costStr(cost):
	if math.isinf(cost):
		return '$&infin;'
	elif cost > 10*1000*1000*1000 or cost < -10*1000*1000*1000:
		return '$%.1fG' % (cost/(1000.0*1000.0*1000.0))
	elif cost > 9999*1000 or cost < -9999*1000:
		return '$%.1fM' % (cost/(1000.0*1000.0))
	elif cost > 9999 or cost < -9999:
		return '$%.1fk' % (cost/(1000.0))
	elif cost == 0:
		return '-'
	else:
		return '$%.1f' % (cost)

def energyStr(energy):
	if math.isinf(energy):
		return '&infin;Wh'
	elif energy >= 1000*1000*1000*1000:
		return '%.1fTWh' % (energy/(1000.0*1000.0*1000.0*1000.0))
	elif energy >= 1000*1000*1000:
		return '%.1fGWh' % (energy/(1000.0*1000.0*1000.0))
	elif energy >= 1000*1000:
		return '%.1fMWh' % (energy/(1000.0*1000.0))
	elif energy >= 1000:
		return '%.1fkWh' % (energy/(1000.0))
	else:
		return '%.1fWh' % (energy)
