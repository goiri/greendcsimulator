#!/usr/bin/env python2.7

from commons import *
from infrastructure import *

class Datacenter:
	def __init__(self):
		self.infrastructure = None
		self.location = None
		self.workload = None


if __name__ == "__main__":
	dc = Datacenter()
	dc.infra = Instratructure('parasol.infra')
	dc.location = Location('parasol.location')
	dc.workload = Workload('fixed.workload')