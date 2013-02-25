#!/usr/bn/python2.7

# bash simulator.sh --solar 3200 --battery 32000 --period 30d --workload data/workload/asplos.workload --net 0.4 -delay

import sys
import os
import os.path
import time
import datetime

from subprocess import Popen, call
from operator import itemgetter

from commons import *
from conf import *
from plotter import *
from parser import *

def generateDayDetails(filenamebase):
	with open(LOG_PATH+filenamebase+'.html', 'w') as fout:
		fout.write('<html>\n')
		fout.write('<head>\n')
		fout.write('<title>Logs</title>\n')
		fout.write('</head>\n')
		fout.write('<body>\n')
		fout.write('<img src="%s"/>\n' % ('img/'+filenamebase+'.png'))
		fout.write('<br/>\n')
		for i in range(0, int(31/3+1)):
			fout.write('<img src="%s"/>\n' % ('img/'+filenamebase+'-'+str(i)+'-day.png'))
			fout.write('<br/>\n')
		fout.write('</body>\n')
		fout.write('</html>\n')

def generateDayFigures(filenamebase):
	# Multi process
	MAX_PROCESSES = 8
	processes = []
	now = time.time()
	# Generate data for plotting
	inputfile =  LOG_PATH+filenamebase+'.log'
	if os.path.isfile(inputfile):
		# Generate input data (make he figure boxed)
		datafile = '/tmp/'+LOG_PATH+filenamebase+'.data'
		if not os.path.isdir(datafile[:datafile.rfind('/')]):
			os.makedirs(datafile[:datafile.rfind('/')])
		genPlotData(inputfile, datafile)
		# Generate a figure for each month
		daystart = int(datetime.date(2012, 1, 1).strftime('%j'))-1
		dayend = int(datetime.date(2012, 2, 1).strftime('%j'))
		
		# Generate figure for each month
		auxoutfile = LOG_PATH+'img/'+filenamebase+'.png'
		p = Popen(['/bin/bash', 'plot.bash', datafile, auxoutfile, '%d' % (daystart*24), '%d' % (dayend*24)])#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
		processes.append(p)
		
		# Generate figure for a couple days in a month
		for i in range(0, int(31/3+1)):
			auxoutfile = LOG_PATH+'img/'+filenamebase+'-'+str(i)+'-day.png'
			p = Popen(['/bin/bash', 'plot.bash', datafile, auxoutfile, '%d' % ((daystart+(i*3))*24), '%d' % ((daystart+(i+1)*3)*24)])#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
			processes.append(p)
	# Wait for everybody to finish
	while len(processes)>0:
		for p in processes:
			if p.poll() != None:
				processes.remove(p)
		if len(processes)>0:
			time.sleep(0.5)

if __name__ == "__main__":
	filenamebase = 'result-1830.0-32000-3200-1y-net0.40-asplos-NEWARK_INTERNATIONAL_ARPT-delay'
	generateDayDetails(filenamebase)
	generateDayFigures(filenamebase)
	print 'Summary at "%s"' % (LOG_PATH+filenamebase+'.html')
	'''
	scenario = Scenario(netmeter=0.4, period=parseTime('1y'), workload='asplos')
	setup = Setup(itsize=1830.0, solar=3200.0, battery=32000.0, location='NEWARK_INTERNATIONAL_ARPT', deferrable=True, turnoff=True)
	cost = Cost()
	saveDetails(scenario, setup, cost)
	generateFigures(scenario, setup)
	'''