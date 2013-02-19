#!/usr/bin/env python2.7

#LOG_SOURCE = 'log-222-swim-source-onoff-netwr-peak-source.log'
#LOG_SOURCE = 'log-133-swim-nobattery-onoff-delay-netwr-peak-source.log'
LOG_SOURCE = 'log-220-swim-source-onoff-netwr-peak-source.log'
#LOG_SOURCE = 'log-230-swim-source-onoff-delay-netwr-peak-source.log'
PERIOD_LENGTH = 15*60

if __name__ == "__main__":
	t0 = None
	period = 0
	values = []
	with open(LOG_SOURCE, 'r') as f:
		for line in f.readlines():
			if not line.startswith('#'):
				lineSplit = line.replace('\n', '').split(';')
				t = int(lineSplit[0])
				# Green Power
				greenpower = float(lineSplit[4])
				
				if t0 == None:
					t0 = t
					periodstart = t - t0

				if (t-t0) - periodstart > PERIOD_LENGTH:
					print period*PERIOD_LENGTH, float(sum(values))/float(len(values))
					#values = [runNodes]
					values = [greenpower]
					periodstart = period*PERIOD_LENGTH
					period += 1
				else:
					#values.append(runNodes)
					values.append(greenpower)