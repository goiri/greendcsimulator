#!/usr/bin/env python2.7

LOG_NODE =   'log-222-swim-source-onoff-netwr-peak-node.log'
LOG_POWER =  'log-222-swim-source-onoff-netwr-peak-power.log'
LOG_SOURCE = 'log-222-swim-source-onoff-netwr-peak-source.log'

if __name__ == "__main__":
	t0 = None
	switch1 = []
	switch2 = []
	servers = {}
	with open(LOG_POWER, 'r') as f:
		for line in f.readlines():
			if not line.startswith('#'):
				lineSplit = line.replace('\n', '').split(';')
				t = int(lineSplit[0])
				if t0 == None:
					t0 = t
				# Power
				switch1.append(float(lineSplit[1]))
				switch2.append(float(lineSplit[2]))
				for i in range(0, 63):
					if i not in servers:
						servers[i] = []
					try:
						servers[i].append(float(lineSplit[3+i]))
					except Exception, e:
						print t-t0, e
	for i in range(0, 63):
		servers[i] = sorted(servers[i])
	
	for j in range(0, len(servers[0])):
		for i in range(0, 63):
			print servers[i][j],
		print