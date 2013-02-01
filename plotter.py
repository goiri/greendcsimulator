#!/usr/bin/env python2.7

import sys

from commons import *

def genPlotData(inputfile, outputfile=None):
	fout = None
	if outputfile!=None:
		fout = open(outputfile, 'w')
	
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
						print line
			else:
				pass

if __name__ == "__main__":
	if len(sys.argv) > 1:
		genPlotData(sys.argv[1])
