#!/usr/bin/env python2.7

import os
import sys
import time
import datetime

from subprocess import Popen, call

from reportercommons import *

# Add general conf
sys.path.append('..')
from conf import *
#from commons import *
#
#from parserconf import *

"""
Generate figures for a log file
"""
def genFigures(filenamebase):
	# Multi process
	MAX_PROCESSES = 8
	processes = []
	now = time.time()
	newData = False
	# Generate data for plotting
	inputfile =  LOG_PATH+filenamebase+'.log'
	if os.path.isfile(inputfile):
		# Generate input data (make he figure boxed)
		datafile = '/tmp/'+LOG_PATH+filenamebase+'.data'
		# Create folder if it does not exist
		if not os.path.isdir(datafile[:datafile.rfind('/')]):
			os.makedirs(datafile[:datafile.rfind('/')])
		# Generate data file if needed (does not exist or newer input file)
		if not os.path.isfile(datafile) or os.path.getmtime(inputfile) > os.path.getmtime(datafile):
			genPlotData(inputfile, datafile)
			# Update modify time for datafile
			os.utime(datafile, (os.path.getatime(datafile), os.path.getmtime(inputfile)))
			newData = True
		# Generate a figure for each monthFb
		for i in range(1, 12+1):
			daystart = int(datetime.date(2012, i, 1).strftime('%j'))-1
			if i < 12:
				dayend = int(datetime.date(2012, i+1, 1).strftime('%j'))
			else:
				dayend = int(datetime.date(2012, i, 31).strftime('%j'))
			
			# Generate figure for each month
			imgfile = LOG_PATH+'img/'+filenamebase+'/'+str(i)+'.png'
			if not os.path.isdir(imgfile[:imgfile.rfind('/')]):
				os.makedirs(imgfile[:imgfile.rfind('/')])
			if not os.path.isfile(imgfile) or newData:
				experiment = Experiment.fromfilename(filenamebase)
				size = experiment.setup.itsize * 1.8 * 1.1 # IT x PUE +10%
				if experiment.setup.solar*1.1 > size:
					size = experiment.setup.solar*1.1
				p = Popen(['/bin/bash', 'plot.sh', datafile, imgfile, '--start', '%d' % (daystart*24), '--end', '%d' % (dayend*24), '--size', str(size)])
				#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
				processes.append(p)
			
			# Generate figure for a couple days in a month
			imgfile = LOG_PATH+'img/'+filenamebase+'/'+str(i)+'-day.png'
			if not os.path.isdir(imgfile[:imgfile.rfind('/')]):
				os.makedirs(imgfile[:imgfile.rfind('/')])
			if not os.path.isfile(imgfile) or newData:
				experiment = Experiment.fromfilename(filenamebase)
				size = experiment.setup.itsize * 1.8 * 1.1 # IT x PUE +10%
				if experiment.setup.solar*1.1 > size:
					size = experiment.setup.solar*1.1
				p = Popen(['/bin/bash', 'plot.sh', datafile, imgfile, '--start', '%d' % ((daystart+15)*24), '--end', '%d' % ((daystart+18)*24), '--size', str(size)])
				#, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
				processes.append(p)
			
			# Wait until we only have 8 figures to go
			while len(processes)>MAX_PROCESSES:
				for p in processes:
					if p.poll() != None:
						processes.remove(p)
				if len(processes)>MAX_PROCESSES:
					time.sleep(0.5)
	# Wait for everybody to finish
	while len(processes)>0:
		for p in processes:
			if p.poll() != None:
				processes.remove(p)
		if len(processes)>0:
			time.sleep(0.5)

"""
Generate figures for a filename base
"""
def generateFigures(experiment):
	genFigures(experiment.getFilename())

"""
Generate the data to plot
"""
def genPlotData(inputfile, outputfile=None):
	fout = None
	if outputfile!=None:
		fout = open(outputfile, 'w')
	# Read input file
	with open(inputfile, 'r') as fin:
		content = True
		lineSplitPrev = None
		for line in fin.readlines():
			if content:
				if line.startswith('# Summary:'):
					content = False
				elif not line.startswith('# Time'):
					try:
						lineSplit = line.replace('\n', '').split('\t')
						time = parseTime(lineSplit[0])
						brownprice =    float(lineSplit[1])
						greenpower =    float(lineSplit[2])
						netmeterpower = float(lineSplit[3])
						brownprower =   float(lineSplit[4])
						batcharge =     float(lineSplit[5])
						batdischarge =  float(lineSplit[6])
						batlevel =      float(lineSplit[7])
						workload =      float(lineSplit[8])
						coolingpower =  float(lineSplit[9])
						execload =      float(lineSplit[10])
						prevload =      float(lineSplit[11])
						
						# Previous line
						if lineSplitPrev != None:
							lineSplitPrev[0] = lineSplit[0]
							if fout == None:
								print '\t'.join(lineSplitPrev)
							else:
								fout.write( '\t'.join(lineSplitPrev) + '\n')
						# Current line
						if fout == None:
							print '\t'.join(lineSplit)
						else:
							fout.write( '\t'.join(lineSplit) + '\n')
						lineSplitPrev = lineSplit
					except Exception, e:
						pass
						#print 'Error parsing line:', line
			else:
				pass

# Testing
if __name__ == "__main__":
	inputfile = None
	outputfile = None
	if len(sys.argv) > 1:
		inputfile = sys.argv[1]
	if len(sys.argv) > 2:
		outputfile = sys.argv[2]
	genPlotData(inputfile, outputfile)
