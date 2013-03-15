#!/usr/bin/python2.7

import sys
import os

from operator import itemgetter

from logcommons import *
from reportercommons import *
from parser import *
from plotter import *

# Add general conf
sys.path.append('..')
from conf import *

from infrastructure import Batteries

"""
Save the details of an experiment with a datacenter with a given setup.
"""
def saveDetails(experiment):
	with open(LOG_PATH+experiment.getFilename()+".html", 'w') as fout:
		# Header
		fout.write(getHeader(title='Result for %s' % str(experiment)))
		
		# Content
		fout.write('<h1>Scenario</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Period: %s</li>\n' % timeStr(experiment.scenario.period))
		fout.write('  <li>Net metering: %.1f%%</li>\n' % (experiment.scenario.netmeter*100.0))
		fout.write('</ul>\n')
		
		fout.write('<h1>Setup</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Location: %s</li>\n' % experiment.setup.location.replace('_', ' ').title())
		fout.write('  <li>IT: %s</li>\n' % powerStr(experiment.setup.itsize))
		fout.write('  <li>Peak power: %s</li>\n' % powerStr(experiment.result.peakpower))
		fout.write('  <li>Solar: %s</li>\n' %   (powerStr(experiment.setup.solar)    if experiment.setup.solar>0.0   else '<font color="#999999">&#9747;</font>'))
		fout.write('  <li>Battery: %s</li>\n' % (energyStr(experiment.setup.battery) if experiment.setup.battery>0.0 else '<font color="#999999">&#9747;</font>'))
		fout.write('  <li>Cooling:%s</li>\n' % ('None' if experiment.setup.cooling == None or experiment.setup.cooling.lower() == 'none' else experiment.setup.cooling.title()))
		fout.write('</ul>\n')
		
		fout.write('<h1>Workload</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Workload: %s</li>\n' % experiment.scenario.workload.title())
		fout.write('  <li>Turn on/off: %s</li>\n' % ('<font color="green">&#10003;</font>' if experiment.setup.turnoff    else '<font color="#999999">&#9747;</font>'))
		fout.write('  <li>Deferrable: %s</li>\n' %  ('<font color="green">&#10003;</font>' if experiment.setup.deferrable else '<font color="#999999">&#9747;</font>'))
		fout.write('</ul>\n')
		
		fout.write('<h1>Cost</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Brown energy: %s</li>\n' % costStr(experiment.cost.energy))
		fout.write('  <li>Brown peak power: %s</li>\n' % costStr(experiment.cost.peak))
		fout.write('  <li>OPEX: %s</li>\n' % costStr(experiment.cost.getOPEX()))
		fout.write('  <li>Building: %s</li>\n' % costStr(experiment.cost.building))
		fout.write('  <li>CAPEX: %s</li>\n' % costStr(experiment.cost.getCAPEX()))
		fout.write('  <li>Total: %s</li>\n' % costStr(experiment.cost.getTotal()))
		fout.write('  <li>Total %d years: %s</li>\n' % (TOTAL_YEARS, costStr(experiment.cost.getOPEX(TOTAL_YEARS) + experiment.cost.getCAPEX())))
		fout.write('</ul>\n')
		
		fout.write('<h1>Battery</h1>\n')
		batnumdischarges = 0
		battotaldischarge = 0
		batmaxdischarge = 0
		batlifetime = 0
		if experiment.setup.battery > 0.0:
			batnumdischarges, battotaldischarge, batmaxdischarge, batlifetime = getBatteryStats(LOG_PATH+experiment.getFilename()+'.log')
		fout.write('<ul>\n')
		if batlifetime == None:
			fout.write('  <li>Processing...</li>\n')
		else:
			fout.write('  <li>Number of discharges: %d</li>\n' % batnumdischarges)
			if batnumdischarges>0:
				fout.write('  <li>Average discharge: %.1f%%</li>\n' % (battotaldischarge/batnumdischarges))
				fout.write('  <li>Maximum discharge: %.1f%%</li>\n' % (batmaxdischarge))
				fout.write('  <li>Total discharge: %.1f%%</li>\n' % battotaldischarge)
				fout.write('  <li>Lifetime: %.1f%% (%.1f years)</li>\n' % (batlifetime, 100.0/batlifetime))
		fout.write('</ul>\n')
		
		fout.write('<h1>Log</h1>\n')
		fout.write('<ul>\n')
		fout.write('  <li>Errors: %d</li>\n' % experiment.errors)
		fout.write('  <li><a href="%s.log">Log file</a></li>\n' % experiment.getFilename())
		fout.write('</ul>\n')
		
		# Figure for each month
		fout.write('<h1>Graphics</h1>\n')
		for i in range(1, 12+1):
			fout.write('<h2>%s</h2>\n' % (datetime.date(2012, i, 1).strftime('%B')))
			fout.write('<img src="img/%s/%d.png"/><br/>\n' %     (experiment.getFilename(), i))
			fout.write('<img src="img/%s/%d-day.png"/><br/>\n' % (experiment.getFilename(), i))
		
		# Footer
		fout.write(getFooter())

"""
Write a table header for the experiments
"""
def writeExperimentHeader(fout):
	# First row header
	fout.write('  <tr>\n')
	fout.write('    <th></th>\n')
	fout.write('    <th colspan="5"></th>\n') #fout.write('<th colspan="5">Scenario</th>\n')
	fout.write('    <th colspan="4"></th>\n') #fout.write('<th colspan="4">Setup</th>\n')
	fout.write('    <th colspan="7">Cost</th>\n') # fout.write('    <th colspan="9">Cost</th>\n')
	fout.write('    <th colspan="1">Lifetime</th>\n')
	fout.write('    <th colspan="2">Savings</th>\n')
	fout.write('  </tr>\n')
	# Second row header
	fout.write('  <tr>\n')
	# Setup
	fout.write('    <th></th>\n')
	fout.write('    <th width="60px">Period</th>\n')
	fout.write('    <th width="100px">DC Size</th>\n')
	fout.write('    <th width="70px">Cooling</th>\n')
	fout.write('    <th width="80px">Location</th>\n')
	fout.write('    <th width="80px">Net meter</th>\n')
	fout.write('    <th width="80px">Workload</th>\n')
	fout.write('    <th width="70px">Solar</th>\n')
	fout.write('    <th width="70px">Battery</th>\n')
	fout.write('    <th width="70px">Delay</th>\n')
	fout.write('    <th width="70px">On/off</th>\n')
	# Cost
	#fout.write('    <th width="80px">Energy</th>\n')
	#fout.write('    <th width="80px">Peak</th>\n')
	fout.write('    <th width="150px" colspan="2">OPEX</th>\n')
	fout.write('    <th width="80px">CAPEX</th>\n')
	fout.write('    <th width="150px" colspan="2">Total (1 year)</th>\n')
	fout.write('    <th width="150px" colspan="2">Total (%d years)</th>\n' % TOTAL_YEARS)
	# Lifetime
	fout.write('    <th width="80px">Battery</th>\n')
	# Saving
	fout.write('    <th width="80px">Yearly</th>\n')
	fout.write('    <th width="80px">Ammort</th>\n')
	fout.write('  </tr>\n')

"""
Write a line summarizing an experiment
"""
def writeExperimentLine(fout, experiment, baseexperiment):
	fout.write('<tr>\n')
	# Experiment progress
	experimentDescription = getBarChart([experiment.progress, 100-experiment.progress], 100, width=75, color=['green', '#C0C0C0'])
	if experiment.cost.energy > 0.0 or experiment.cost.peak > 0.0 or experiment.cost.capex > 0.0:
		experimentDescription = 'R'
	if experiment.setup == baseexperiment.setup:
		experimentDescription = '<b>'+experimentDescription+'</b>'
	fout.write('<td align="center"><a href="%s">%s</a></td>\n' % (experiment.getFilename()+'.html', experimentDescription))
	# Setup
	fout.write('<td align="right">%s</td>\n' % (timeStr(experiment.scenario.period)))
	fout.write('<td align="right">%s (%s)</td>\n' % (powerStr(experiment.setup.itsize), powerStr(experiment.result.peakpower)))
	fout.write('<td align="center">%s</td>\n' % ('-' if experiment.setup.cooling == None or experiment.setup.cooling.lower() == 'none' else experiment.setup.cooling.title()))
	fout.write('<td align="right">%s</td>\n' % (experiment.setup.location.replace('_', ' ').title()[0:10]))
	fout.write('<td align="right">%.1f%%</td>\n' % (experiment.scenario.netmeter*100.0))
	fout.write('<td align="right">%s</td>\n' % (experiment.scenario.workload.title()))
	# Solar
	if experiment.setup.solar == 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	else:
		fout.write('<td align="right">%s</td>\n' % powerStr(experiment.setup.solar))
	# Battery
	if experiment.setup.battery == 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	else:
		fout.write('<td align="right">%s</td>\n' % energyStr(experiment.setup.battery))
	# Deferrable
	fout.write('<td align="center">%s</td>\n' % ('<font color="green">&#10003;</font>' if experiment.setup.deferrable else '<font color="#999999">&#9747;</font>'))
	# Turn on/off nodes
	fout.write('<td align="center">%s</td>\n' % ('<font color="green">&#10003;</font>' if experiment.setup.turnoff else '<font color="#999999">&#9747;</font>'))
	# Costs
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(experiment.cost.getOPEX()))
	fout.write('<td>\n')
	fout.write(getBarChart([experiment.cost.energy, experiment.cost.peak], 4*1000*1000, width=100, color=['brown', 'yellow'])) # 2.5 * 1000
	fout.write('</td>\n')
	fout.write('<td align="right">%s</td>\n' % costStr(experiment.cost.getCAPEX()))
	# Total cost
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(experiment.cost.getTotal()))
	fout.write('<td>\n')
	fout.write(getBarChart([experiment.cost.building, experiment.cost.energy, experiment.cost.peak, experiment.cost.capex-experiment.cost.building], 150*1000*1000, width=150, color=['black', 'brown', 'yellow', 'green'])) # 16*1000
	fout.write('</td>\n')
	# Total in N years
	fout.write('<td align="right" width="80px">%s</td>\n' % costStr(experiment.cost.getOPEX()*TOTAL_YEARS + experiment.cost.getCAPEX()))
	fout.write('<td>\n')
	fout.write(getBarChart([experiment.cost.building, experiment.cost.energy*TOTAL_YEARS, experiment.cost.peak*TOTAL_YEARS, experiment.cost.capex-experiment.cost.building], 200*1000*1000, width=150, color=['black', 'brown', 'yellow', 'green'])) # 44*1000
	fout.write('</td>\n')
	
	# Calculate ammortization
	# Saving compare to baseline
	saveopexyear = baseexperiment.cost.getOPEX() - experiment.cost.getOPEX()
	savecapex =  experiment.cost.getCAPEX() - baseexperiment.cost.getCAPEX()
	ammortization = float(savecapex)/float(saveopexyear) if saveopexyear != 0.0 else 0.0
	
	# Lifetime battery
	if experiment.batterylifetime != None:
		if experiment.batterylifetime < 0.1:
			fout.write('<td align="right" width="80px"><font color="#999999">No use</font></td>\n')
		elif saveopexyear < 0:
			fout.write('<td align="right" width="80px"><font color="red">%.1fy</font></td>\n' % (100.0/experiment.batterylifetime))
		elif experiment.batterylifetime >= ammortization:
			fout.write('<td align="right" width="80px"><font color="green">%.1fy</font></td>\n' % (100.0/experiment.batterylifetime))
		else:
			fout.write('<td align="right" width="80px"><font color="#999999">%.1fy</font></td>\n' % (100.0/experiment.batterylifetime))
	else:
		fout.write('<td align="right" width="80px"><font color="#999999">&#9747;</font></td>\n')

	# Costs
	if saveopexyear < 0:
		fout.write('<td align="right"><font color="#FF0000">%s</font></td>\n' % costStr(saveopexyear))
	else:
		fout.write('<td align="right">%s</td>\n' % costStr(saveopexyear))
	# Amortization
	if saveopexyear < 0:
		fout.write('<td align="center"><font color="#999999">&#9747;</font></td>\n')
	elif ammortization == 0:
		fout.write('<td align="center"></td>\n')
	elif ammortization < TOTAL_YEARS:
		fout.write('<td align="right">%.1fy</td>\n' % ammortization)
	else:
		fout.write('<td align="right"><font color="#FF0000">%.1fy</font></td>\n' % ammortization)
	fout.write('<tr/>\n')

# Parsing
if __name__ == "__main__":
	# Collect results by checking all files in the log directory
	print 'Collecting results...'
	results = getResults()
	expRunni = 0
	expTotal = 0
	for scenario in results:
		for experiment in results[scenario]:
			if experiment.progress < 100.0:
				expRunni += 1
			expTotal += 1
	
	# Main Summary
	# ============================================================
	print 'Generating summary...'
	with open(LOG_PATH+'summary.html', 'w') as fout:
		# Header
		fout.write(getHeader(title='Green Datacenter Simulator results'))
		
		fout.write('<h1>Workloads</h1>\n')
		fout.write('<table>\n')
		fout.write('<thead>\n')
		fout.write('<tr>\n')
		fout.write('  <th colspan="3"></th>\n')
		fout.write('  <th colspan="6">Non-deferrable</th>\n')
		fout.write('  <th colspan="6">Deferrable</th>\n')
		fout.write('</tr>\n')
		fout.write('<tr>\n')
		fout.write('  <th></th>\n')
		fout.write('  <th colspan="2">Base cost</th>\n')
		# Non-deferrable
		fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
		fout.write('  <th width="160px" colspan="2">Solar</th>\n')
		fout.write('  <th width="160px" colspan="2">Battery</th>\n')
		# Deferrable
		fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
		fout.write('  <th width="160px" colspan="2">Solar</th>\n')
		fout.write('  <th width="160px" colspan="2">Battery</th>\n')
		fout.write('</tr>\n')
		fout.write('</thead>\n')
		fout.write('<tbody>\n')
		for scenario in sorted(results.keys()):
			# Get experiment baseline
			baseexperiment = sorted(results[scenario])[0]
			for experiment in results[scenario]:
				if experiment.setup.solar==0 and experiment.setup.battery==0 and experiment.setup.deferrable==False and experiment.setup.turnoff==True and experiment.isComplete():
					if experiment.setup.cooling==None or experiment.setup.cooling.lower()=='none':
						baseexperiment = experiment
						if experiment.setup.location=='NEWARK_INTERNATIONAL_ARPT':
							break
			# Get experiment best result
			# Print experiment
			fout.write('<tr>\n')
			fout.write('  <td><a href="summary-%s.html">%s</a></td>\n' % (experiment.scenario.workload, experiment.scenario.workload.title()))
			# Base
			fout.write('  <td><a href="%s.html">%s</td>\n' % (experiment.getFilename(), costStr(baseexperiment.cost.getOPEX()*TOTAL_YEARS + baseexperiment.cost.getCAPEX())))
			fout.write('  <td>' + getBarChart([baseexperiment.cost.energy*TOTAL_YEARS, baseexperiment.cost.peak*TOTAL_YEARS, baseexperiment.cost.capex], 150*1000*1000)+'</td>\n')
			
			# Best non deferrable
			bestexperiment = baseexperiment
			for experiment in results[scenario]:
				if experiment.isComplete() and experiment.setup.deferrable == False:
					if experiment.cost.getTotal(TOTAL_YEARS) < bestexperiment.cost.getTotal(TOTAL_YEARS):
						if experiment.setup.cooling==None or experiment.setup.cooling.lower()=='none' or experiment.setup.cooling!=None:
							bestexperiment = experiment
			fout.write('  <td><a href="%s.html">%s</a></td>\n' % (bestexperiment.getFilename(), costStr(bestexperiment.cost.getTotal(TOTAL_YEARS))))
			fout.write('  <td>' + getBarChart([bestexperiment.cost.energy*TOTAL_YEARS, bestexperiment.cost.peak*TOTAL_YEARS, bestexperiment.cost.capex], 150*1000*1000)+'</td>\n')
			# Solar
			fout.write('  <td align="right">%s</td>\n' % powerStr(bestexperiment.setup.solar))
			fout.write('  <td>' + getBarChart([bestexperiment.setup.solar], 15*1000*1000, color='green')+'</td>\n')
			# Battery
			fout.write('  <td align="right">%s</td>\n' % energyStr(bestexperiment.setup.battery))
			fout.write('  <td>' + getBarChart([bestexperiment.setup.battery], 100*1000*1000, color='yellow')+'</td>\n')
			# Best non-deferrable
			bestexperiment = baseexperiment
			for experiment in results[scenario]:
				if experiment.isComplete() and experiment.setup.deferrable == True:
					if experiment.cost.getTotal(TOTAL_YEARS) < bestexperiment.cost.getTotal(TOTAL_YEARS):
						if experiment.setup.cooling==None or experiment.setup.cooling.lower()=='none' or experiment.setup.cooling!=None:
							bestexperiment = experiment
			fout.write('  <td><a href="%s.html">%s</a></td>\n' % (bestexperiment.getFilename(), costStr(bestexperiment.cost.getTotal(TOTAL_YEARS))))
			fout.write('  <td>' + getBarChart([bestexperiment.cost.energy*TOTAL_YEARS, bestexperiment.cost.peak*TOTAL_YEARS, bestexperiment.cost.capex], 150*1000*1000)+'</td>\n')
			# Solar
			fout.write('  <td align="right">%s</td>\n' % powerStr(bestexperiment.setup.solar))
			fout.write('  <td>' + getBarChart([bestexperiment.setup.solar], 15*1000*1000, color='green')+'</td>\n')
			# Battery
			fout.write('  <td align="right">%s</td>\n' % energyStr(bestexperiment.setup.battery))
			fout.write('  <td>' + getBarChart([bestexperiment.setup.battery], 100*1000*1000, color='yellow')+'</td>\n')
			fout.write('</tr>\n')
		fout.write('</tbody>\n')
		fout.write('</table>\n')
		fout.write('<br/>\n')
		
		# Add 3D figures to the summary page
		i=0
		fout.write('<table>\n')
		fout.write('<tr>\n')
		for scenario in sorted(results.keys()):
			fout.write('<td>\n')
			fout.write('<h2>%s</h2>\n' % scenario.workload.title())
			imgfile =  '3d-'+str(scenario)+'.svg'
			fout.write('<a href="summary-%s.html"><img src="%s" width="400px"></a>\n' % (scenario.workload, imgfile))
			fout.write('</td>\n')
			i+=1
			if i%4 == 0:
				fout.write('<tr>\n')
				fout.write('</tr>\n')
		fout.write('</tr>\n')
		fout.write('</table>\n')
		
		
		fout.write('<h1>Locations</h1>\n')
		locations = []
		for scenario in sorted(results.keys()):
			for experiment in results[scenario]:
				if experiment.setup.location not in locations:
					locations.append(experiment.setup.location)
		for location in locations:
			fout.write('<h2>%s</h2>\n' % location.replace('_', ' ').title())
			fout.write('<table>\n')
			fout.write('<thead>\n')
			fout.write('<tr>\n')
			fout.write('  <th colspan="3"></th>\n')
			fout.write('  <th colspan="6">Non-deferrable</th>\n')
			fout.write('  <th colspan="6">Deferrable</th>\n')
			fout.write('</tr>\n')
			fout.write('<tr>\n')
			fout.write('  <th></th>\n')
			fout.write('  <th colspan="2">Base cost</th>\n')
			# Non-deferrable
			fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
			fout.write('  <th width="160px" colspan="2">Solar</th>\n')
			fout.write('  <th width="160px" colspan="2">Battery</th>\n')
			# Ddeferrable
			fout.write('  <th width="160px" colspan="2">Best cost</th>\n')
			fout.write('  <th width="160px" colspan="2">Solar</th>\n')
			fout.write('  <th width="160px" colspan="2">Battery</th>\n')
			fout.write('</tr>\n')
			fout.write('</thead>\n')
			fout.write('<tbody>\n')
			for scenario in sorted(results.keys()):
				# Get experiment baseline
				baseexperiment = None
				for experiment in results[scenario]:
					if experiment.isComplete():
						if experiment.setup.solar==0 and experiment.setup.battery==0 and experiment.setup.deferrable==False and experiment.setup.turnoff==True and experiment.setup.location==location:
							baseexperiment = experiment
							break
				if baseexperiment != None:
					# Print experiment
					fout.write('<tr>\n')
					fout.write('  <td><a href="summary-%s.html">%s</a></td>\n' % (experiment.scenario.workload, experiment.scenario.workload.title()))
					# Base
					fout.write('  <td><a href="%s.html">%s</a></td>\n' % (experiment.getFilename(), costStr(baseexperiment.cost.getTotal(TOTAL_YEARS))))
					fout.write('  <td>' + getBarChart([baseexperiment.cost.energy*TOTAL_YEARS, baseexperiment.cost.peak*TOTAL_YEARS, baseexperiment.cost.capex], 150*1000*1000)+'</td>\n')
					# Best non deferrable
					bestexperiment = baseexperiment
					for experiment in results[scenario]:
						if experiment.cost.getTotal(TOTAL_YEARS) < bestexperiment.cost.getTotal(TOTAL_YEARS) and experiment.isComplete():
							if not experiment.setup.deferrable and experiment.setup.location==location:
								bestexperiment = experiment
					fout.write('  <td><a href="%s.html">%s</a></td>\n' % (bestexperiment.getFilename(), costStr(bestexperiment.cost.getTotal(TOTAL_YEARS))))
					fout.write('  <td>' + getBarChart([bestexperiment.cost.energy*TOTAL_YEARS, bestexperiment.cost.peak*TOTAL_YEARS, bestexperiment.cost.capex], 150*1000*1000)+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % powerStr(bestexperiment.setup.solar))
					fout.write('  <td>' + getBarChart([bestexperiment.setup.solar], 15*1000*1000, color='green')+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % energyStr(bestexperiment.setup.battery))
					fout.write('  <td>' + getBarChart([bestexperiment.setup.battery], 100*1000*1000, color='yellow')+'</td>\n')
					# Best deferrable
					bestexperiment = baseexperiment
					for experiment in results[scenario]:
						if experiment.cost.getTotal(TOTAL_YEARS) < bestexperiment.cost.getTotal(TOTAL_YEARS) and experiment.isComplete():
							if experiment.setup.deferrable and experiment.setup.location==location:
								bestexperiment = experiment
					fout.write('  <td><a href="%s.html">%s</a></td>\n' % (bestexperiment.getFilename(), costStr(bestexperiment.cost.getTotal(TOTAL_YEARS))))
					fout.write('  <td>' + getBarChart([bestexperiment.cost.energy*TOTAL_YEARS, bestexperiment.cost.peak*TOTAL_YEARS, bestexperiment.cost.capex], 150*1000*1000)+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % powerStr(bestexperiment.setup.solar))
					fout.write('  <td>' + getBarChart([bestexperiment.setup.solar], 15*1000*1000, color='green')+'</td>\n')
					fout.write('  <td align="right">%s</td>\n' % energyStr(bestexperiment.setup.battery))
					fout.write('  <td>' + getBarChart([bestexperiment.setup.battery], 100*1000*1000, color='yellow')+'</td>\n')
					fout.write('</tr>\n')
			fout.write('</tbody>\n')
			fout.write('</table>\n')
		
		
		fout.write('<h1>Cooling</h1>\n')
		coolingtypes = []
		for scenario in sorted(results.keys()):
			for experiment in results[scenario]:
				if experiment.setup.cooling not in coolingtypes:
					coolingtypes.append(experiment.setup.cooling)
		for coolingtype in coolingtypes:
			fout.write('<h2>%s</h2>\n' % (coolingtype.title() if coolingtype != None else 'None'))
		
		
		fout.write('<h1>Datacenter size</h1>\n')
		datacentersizes = []
		for scenario in sorted(results.keys()):
			for experiment in results[scenario]:
				if experiment.setup.itsize not in datacentersizes:
					datacentersizes.append(experiment.setup.itsize)
		for datacentersize in datacentersizes:
			fout.write('<h2>%s</h2>\n' % (powerStr(datacentersize) if datacentersize != None else 'None'))
		
		
		fout.write('<h1>Experiments</h1>\n')
		fout.write('<a href="summary-experiments.html">List of experiments</a><br/>\n')
		fout.write('Experiments: %d/%d<br/>\n' % (expTotal-expRunni, expTotal))
		if expTotal > 0:
			fout.write('Completed: %.1f%%<br/>\n' % (100.0*float(expTotal-expRunni)/expTotal))
		fout.write('<br/>\n')
		
		
		# Footer
		fout.write(getFooter())
	
	# All experiments
	# ============================================================
	print 'Generating all experiments summary...'
	with open(LOG_PATH+'summary-experiments.html', 'w') as fout:
		# Header
		fout.write(getHeader(title='Green Datacenter Simulator results'))
		
		# All experiments
		fout.write('<h1>All experiments</h1>\n')
		# Table header
		fout.write('<table>\n')
		fout.write('<thead>\n')
		writeExperimentHeader(fout)
		fout.write('</thead>\n')
		# Table body
		fout.write('<tbody>\n')
		for scenario in sorted(results.keys()):
			# Get data
			try:
				# Get experiment baseline
				baseexperiment = sorted(results[scenario])[0]
				for experiment in results[scenario]:
					if experiment.setup.solar==0 and experiment.setup.battery==0 and experiment.setup.deferrable==False and experiment.setup.turnoff==True and (experiment.setup.cooling==None or experiment.setup.cooling.lower()=='none'):
						baseexperiment = experiment
						if experiment.setup.location=='NEWARK_INTERNATIONAL_ARPT':
							break
				# Draw result in a row
				for experiment in sorted(results[scenario]):
					writeExperimentLine(fout, experiment, baseexperiment)
			except Exception, e:
				print 'Error generating experiment summary:', e
		# Finish table content
		fout.write('</tbody>\n')
		fout.write('</table>\n')
		# Footer
		fout.write(getFooter())
	
	# Scenario details
	# ============================================================
	print 'Generating scenario details...'
	for scenario in sorted(results.keys()):
		with open(LOG_PATH+'summary-%s.html' % scenario.workload, 'w') as fout:
			# Header
			fout.write(getHeader(title=scenario.workload.title()))
			
			fout.write('<h1>%s</h1>\n' % scenario.workload.title())
			# 3D Figure
			imgfile =  ''
			fout.write('<img width="800px" src="3d-'+str(scenario)+'.svg">\n')
			fout.write('<img width="800px"src="3d-'+str(scenario)+'-base.svg">\n')
			
			# All experiments
			fout.write('<table>\n')
			fout.write('<thead>\n')
			writeExperimentHeader(fout)
			fout.write('</thead>\n')
			fout.write('<tbody>\n')
			# Write data
			try:
				# Get experiment baseline
				baseexperiment = sorted(results[scenario])[0]
				for experiment in results[scenario]:
					if experiment.setup.solar==0 and experiment.setup.battery==0 and experiment.setup.deferrable==False and experiment.setup.turnoff==True and (experiment.setup.cooling==None or experiment.setup.cooling.lower()=='none'):
						baseexperiment = experiment
						if experiment.setup.location=='NEWARK_INTERNATIONAL_ARPT':
							break
				
				# Draw result in a row
				for experiment in sorted(results[scenario]):
					writeExperimentLine(fout, experiment, baseexperiment)
			except Exception, e:
				print 'Error generating scenario details:', e
			# Finish table content
			fout.write('</tbody>\n')
			fout.write('</table>\n')
			# Footer
			fout.write(getFooter())
	
	# 3D Figures
	# ============================================================
	if '--summary' not in sys.argv:
		print 'Generating 3D figures...'
		for scenario in sorted(results.keys()):
			# Data for 3D figure
			figure3d = {}
			figure3dlocations = []
			
			# Data for 3D Figure
			for experiment in sorted(results[scenario]):
				if experiment.setup.turnoff:
					if experiment.setup.location not in figure3dlocations:
						figure3dlocations.append(experiment.setup.location)
					if (experiment.setup.solar, experiment.setup.battery) not in figure3d:
						figure3d[experiment.setup.solar, experiment.setup.battery] = {}
					figure3d[experiment.setup.solar, experiment.setup.battery][experiment.setup.deferrable, experiment.setup.location] = experiment.cost.getTotal(TOTAL_YEARS)
			
			# Generate each one of the 3D figures
			datafile =     LOG_PATH+'3d-'+str(scenario)+'.data'
			imgfile =      LOG_PATH+'3d-'+str(scenario)+'.svg'
			imgfilebase =  LOG_PATH+'3d-'+str(scenario)+'-base.svg'
			#with open('3d.data', 'w') as f3ddata:
			with open(datafile, 'w') as f3ddata:
				f3ddata.write('# '+' '.join(figure3dlocations)+'\n')
				for solar, battery in sorted(figure3d):
					aux = [99999999] * 2 * len(figure3dlocations)
					for location in figure3dlocations:
						if (False, location) in figure3d[solar, battery]:
							aux[figure3dlocations.index(location)*2+0] = figure3d[solar, battery][False, location]
						if (True, location) in figure3d[solar, battery]:
							aux[figure3dlocations.index(location)*2+1] = figure3d[solar, battery][True, location]
					out = '%11.1f\t%11.1f' % (solar, battery)
					for i in range(0, len(figure3dlocations)):
						out += '\t%11.2f\t%11.2f' % (aux[i*2+0], aux[i*2+1])
					f3ddata.write(out+'\n')
			call(['bash', '3dplot.sh', datafile, imgfile])
			call(['bash', '3dplot.sh', datafile, imgfilebase, '1'])
	
	# Experiments details
	# ============================================================
	if '--summary' not in sys.argv:
		# Generate detailed page for experiment
		print 'Generating details...'
		total = 0
		for scenario in sorted(results.keys()):
			for experiment in sorted(results[scenario]):
				saveDetails(experiment)
				total += 1
	
	# Figures
	# ============================================================
	if '--summary' not in sys.argv:
		# Generate figures
		print 'Generating monthly figures...'
		current = 0
		last = datetime.datetime.now()
		for scenario in sorted(results.keys(), reverse=False):
			for experiment in sorted(results[scenario], reverse=False):
				generateFigures(experiment)
				current+=1
				if datetime.datetime.now()-last > datetime.timedelta(seconds=30):
					print '%.1f%%' % (100.0*current/total)
					last = datetime.datetime.now()
