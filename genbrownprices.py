#!/usr/bin/env python2.7

from commons import *

from datetime import datetime, timedelta

if __name__ == "__main__":
	startdate = datetime(2013, 1, 1)
	# Energy
	for day in range(0, 365):
		time = day*24*60*60
		currentmonth = (startdate + timedelta(seconds=time)).month
		# Summer (June-September)
		if currentmonth >= 6 and currentmonth <= 9:
			print timeStr(time + 0)        + '\t' + str(0.084026)
			print timeStr(time + 9*60*60)  + '\t' + str(0.132723)
			print timeStr(time + 23*60*60) + '\t' + str(0.084026)
		# Winter (January-May and October-December)
		else:
			print timeStr(time + 0)        + '\t' + str(0.080017)
			print timeStr(time + 9*60*60)  + '\t' + str(0.1175)
			print timeStr(time + 23*60*60) + '\t' + str(0.080017)

	# Peak power
	# Winter
	td = datetime(2013, 1, 1) - startdate
	print timeStr(td.days*24*60*60 + td.seconds) + '\t' + str(5.59)
	# Summer
	td = datetime(2013, 6, 1) - startdate
	print timeStr(td.days*24*60*60 + td.seconds) + '\t' + str(13.61)
	# Winter
	td = datetime(2013, 10, 1) - startdate
	print timeStr(td.days*24*60*60 + td.seconds) + '\t' + str(5.59)
	

