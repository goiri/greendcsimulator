#!/usr/bin/python2.7

from commons import *
from conf import *

def getResults():
	results = {}
	for filename in sorted(os.listdir(LOG_PATH)):
		if filename.endswith('.log'):
			# Get experiment information from filename
			experiment = Experiment.fromfilename(filename)
			
			# Open file to check progress or final results
			costenergy = 0.0
			costpeak = 0.0
			costcapex = 0.0
			costbuilding = 0.0
			# Peak
			peakpower = 0.0
			# Battery
			batnumdischarges = None
			batmaxdischarge = None
			battotaldischarge = None
			batlifetime = None
			# Solver errors
			errors = 0
			# Timing
			lastTime = 0
			try:
				with open(LOG_PATH+filename, 'r') as f:
					# Go to the end of the file
					f.seek(-2*1024, os.SEEK_END)
					f.readline()
					# Start checking from the end
					for line in f.readlines():
						if line.startswith('#'):
							line = line.replace('\n', '')
							if line.startswith('# Brown energy:'):
								costenergy = parseCost(line.split(' ')[3])
							elif line.startswith('# Peak brown power:'):
								costpeak = parseCost(line.split(' ')[4])
							elif line.startswith('# Peak brown power life:'):
								costbuilding = parseCost(line.split(' ')[5])
								peakpower = parsePower(line.split(' ')[6][1:-1])
							elif line.startswith('# Infrastructure:'):
								costcapex = parseCost(line.split(' ')[2])
							elif line.startswith('# Total:'):
								#print 'Total:', line.split(' ')[2]
								lastTime = experiment.scenario.period
							elif line.startswith('# Battery number discharges:'):
								batnumdischarges = int(line.split(' ')[4])
							elif line.startswith('# Battery max discharge:'):
								batmaxdischarge = float(line.split(' ')[4][:-1])
							elif line.startswith('# Battery total discharge:'):
								battotaldischarge = float(line.split(' ')[4][:-1])
							elif line.startswith('# Battery lifetime:'):
								batlifetime = float(line.split(' ')[3][:-1])
							elif line.startswith('# Solver error at'):
								errors += 1
								#print filename, line[2:]
							elif line.startswith('# Solver errors'):
								errors = int(line.split(' ')[3])
								if errors > 0:
									print filename, ' solver errors', errors
						else:
							try:
								expTime = int(line.split('\t')[0])
								if expTime > lastTime:
									lastTime = expTime
							except Exception, e:
								print 'Error reading log file', line, e
			except Exception, e:
				print 'Cannot read file', LOG_PATH+filename, e
				
			experiment.errors = errors
			experiment.progress = 100.0*lastTime/experiment.scenario.period
			
			experiment.result = Result(peakpower=peakpower)
			experiment.cost = Cost(energy=costenergy, peak=costpeak, capex=costcapex, building=costbuilding)
			experiment.batterylifetime = batlifetime
			
			# Create data structures
			#scenario =   Scenario(netmeter=netmeter, period=period, workload=workload)
			#setup =      Setup(itsize=itsize, solar=solar, battery=battery, location=location, cooling=cooling, deferrable=delay, turnoff=not alwayson, greenswitch=greenswitch)
			#cost =       Cost(energy=costenergy, peak=costpeak, capex=costcapex)
			#experiment = Experiment(scenario=scenario, setup=setup, progress=progress, cost=cost, batterylifetime=batlifetime)
			
			# Store results
			if experiment.scenario not in results:
				results[experiment.scenario] = []
			results[experiment.scenario].append(experiment)
	return results
