#!/usr/bin/python2.7

from tarfile import TarFile

from datetime import datetime

FILENAME='projectcounts-2008.tar'
MAX_REQUESTS = 33056088*0.4

if __name__ == "__main__":
	tar = TarFile(FILENAME)
	inidate = datetime(year=2008, month=1, day=1)
	maxrequests = 0
	for filename in tar.getnames():
		pre, date, time = filename.split('-')
		year = int(date[0:4])
		month = int(date[4:6])
		day = int(date[6:8])
		hour = int(time[0:2])
		minute = int(time[2:4])
		second = int(time[4:6])
		date = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
		td = date-inidate
		seconds = td.days*24*60*60 + td.seconds
		
		f = tar.extractfile(filename)
		for line in f.readlines():
			if line.startswith('en -'):
				line = line.replace('\n', '').replace('\r', '')
				lineSplit = line.split(' ')
				requests = int(lineSplit[2])
				if requests > MAX_REQUESTS:
					requests = MAX_REQUESTS
				print '%d %.2f' % (seconds, float(requests)/MAX_REQUESTS)
				if requests > maxrequests:
					maxrequests = requests