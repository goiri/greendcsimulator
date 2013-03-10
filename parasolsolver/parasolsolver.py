#!/usr/bin/env python

import os
import sys
import math
import socket

from parasolsolvercommons import *

from datetime import datetime

# Load Gurobi libraries
try:
	# Gurobi
	# export LD_LIBRARY_PATH="/home/goiri/hadoop-parasol/solver/gurobi500/linux64/lib"
	GUROBI_PATH = "/home/goiri/hadoop-parasol/solver/gurobi500/linux64"
	GUROBI_PATH = "/home/jlberral/gurobi501/linux64"
	GUROBI_PATH = "/home/goiri/gurobi510/linux64"
	os.environ["LD_LIBRARY_PATH"] = GUROBI_PATH+"/lib/"
	#os.environ["GRB_LICENSE_FILE"] = GUROBI_PATH+"/gurobi.lic"
	#os.environ["GRB_LICENSE_FILE"] = GUROBI_PATH+"/gurobi-"+socket.gethostname()+".lic"
	os.environ["GRB_LICENSE_FILE"] = GUROBI_PATH+"/gurobi.lic."+socket.gethostname()
	sys.path.append(GUROBI_PATH+"/lib")
	sys.path.append(GUROBI_PATH+"/lib/python2.7")
	from gurobipy import *
except ImportError, e:
	print 'export LD_LIBRARY_PATH='+GUROBI_PATH+'/lib'

TOTAL_YEARS = 12

"""
Model of Parasol using MILP.
"""
class ParasolModel:
	def __init__(self):
		self.options = SolverOptions()
		self.obj = None
		self.sol = None
		self.load = None
		self.greenAvail = None
		self.brownPrice = None
		self.pue = None
		# Store for auxiliary variables
		self.auxvars = []
		self.auxbins = []
		self.largeNumber = 99999
		
		self.saveModel = False
	
	# Solve problem using Gurobi
	def solve(self, load=None, greenAvail=None, brownPrice=None, pue=None, steps=False, stateChargeBattery=False, stateNetMeter=False):
		# Solution and objective
		self.sol = None
		self.obj = None
		
		# Initialize parameters
		self.load = load
		self.greenAvail = greenAvail
		self.brownPrice = brownPrice
		self.pue = pue
		
		# Model
		m = Model("parasol")
		m.setParam("OutputFlag", 0)
		if self.options.timeLimit > 0:
			m.setParam("TimeLimit", self.options.timeLimit)

		# Parameters
		# Green availability
		MaxGreenAvail = 0.0
		if self.greenAvail != None:
			GreenAvail = {}
			jG = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(self.greenAvail)>jG+1 and self.greenAvail[jG+1].t <= ts:
					jG += 1
				GreenAvail[t] = self.greenAvail[jG].v
				if GreenAvail[t] > MaxGreenAvail:
					MaxGreenAvail = GreenAvail[t]
		# Brown prices
		if self.brownPrice != None:
			BrownPrice = {}
			jB = 0
			for t in range(0, self.options.maxTime):
				# Look for current values
				ts = t*self.options.slotLength
				while len(self.brownPrice)>jB+1 and self.brownPrice[jB+1].t <= ts:
					jB += 1
				BrownPrice[t] = self.brownPrice[jB].v
		# PUE
		PUE = {}
		MaxPUE = 0.0
		if self.pue == None:
			# Default PUE
			for t in range(0, self.options.maxTime):
				PUE[t] = 1.0
		else:
			jP = 0
			for t in range(0, self.options.maxTime):
				# Look for current values
				ts = t*self.options.slotLength
				while len(self.pue)>jP+1 and self.pue[jP+1].t <= ts:
					jP += 1
				PUE[t] = self.pue[jP].v
				if PUE[t] > MaxPUE:
					MaxPUE = PUE[t]
		PUE[-1] = PUE[0] # Set value for the battery
		
		# Workload
		MaxWorkload = 0.0
		if self.load != None:
			Workload = {}
			jW = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(self.load)>jW+1 and self.load[jW+1].t <= ts:
					jW += 1
				Workload[t] = self.load[jW].v
				if Workload[t] > MaxWorkload:
					MaxWorkload = Workload[t]
		
		# Check maximum size for the values
		if self.largeNumber < MaxWorkload*MaxPUE:
			self.largeNumber =  int(10*MaxWorkload*MaxPUE)
		if self.largeNumber < MaxGreenAvail:
			self.largeNumber =  int(10*MaxGreenAvail)
		if self.largeNumber < self.options.maxSize*MaxPUE:
			self.largeNumber = int(10*self.options.maxSize*MaxPUE)
		
		# Integrate new variables
		m.update()

		# Variables
		# Load
		Load = {}
		for t in range(0, self.options.maxTime):
			Load[t] = m.addVar(lb=self.options.minSize, ub=self.options.maxSize, name="Load["+str(t)+"]")
		if self.greenAvail != None:
			LoadGreen = {}
			for t in range(0, self.options.maxTime):
				LoadGreen[t] = m.addVar(ub=self.options.maxSize*PUE[t], name="LoadGreen["+str(t)+"]")
		if self.brownPrice != None:
			LoadBrown = {}
			for t in range(0, self.options.maxTime):
				LoadBrown[t] = m.addVar(ub=self.options.maxSize*PUE[t], name="LoadBrown["+str(t)+"]")
		
		# Battery
		if self.options.batCap > 0:
			LoadBatt = {}
			LoadBatt[-1] = 0.0
			for t in range(0, self.options.maxTime):
				LoadBatt[t] = m.addVar(ub=self.options.maxSize*PUE[t], name="LoadBatt["+str(t)+"]")
			# var BattGreen  {t in XTIME} >= 0;
			if self.greenAvail != None:
				BattGreen = {}
				BattGreen[-1] = 0.0
				for t in range(0, self.options.maxTime):
					BattGreen[t] = m.addVar(name="BattGreen["+str(t)+"]")
			if self.brownPrice != None:
				BattBrown = {}
				BattBrown[-1] = 0.0
				for t in range(0, self.options.maxTime):
					BattBrown[t] = m.addVar(name="BattBrown["+str(t)+"]")
			CapBattery = {}
			CapBattery[-1] = self.options.batIniCap
			if CapBattery[-1] > self.options.batCap:
				CapBattery[-1] = self.options.batCap
			for t in range(0, self.options.maxTime):
				CapBattery[t] = m.addVar(ub=self.options.batCap, name="CapBattery["+str(t)+"]")
		
		# Peak costs
		if self.brownPrice != None:
			if self.options.peakCost != None:
				PeakBrown =     m.addVar(lb=0.0, ub=max(self.options.maxSize*MaxPUE+self.options.batChargeRate, self.options.previousPeak),     name="PeakBrown")
			if self.options.peakCostLife != None:
				PeakBrownLife = m.addVar(lb=0.0, ub=max(self.options.maxSize*MaxPUE+self.options.batChargeRate, self.options.previousPeakLife), name="PeakBrownLife")
			
		# Net metering
		if self.greenAvail != None and self.brownPrice != None:
			NetGreen = {}
			for t in range(0, self.options.maxTime):
				NetGreen[t] = m.addVar(name="NetGreen["+str(t)+"]")
		
		# Finish variables declaration
		m.update()
		
		# Optimization function
		optFunction = 0.0
		if self.options.optCost>0.0 and self.brownPrice != None:
			optCost = 0.0
			# Add energy costs for a day ($/day)
			optCost += quicksum(LoadBrown[t]/1000.0 * BrownPrice[t] for t in range(0, self.options.maxTime)) # kWh x $/kWh = $
			if self.options.batCap > 0:
				optCost += quicksum(BattBrown[t]/1000.0 * BrownPrice[t] for t in range(0, self.options.maxTime)) # kWh x $/kWh = $
			if self.greenAvail != None and self.options.netMeter!=None:
				optCost -= quicksum(NetGreen[t]/1000.0 * self.options.netMeter*BrownPrice[t] for t in range(0, self.options.maxTime)) # kWh x $/kWh = $
			#for t in range(0, self.options.maxTime):
				#optCost += LoadBrown[t]/1000.0 * BrownPrice[t] # kWh x $/kWh = $
				#if self.options.batCap > 0:
					#optCost += BattBrown[t]/1000.0 * BrownPrice[t]# kWh x $/kWh = $
				#if self.greenAvail != None and self.options.netMeter!=None:
					#optCost -= NetGreen[t]/1000.0 * self.options.netMeter*BrownPrice[t] # kWh x $/kWh = $
			# Add peak power cost in a linear way ($/day)
			if self.options.peakCost != None:
				optCost += PeakBrown/1000.0 * self.options.peakCost/30.0 # Account the month (30 days) for just one day: kW x $/kW/day = $/day
			# Add peak power cost for life time ($/day)
			if self.options.peakCostLife != None:
				optCost += PeakBrownLife * self.options.peakCostLife/(TOTAL_YEARS*365.0) # Account the building (12 years): W x ($/W)/day = $/day
			# Add the final cost function to the optimization function
			optFunction += self.options.optCost * optCost * 1000.0
		
		# Add a delta to avoid net metering and battery changes
		if self.greenAvail != None and self.brownPrice != None and self.options.batCap > 0:
			if stateChargeBattery:
				optFunction -= 0.0001*(BattGreen[0]+LoadGreen[0])
			elif stateNetMeter:
				optFunction -= 0.0001*(NetGreen[0]+LoadGreen[0])

		# Dump objective function
		#m.setObjective(optFunction, GRB.MAXIMIZE)
		m.setObjective(optFunction, GRB.MINIMIZE)
		
		m.update()
		
		# Constraints
		# Load constraints
		if self.load != None:
			if not self.options.loadDelay:
				for t in range(0, self.options.maxTime):
					#m.addConstr(Load[t] >= Workload[t], "WorkloadMin["+str(t)+"]")
					m.addConstr(Load[t] == Workload[t], "WorkloadMin["+str(t)+"]") # Make it tight
			else:
				# Summation of powers have to be the power required by the workload
				# Checking previous load is actually executed
				if self.options.optPerf == 0:
					sumLoad = quicksum(Load[t] for t in range(0, self.options.maxTime))
					#sumWorkload = self.options.prevLoad + quicksum(Workload[t] for t in range(0, self.options.maxTime))
					sumWorkload = self.options.prevLoad/self.options.compression + quicksum(Workload[t] for t in range(0, self.options.maxTime))
					#sumWorkload = (self.options.prevLoad + quicksum(Workload[t] for t in range(0, self.options.maxTime)))/self.options.compression
					m.addConstr(sumLoad >= sumWorkload, "WorkloadMin")
				else:
					# We don't need to run everything if we try to minimize the difference
					pass
				
				# Guarrantee that the load is already there
				#for t in range(0, self.options.maxTime):
				for t in range(1, self.options.maxTime):
					sumLoadT = quicksum(Load[t] for t in range(0, t))
					#sumWorkloadT = self.options.prevLoad + quicksum(Workload[t] for t in range(0, t))
					sumWorkloadT = self.options.prevLoad/self.options.compression + quicksum(Workload[t] for t in range(0, t))
					#sumWorkloadT = (self.options.prevLoad + quicksum(Workload[t] for t in range(0, t)))/self.options.compression
					m.addConstr(sumLoadT <= sumWorkloadT, "WorkloadMin["+str(t)+"]") # +1 to have some margin
			if self.options.minSizeIni != None:
				m.addConstr(Load[0] >= self.options.minSizeIni, 'WorkloadMinInitial')
		
		# Load distribution
		# s.t. LoadProvide {t in TIME} :   Load[t] =  LoadGreen[t] + LoadBatt[t];
		# s.t. MaxSize {t in TIME} :       Load[t] <= maxSize;
		for t in range(0, self.options.maxTime):
			aux = 0
			if self.greenAvail != None:
				aux += LoadGreen[t]
			if self.brownPrice != None:
				aux += LoadBrown[t]
			if self.options.batCap > 0:
				aux += LoadBatt[t]
			m.addConstr(PUE[t] * Load[t] == aux,  "LoadProvide["+str(t)+"]")
		
		# Maximum green availability
		# s.t. MaxGreen {t in TIME} :      LoadGreen[t] + BattGreen[t] + NetGreen[t] <= GreenAvail[t]"
		for t in range(0, self.options.maxTime):
			if self.greenAvail != None:
				aux = 0
				if self.options.batCap > 0:
					aux += BattGreen[t]
				if self.greenAvail != None and self.brownPrice != None:
					aux += NetGreen[t]
				#m.addConstr(LoadGreen[t] + aux <= GreenAvail[t], "MaxGreen["+str(t)+"]")
				m.addConstr(LoadGreen[t] + aux == GreenAvail[t], "MaxGreen["+str(t)+"]") # Make it tight
		
		# Battery
		if self.options.batCap > 0:
			# There seems to be a bug in Gurobi. If the initial battery is the maximum, it breaks
			if CapBattery[-1] == self.options.batCap:
				CapBattery[-1] -= 0.001
			# We cannot discharge more than available
			for t in range(0, self.options.maxTime):
				m.addConstr(LoadBatt[t] <= CapBattery[t], "CapBatteryT["+str(t)+"]")
			# Charge battery
			for t in range(0, self.options.maxTime):
				aux = 0
				if self.brownPrice != None:
					aux += BattBrown[t-1]
				if self.greenAvail != None:
					aux += BattGreen[t-1]
				m.addConstr(CapBattery[t] == CapBattery[t-1] + self.options.batEfficiency*aux - LoadBatt[t-1], "ChargeBattery["+str(t)+"]")
			# Maximum battery charge rate (kW)
			if self.options.batChargeRate > 0 and (self.greenAvail != None or self.brownPrice != None):
				# s.t. BattRate {t in TIME} :  <= self.options.batChargeRate
				for t in range(0, self.options.maxTime):
					aux = 0
					if self.greenAvail != None:
						aux += BattGreen[t]
					if self.brownPrice != None:
						aux += BattBrown[t]
					m.addConstr(aux <= self.options.batChargeRate, "BattRate["+str(t)+"]")
			# Maximum depth of discharge (to extend battery lfietime)
			if self.options.batDischargeMax != None:
				minPercentage = 1.0 - self.options.batDischargeMax
				# Adapt DoD taking into account initial capacity
				if CapBattery[-1]/self.options.batCap < minPercentage:
					minPercentage = CapBattery[-1]/self.options.batCap
				# System protection: it is usually 15%+10% = 25%
				if self.options.batDischargeProtection != None:
					if self.options.batDischargeProtection > minPercentage:
						minPercentage = self.options.batDischargeProtection
				# Depth of discharge
				for t in range(0, self.options.maxTime):
					#m.addConstr(CapBattery[t] >= self.options.batCap*(1.0 - batDischargeMax), "Batt["+str(t)+"]")
					m.addConstr(CapBattery[t] >= self.options.batCap*minPercentage, "Batt["+str(t)+"]")
			'''
			# System protection: it is usually 15%+10% = 25%
			if self.options.batDischargeProtection != None:
				for t in range(0, self.options.maxTime):
					m.addConstr(CapBattery[t] >= self.options.batCap*self.options.batDischargeProtection, "BattProtection["+str(t)+"]")
			'''
		
		# Peak cost constraints
		if self.options.peakCost != None and self.brownPrice != None:
			for t in range(0, self.options.maxTime):
				aux = LoadBrown[t]
				if self.options.batCap > 0:
					aux += BattBrown[t]
				m.addConstr(aux <= PeakBrown, "Peak["+str(t)+"]")
			m.addConstr(self.options.previousPeak <= PeakBrown)
		# Peak cost constraints
		if self.options.peakCostLife != None and self.brownPrice != None:
			for t in range(0, self.options.maxTime):
				aux = LoadBrown[t]
				if self.options.batCap > 0:
					aux += BattBrown[t]
				m.addConstr(aux <= PeakBrownLife, "Peak["+str(t)+"]")
			m.addConstr(self.options.previousPeakLife <= PeakBrownLife)
		
		# Parasol constraints
		# Constraints: We can only do one thing at a time
		for t in range(0, self.options.maxTime):
			# LoadBrown > 0  => NetGreen = 0
			if self.brownPrice != None and self.greenAvail != None:
				self.addConstrXlt0implYeq0(m, LoadBrown[t], NetGreen[t])
			# LoadBatt > 0  => NetGreen + BattBrown + BattGreen = 0 
			if self.options.batCap > 0 and self.greenAvail != None:
				self.addConstrXlt0implYeq0(m, LoadBatt[t],  BattGreen[t] + ((NetGreen[t] + BattBrown[t]) if self.brownPrice != None else 0))
			# BattGreen > 0 => LoadBrown = 0
			#if self.options.batCap > 0 and self.greenAvail != None and self.brownPrice != None:
				#self.addConstrXlt0implYeq0(m, BattGreen[t], LoadBrown[t])
			# BattGreen > 0 => NetGreen = 0
			#if self.options.batCap > 0 and self.greenAvail != None and self.brownPrice != None:
				#self.addConstrXlt0implYeq0(m, BattGreen[t] + BattBrown[t], NetGreen[t])
		
		m.update()
		
		# Solver parameters
		
		#m.setParam("OutputFlag", 1)
		#m.setParam("MIPGap", 0.0)
		#m.setParam("FeasibilityTol", 1e-09)
		#m.setParam("IntFeasTol", 1e-09)
		#m.setParam("OptimalityTol", 1e-09)
		#m.setParam("Quad", 1)
		#m.setParam("ObjScale", 1)
		if self.saveModel:
			m.write('test.mps')
		
		# Solve
		m.optimize()
		
		if self.saveModel:
			#print 'SOLUUUUUUUUUUUUUUUUUUTION'
			#print LoadBrown[0].x, LoadGreen[0].x, LoadBatt[0].x
			#print 'SOLUUUUUUUUUUUUUUUUUUTION'
			m = read('test.mps')
			m.optimize()
			#print m.getVars()
			self.sol = {}
			for var in m.getVars():
				self.sol[str(var).split(' ')[1]] = var.x		
		
		if m.status == GRB.status.LOADED:
			print "Loaded"
		elif m.status == GRB.status.INFEASIBLE:
			if self.options.debug > 0:
				print "Infeasible"
		elif m.status == GRB.status.OPTIMAL:
			if self.options.debug > 0:
				print "Optimal"
		elif m.status == GRB.status.INF_OR_UNBD:
			if self.options.debug > 0:
				print "Infeasible or Unbounded"
		elif m.status == GRB.status.CUTOFF:
			print "Cutoff"
		elif m.status == GRB.status.ITERATION_LIMIT:
			print "Iteration limit"
		elif m.status == GRB.status.NODE_LIMIT:
			print "Node limit"
		elif m.status == GRB.status.SOLUTION_LIMIT:
			print "Solution limit"
		elif m.status == GRB.status.INTERRUPTED:
			print "Interrupted"
		elif m.status == GRB.status.SUBOPTIMAL:
			print "Suboptimal"
		elif m.status == GRB.status.NUMERIC:
			print "Numeric"
		elif m.status == GRB.status.UNBOUNDED:
			print "Unbounded"
		elif m.status == GRB.status.TIME_LIMIT:
			print "Time limit"
		else:
			print "Unknown:", m.status
		
		# Get solution
		try:
			if m.status != GRB.status.INF_OR_UNBD and m.status != GRB.status.INFEASIBLE:
				self.obj = m.objVal
				self.sol = {}
				# Parameters
				for t in range(0, self.options.maxTime):
					# Workload
					if self.load != None:
						self.sol["Workload["+str(t)+"]"] = Workload[t]
					if self.brownPrice != None:
						self.sol["BrownPrice["+str(t)+"]"] = BrownPrice[t]
				# Variables
				for t in range(0, self.options.maxTime):
					self.sol["Load["+str(t)+"]"] = Load[t].x
					if self.greenAvail != None:
						self.sol["LoadGreen["+str(t)+"]"] = LoadGreen[t].x
						if self.sol["LoadGreen["+str(t)+"]"] < 1:
							self.sol["LoadGreen["+str(t)+"]"] = 0.0
					if self.brownPrice != None:
						self.sol["LoadBrown["+str(t)+"]"] = LoadBrown[t].x
						if self.sol["LoadBrown["+str(t)+"]"] < 1:
							self.sol["LoadBrown["+str(t)+"]"] = 0.0
					if self.options.batCap > 0:
						self.sol["LoadBatt["+str(t)+"]"] = LoadBatt[t].x
						if self.sol["LoadBatt["+str(t)+"]"] < 1:
							self.sol["LoadBatt["+str(t)+"]"] = 0.0
						if self.greenAvail != None:
							self.sol["BattGreen["+str(t)+"]"] = BattGreen[t].x
							if self.sol["BattGreen["+str(t)+"]"] < 1:
								self.sol["BattGreen["+str(t)+"]"] = 0.0
						if self.brownPrice != None:
							self.sol["BattBrown["+str(t)+"]"] = BattBrown[t].x
							if self.sol["BattBrown["+str(t)+"]"] < 1:
								self.sol["BattBrown["+str(t)+"]"] = 0.0
						self.sol["CapBattery["+str(t)+"]"] = CapBattery[t].x
					if self.brownPrice != None and self.greenAvail != None:
						self.sol["NetGreen["+str(t)+"]"] = NetGreen[t].x
						if self.sol["NetGreen["+str(t)+"]"] < 1:
							self.sol["NetGreen["+str(t)+"]"] = 0.0
					# Default values
					if "LoadBrown["+str(t)+"]" not in self.sol:
						self.sol["LoadBrown["+str(t)+"]"] = 0.0
					if "BattBrown["+str(t)+"]" not in self.sol:
						self.sol["BattBrown["+str(t)+"]"] = 0.0
					if "BattGreen["+str(t)+"]" not in self.sol:
						self.sol["BattGreen["+str(t)+"]"] = 0.0
					if "LoadBatt["+str(t)+"]" not in self.sol:
						self.sol["LoadBatt["+str(t)+"]"] = 0.0
					if "NetGreen["+str(t)+"]" not in self.sol:
						self.sol["NetGreen["+str(t)+"]"] = 0.0
				if self.options.peakCost!=None and self.brownPrice != None:
					self.sol["PeakBrown"] = PeakBrown.x
				else:
					self.sol["PeakBrown"] = 0.0
					for t in range(0, self.options.maxTime):
						if self.sol["LoadBrown["+str(t)+"]"] + self.sol["BattBrown["+str(t)+"]"] > self.sol["PeakBrown"]:
							self.sol["PeakBrown"] = self.sol["LoadBrown["+str(t)+"]"] + self.sol["BattBrown["+str(t)+"]"]
				if self.options.peakCostLife!=None and self.brownPrice != None:
					self.sol["PeakBrownLife"] = PeakBrownLife.x
				else:
					self.sol["PeakBrownLife"] = 0.0
					for t in range(0, self.options.maxTime):
						if self.sol["LoadBrown["+str(t)+"]"] + self.sol["BattBrown["+str(t)+"]"] > self.sol["PeakBrownLife"]:
							self.sol["PeakBrownLife"] = self.sol["LoadBrown["+str(t)+"]"] + self.sol["BattBrown["+str(t)+"]"]
		except Exception, e:
			print 'Error reading solution. State=%d. Message: %s.' % (m.status, str(e))
		
		# Return result
		if steps:
			return m.status, self.obj, self.sol
		else:
			return self.obj, self.sol

	# X>0 => Y=0
	# if X > 0:
	#     Y=0
	def addConstrXlt0implYeq0(self, m, X, Y):
		# X >= 0; Y >= 0
		# X <= bin * inf
		# bin <= X * inf
		# Y <= 1-bin * inf
		# aux - Y >= 0
		# Y - aux >= bin * -inf 
		
		# Auxiliar variables for MILP constraints
		#auxvar = m.addVar()
		#auxbin = m.addVar(vtype=GRB.BINARY)
		auxvar = self.getAuxVar(m)
		auxbin = self.getAuxBin(m)
		
		# New constraints
		#LARGE = 99999
		#LARGE = 9999999
		m.addConstr(X <= auxbin * self.largeNumber*2)
		m.addConstr(auxbin <= X * self.largeNumber*2)
		m.addConstr(Y <= (1-auxbin) * self.largeNumber*2)
		m.addConstr(auxvar - Y >= 0)
		m.addConstr(Y - auxvar >= auxbin * -self.largeNumber*2)
	
	# Get an auxiliary variable
	def getAuxVar(self, m):
		if len(self.auxvars)==0:
			for t in range(0, self.options.maxTime):
				self.auxvars.append(m.addVar())
			m.update()
		return self.auxvars.pop()
		
	# Get an auxiliary variable
	def getAuxBin(self, m):
		if len(self.auxbins)==0:
			for t in range(0, self.options.maxTime):
				self.auxbins.append(m.addVar(vtype=GRB.BINARY))
			m.update()
		return self.auxbins.pop()
	
	# Show the results of the optimization
	def printResults(self):
		if self.obj != None:
			# Run execution simulation
			PRICE_THRES = 0.09 # Cheap and expensive price
			totalUseBrown = 0.0
			totalUseBrownCost = 0.0
			totalUseGreen = 0.0
			totalAvailGreen = 0.0
			totalUseBatte = 0.0
			totalNetMeter = 0.0
			totalNetMeterCost = 0.0
			totalQualityFraction = 0.0
			prevLine = None

			if self.options.output != None:
				out = open(self.options.output, "w")
				out.write("#t\tuseGree\tuseBrow\tuseChea\tuseExpe\tuseBatt\tcapBatt\tavGreen\tcurLoad\tpriceBr\tnetMet\tqos\tworkload\n")
				out.write("0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")
			
			print "Running simulation..."
			for t in range(0, self.options.maxTime):
				# Inputs
				ts = t*self.options.slotLength
				jG = jB = jL = 0
				curGreen = 0.0
				if self.greenAvail != None:
					while len(self.greenAvail)>jG+1 and self.greenAvail[jG+1].t <= ts: jG += 1 # Green
					curGreen = self.greenAvail[jG].v
				priceBrown = 0.0
				if self.brownPrice != None:
					while len(self.brownPrice)>jB+1 and self.brownPrice[jB+1].t <= ts: jB += 1 # Brown
					priceBrown = self.brownPrice[jB].v
				curLoad = 0.0
				#if load != None:
					#while len(load)>jL+1 and load[jL+1].t <= ts: jL += 1 # Load
					#curLoad = load[jL].v
				#curLoad = self.sol["Load["+str(t)+"]"]
				
				# Read result
				# Load
				if "LoadGreen["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadGreen["+str(t)+"]"]
				if "LoadBrown["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadBrown["+str(t)+"]"]
				if "LoadBatt["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadBatt["+str(t)+"]"]
				# Green
				useGreen = 0.0
				netMeter = 0.0
				if "LoadGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["LoadGreen["+str(t)+"]"]
				if "BattGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["BattGreen["+str(t)+"]"]
				if "NetGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["NetGreen["+str(t)+"]"]
					netMeter += self.sol["NetGreen["+str(t)+"]"]
				# Brown
				useBrown = 0.0
				useBrownCheap = 0.0
				useBrownExpen = 0.0
				if "LoadBrown["+str(t)+"]" in self.sol: 
					useBrown += self.sol["LoadBrown["+str(t)+"]"] 
				if "BattBrown["+str(t)+"]" in self.sol:
					useBrown += self.sol["BattBrown["+str(t)+"]"]
				# Brown price
				if self.brownPrice != None:
					if priceBrown < PRICE_THRES:
						useBrownCheap = useBrown
						useBrownExpen = 0.0
					else:
						useBrownCheap = 0.0
						useBrownExpen = useBrown
				# Battery
				useBatte = 0.0
				capBatte = 0.0
				if self.options.batCap > 0:
					#print sol
					if "LoadBatt["+str(t)+"]" in self.sol: 
						useBatte = self.sol["LoadBatt["+str(t)+"]"]
					if "CapBattery["+str(t)+"]" in self.sol: 
						capBatte = self.sol["CapBattery["+str(t)+"]"]
				# Degraded quality
				fraction = 0.0
				if "Fraction["+str(t)+"]" in self.sol: 
					fraction = self.sol["Fraction["+str(t)+"]"]
					totalQualityFraction += fraction
				# workload
				workload = 0.0
				if "Workload["+str(t)+"]" in self.sol: 
					workload = self.sol["Workload["+str(t)+"]"]
				
				# Summarize
				totalUseBrown += useBrown
				totalUseGreen += useGreen
				totalAvailGreen += curGreen
				totalUseBrownCost += (useBrown/1000.0)*priceBrown
				totalUseBatte += useBatte
				totalNetMeter += netMeter
				totalNetMeterCost += (netMeter/1000.0)*priceBrown*self.options.netMeter
				# Ouput
				if self.options.debug > 0:
					print ts, useGreen, useBrown, useBatte, capBatte
				if self.options.output != None:
					if prevLine != None:
						out.write(str(ts/(1.0*self.options.slotLength))+"\t"+prevLine+"\n")
					prevLine = str(useGreen)+"\t"+str(useBrown)+"\t"+str(useBrownCheap)+"\t"+str(useBrownExpen)+"\t"+str(useBatte)+"\t"
					prevLine+= str(capBatte)+"\t"+str(curGreen)+"\t"+str(curLoad)+"\t"+str(priceBrown)+"\t"+str(netMeter)+"\t"+str(fraction)+"\t"+str(workload)
					out.write(str(ts/(1.0*self.options.slotLength))+"\t"+prevLine+"\n")

			if self.options.output != None:
				out.write(str(ts/(1.0*self.options.slotLength))+"\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")
			
			# Result summary
			print "Summary:"
			print "\tBrown: %s $%.2f" % (toEnergyString(totalUseBrown*self.options.slotLength), totalUseBrownCost)
			if self.options.peakCost != None:
				print "\tPeak:  %dW $%.2f" % (self.sol["PeakBrown"], self.sol["PeakBrown"]/1000.0*self.options.peakCost)
			else:
				print "\tPeak:  %dW $-" % (self.sol["PeakBrown"])
			print "\tGreen:", toEnergyString(totalUseGreen*self.options.slotLength)
			print "\tBatte:", toEnergyString(totalUseBatte*self.options.slotLength)
			print "\tNet:  ", toEnergyString(totalNetMeter*self.options.slotLength), "$%.2f" % (totalNetMeterCost)

			if self.options.report != None:
				report = open(self.options.report, "w")
				report.write("Brown: %s $%.2f\n" % (toEnergyString(totalUseBrown*self.options.slotLength), totalUseBrownCost))
				report.write("Green: %s\n" % (toEnergyString(totalUseGreen*self.options.slotLength)))
				report.write("Green available: %s\n" % (toEnergyString(totalAvailGreen*self.options.slotLength)))
				report.write("Battery: %s\n" % (toEnergyString(totalUseBatte*self.options.slotLength)))
				report.write("Net: %s $%.2f\n" % (toEnergyString(totalNetMeter*self.options.slotLength), totalNetMeterCost))
				report.write("Degraded quality: %.2f%%\n" % ((totalQualityFraction*100.0)/self.options.maxTime))
				
				report.close()
	
	def writeOutput(self):
		if self.obj != None and self.options.output != None:
			# Run execution simulation
			PRICE_THRES = 0.09 # Cheap and expensive price
			totalUseBrown = 0.0
			totalUseBrownCost = 0.0
			totalUseGreen = 0.0
			totalAvailGreen = 0.0
			totalUseBatte = 0.0
			totalNetMeter = 0.0
			totalNetMeterCost = 0.0
			totalQualityFraction = 0.0
			prevLine = None

			# Output
			out = open(self.options.output, "w")
			out.write("#t\tuseGree\tuseBrow\tuseChea\tuseExpe\tuseBatt\tcapBatt\tavGreen\tcurLoad\tpriceBr\tnetMet\tqos\n")
			out.write("0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")
			
			# Simulation
			for t in range(0, self.options.maxTime):
				# Inputs
				ts = t*self.options.slotLength
				jG = jB = jL = 0
				curGreen = 0.0
				if self.greenAvail != None:
					while len(self.greenAvail)>jG+1 and self.greenAvail[jG+1].t <= ts: jG += 1 # Green
					curGreen = self.greenAvail[jG].v
				priceBrown = 0.0
				if self.brownPrice != None:
					while len(self.brownPrice)>jB+1 and self.brownPrice[jB+1].t <= ts: jB += 1 # Brown
					priceBrown = self.brownPrice[jB].v
				curLoad = 0.0
				
				# Read result
				# Load
				if "LoadGreen["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadGreen["+str(t)+"]"]
				if "LoadBrown["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadBrown["+str(t)+"]"]
				if "LoadBatt["+str(t)+"]" in self.sol:
					curLoad += self.sol["LoadBatt["+str(t)+"]"]
				# Green
				useGreen = 0.0
				netMeter = 0.0
				if "LoadGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["LoadGreen["+str(t)+"]"]
				if "BattGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["BattGreen["+str(t)+"]"]
				if "NetGreen["+str(t)+"]" in self.sol:
					useGreen += self.sol["NetGreen["+str(t)+"]"]
					netMeter += self.sol["NetGreen["+str(t)+"]"]
				# Brown
				useBrown = 0.0
				useBrownCheap = 0.0
				useBrownExpen = 0.0
				if "LoadBrown["+str(t)+"]" in self.sol: 
					useBrown += self.sol["LoadBrown["+str(t)+"]"] 
				if "BattBrown["+str(t)+"]" in self.sol:
					useBrown += self.sol["BattBrown["+str(t)+"]"]
				# Brown price
				if self.brownPrice != None:
					if priceBrown < PRICE_THRES:
						useBrownCheap = useBrown
						useBrownExpen = 0.0
					else:
						useBrownCheap = 0.0
						useBrownExpen = useBrown
				# Battery
				useBatte = 0.0
				capBatte = 0.0
				if self.options.batCap > 0:
					if "LoadBatt["+str(t)+"]" in self.sol: 
						useBatte = self.sol["LoadBatt["+str(t)+"]"]
					if "CapBattery["+str(t)+"]" in self.sol: 
						capBatte = self.sol["CapBattery["+str(t)+"]"]
				# Degraded quality
				fraction = 0.0
				if "Fraction["+str(t)+"]" in self.sol: 
					fraction = self.sol["Fraction["+str(t)+"]"]
					totalQualityFraction += fraction
				
				# Summarize
				totalUseBrown += useBrown
				totalUseGreen += useGreen
				totalAvailGreen += curGreen
				totalUseBrownCost += (useBrown/1000.0)*priceBrown
				totalUseBatte += useBatte
				totalNetMeter += netMeter
				totalNetMeterCost += (netMeter/1000.0)*priceBrown*self.options.netMeter
				
				# Ouput
				if prevLine != None:
					out.write(str(ts/(1.0*self.options.slotLength))+"\t"+prevLine+"\n")
				prevLine = str(useGreen)+"\t"+str(useBrown)+"\t"+str(useBrownCheap)+"\t"+str(useBrownExpen)+"\t"+str(useBatte)+"\t"
				prevLine+= str(capBatte)+"\t"+str(curGreen)+"\t"+str(curLoad)+"\t"+str(priceBrown)+"\t"+str(netMeter)+"\t"+str(fraction)
				out.write(str(ts/(1.0*self.options.slotLength))+"\t"+prevLine+"\n")

			out.write(str(ts/(1.0*self.options.slotLength))+"\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")

if __name__=='__main__':
	start = datetime.now()
	
	# Input parameters
	'''
	greenAvail = None
	brownPrice = None
	workload = None
	greenAvail = readGreenAvailFile("data/solarpower-06-07-2011")
	brownPrice = readDataTimeValue("data/browncost-onoffpeak-summer.nj")
	workload =   readDataTimeValue("data/test.load")
	
	# Shift to current date
	now = datetime.now()
	time = now.timetuple()
	secs = int(time[3])*3600
	secs += int(time[4])*60
	secs += int(time[5])
	
	for tv in brownPrice:
		tv.t -= secs
	
	# Shift
	#tv = TimeValue(10, 0)
	#for tv in greenAvail:
		#tv.t = tv.t-(12*3600)
	'''
	
	# Solve model
	solver = ParasolModel()
	'''
	solver.options.optCost = 1.0
	solver.options.output = 'out3.data'
	solver.options.loadDelay = True
	#solver.options.prevLoad = 5000.0
	solver.options.netMeter = 0.0
	solver.options.peakCost = 13.6136
	solver.options.peakCost = 0.0
	#solver.options.peakCost = None
	solver.options.previousPeak = 1500.0
	solver.options.minSize = 279 # Covering subset
	solver.options.maxSize = 2100 # Max size
	solver.options.batCap = 0.0
	solver.options.batCap = 27200.0
	#solver.options.batIniCap = 27200.0
	#solver.options.batIniCap = 27000.0
	#solver.options.batDischargeMax = 0.235294117647
	solver.options.prevLoad = 0.0
	
	# Outage
	solver.options.batIniCap = 0.30*solver.options.batCap # 78%
	#solver.options.batIniCap = 0.35*27200.0 # 78%
	solver.options.batDischargeMax = None
	solver.options.optCost = 0.0
	solver.options.optPerf = 1.0
	
	secondsdelay = 20*3600
	'''
		
	'''
	# Define input parameters
	greenAvail = [TimeValue(0,1685.00),TimeValue(3600,1597.11),TimeValue(2*3600,1710.79),TimeValue(3*3600,1586.00),TimeValue(14400,1342.94),
		TimeValue(18000,1025.41),TimeValue(21600,675.72),TimeValue(25200,325.64),TimeValue(28800,76.17),TimeValue(32400,3.37),
		TimeValue(36000,0.00),TimeValue(39600,0.00),TimeValue(43200,0.00),TimeValue(46800,0.00),TimeValue(50400,0.00),
		TimeValue(54000,0.00),TimeValue(57600,0.00),TimeValue(61200,0.00),TimeValue(64800,0.00),TimeValue(68400,0.00),
		TimeValue(72000,23.95),TimeValue(75600,159.47),TimeValue(79200,467.53),TimeValue(82800,964.34),TimeValue(86400,2313.47),
		TimeValue(90000,2975.02),TimeValue(93600,3168.14),TimeValue(97200,3050.00),TimeValue(100800,2741.84),TimeValue(104400,2283.86),
		TimeValue(108000,1672.40),TimeValue(111600,930.40),TimeValue(115200,251.37),TimeValue(118800,13.61),TimeValue(122400,0.00),
		TimeValue(126000,0.00),TimeValue(129600,0.00),TimeValue(133200,0.00),TimeValue(136800,0.00),TimeValue(140400,0.00),
		TimeValue(144000,0.00),TimeValue(147600,0.00),TimeValue(151200,0.00),TimeValue(154800,0.00),TimeValue(158400,167.68),
		TimeValue(162000,751.81),TimeValue(165600,1402.59),TimeValue(169200,2338.52),TimeValue(172800,2627.64)]
		
	greenAvail = [
		TimeValue(0*3600,0.00),
		TimeValue(1*3600,0.00),
		TimeValue(2*3600,0.00),
		TimeValue(3*3600,0.00),
		TimeValue(4*3600,0.00),
		TimeValue(5*3600,0.00),
		TimeValue(6*3600,23.95),
		TimeValue(7*3600,159.47),
		TimeValue(8*3600,467.53),
		TimeValue(9*3600,964.34),
		TimeValue(10*3600,2313.47),
		TimeValue(11*3600,2975.02),
		TimeValue(12*3600,3168.14),
		TimeValue(13*3600,3050.00),
		TimeValue(14*3600,2741.84),
		TimeValue(15*3600,2283.86),
		TimeValue(16*3600,1672.40),
		TimeValue(17*3600,930.40),
		TimeValue(18*3600,251.37),
		TimeValue(19*3600,13.61),
		TimeValue(20*3600,0.00),
		TimeValue(21*3600,0.00),
		TimeValue(22*3600,0.00),
		TimeValue(23*3600,0.00),
		TimeValue(24*3600,0.00),
		TimeValue(25*3600,0.00),
		TimeValue(26*3600,0.00),
		TimeValue(27*3600,0.00),
		TimeValue(28*3600,0.00),
		TimeValue(29*3600,0.00),
		TimeValue(30*3600,167.68),
		TimeValue(31*3600,751.81),
		TimeValue(32*3600,1402.59),
		TimeValue(33*3600,2338.52),
		TimeValue(34*3600,2627.64)]
	for tv in greenAvail:
		tv.t -= secondsdelay
		
	brownPrice = readDataTimeValue("data/browncost-onoffpeak-summer.nj")
	# Shift time
	for tv in brownPrice:
		tv.t -= secondsdelay
	#brownPrice = None
	
	workload = readDataTimeValue("data/outageworkload")
	# Shift workload time
	time = now.timetuple()
	secs = int(time[3])*3600 # hours
	secs += int(time[4])*60  # minutes
	secs += int(time[5])     # seconds
	#secs = secs % (24*60*60)
	for tv in workload:
		tv.t -= secondsdelay
	'''
	
	# DEBUGGING
	brownPrice = [TimeValue(0, 0.117500), 
		TimeValue(3600, 0.117500), 
		TimeValue(7200, 0.117500), 
		TimeValue(10800, 0.117500), 
		TimeValue(14400, 0.117500), 
		TimeValue(18000, 0.117500), 
		TimeValue(21600, 0.117500), 
		TimeValue(25200, 0.117500), 
		TimeValue(28800, 0.080017), 
		TimeValue(32400, 0.080017), 
		TimeValue(36000, 0.080017), 
		TimeValue(39600, 0.080017), 
		TimeValue(43200, 0.080017), 
		TimeValue(46800, 0.080017), 
		TimeValue(50400, 0.080017), 
		TimeValue(54000, 0.080017), 
		TimeValue(57600, 0.080017), 
		TimeValue(61200, 0.080017), 
		TimeValue(64800, 0.117500), 
		TimeValue(68400, 0.117500), 
		TimeValue(72000, 0.117500), 
		TimeValue(75600, 0.117500), 
		TimeValue(79200, 0.117500), 
		TimeValue(82800, 0.117500)]
	greenAvail = [TimeValue(0, 0.000000), 
		TimeValue(3600, 0.000000), 
		TimeValue(7200, 0.000000), 
		TimeValue(10800, 0.000000), 
		TimeValue(14400, 0.000000), 
		TimeValue(18000, 0.000000), 
		TimeValue(21600, 0.000000), 
		TimeValue(25200, 0.000000), 
		TimeValue(28800, 0.000000), 
		TimeValue(32400, 0.000000), 
		TimeValue(36000, 0.000000), 
		TimeValue(39600, 0.000000), 
		TimeValue(43200, 0.000000), 
		TimeValue(46800, 0.000000), 
		TimeValue(50400, 0.000000), 
		TimeValue(54000, 0.000000), 
		TimeValue(57600, 0.000000), 
		TimeValue(61200, 0.000000), 
		TimeValue(64800, 0.000000), 
		TimeValue(68400, 0.000000), 
		TimeValue(72000, 0.000000), 
		TimeValue(75600, 0.000000), 
		TimeValue(79200, 0.000000), 
		TimeValue(82800, 0.000000)]
	puePredi = [TimeValue(0, 1.187609), 
		TimeValue(3600, 1.187609), 
		TimeValue(7200, 1.166087), 
		TimeValue(10800, 1.136739), 
		TimeValue(14400, 1.126304), 
		TimeValue(18000, 1.115217), 
		TimeValue(21600, 1.119130), 
		TimeValue(25200, 1.122391), 
		TimeValue(28800, 1.122391), 
		TimeValue(32400, 1.126304), 
		TimeValue(36000, 1.119130), 
		TimeValue(39600, 1.115217), 
		TimeValue(43200, 1.111304), 
		TimeValue(46800, 1.111304), 
		TimeValue(50400, 1.115217), 
		TimeValue(54000, 1.108043), 
		TimeValue(57600, 1.108043), 
		TimeValue(61200, 1.129565), 
		TimeValue(64800, 1.147826), 
		TimeValue(68400, 1.169348), 
		TimeValue(72000, 1.180435), 
		TimeValue(75600, 1.194783), 
		TimeValue(79200, 1.194783), 
		TimeValue(82800, 1.194783)]
	worklPredi = [TimeValue(0, 3381786.689509), 
		TimeValue(3600, 3576087.988509), 
		TimeValue(7200, 3870235.030619), 
		TimeValue(10800, 4155499.063240), 
		TimeValue(14400, 4425937.380049), 
		TimeValue(18000, 4561783.027205), 
		TimeValue(21600, 4473279.958272), 
		TimeValue(25200, 4178951.303588), 
		TimeValue(28800, 3541607.605988), 
		TimeValue(32400, 2863838.329942), 
		TimeValue(36000, 2118686.189819), 
		TimeValue(39600, 1543440.407169), 
		TimeValue(43200, 1251385.686973), 
		TimeValue(46800, 1120830.945292), 
		TimeValue(50400, 1259456.634470), 
		TimeValue(54000, 1477364.739694), 
		TimeValue(57600, 1827444.704996), 
		TimeValue(61200, 2133174.794860), 
		TimeValue(64800, 2365043.625660), 
		TimeValue(68400, 2549364.176339), 
		TimeValue(72000, 2654499.693480), 
		TimeValue(75600, 2766692.256109), 
		TimeValue(79200, 2890722.461219), 
		TimeValue(82800, 3034743.237055)]
	stateChargeBattery = False
	stateNetMeter = False
	
	
	solver.options.optCost = 1.0
	solver.options.loadDelay = True
	solver.options.compression =  1.0
	solver.options.minSizeIni = 407464.0
	solver.options.minSize =    407464.0
	solver.options.maxSize =    5741520.0
	solver.options.netMeter = 0.4
	solver.options.batEfficiency = 0.87
	solver.options.batIniCap = 20062636.6517
	solver.options.batCap = 100000000.0
	solver.options.batDischargeMax = 0.8
	solver.options.batDischargeProtection = 0.2
	solver.options.batChargeRate = 0
	solver.options.prevLoad = 9957497.60376
	solver.options.previousPeak = 4539262.54908
	solver.options.previousPeakLife = 4539262.54908
	solver.options.peakCost = 5.59
	solver.options.peakCostLife = 10.0
	
	tnow = datetime.now()
	#obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, load=workload)
	#obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, load=workload, stateChargeBattery=False)
	obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, pue=puePredi, load=worklPredi, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
	#obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, load=workload, stateChargeBattery=False)
	print datetime.now()-tnow
	
	# Solution
	print "Time: %s" % (str(datetime.now()-start))
	if solver.obj == None:
		print "Opti: No solution"
	else:
		print "Opti: %.3f" % (solver.obj)

		# Print output
		solver.printResults()

		battBrown0 = solver.sol["BattBrown[0]"]
		battGreen0 = solver.sol["BattGreen[0]"]
		loadBatt0 = solver.sol["LoadBatt[0]"]
		loadBrown0 = solver.sol["LoadBrown[0]"]
		loadGreen0 = solver.sol["LoadGreen[0]"]

		print
		print "Current status:"
		print "\tLoad:          %.1f W = %.1f + %.1f + %.1f" % (loadBatt0+loadBrown0+loadGreen0, loadBatt0, loadBrown0, loadGreen0)
		print "\tSolar:         %.1f W" % (solver.sol["BattGreen[0]"] + solver.sol["LoadGreen[0]"])
		print "\tGrid:          %.1f W" % (solver.sol["LoadBrown[0]"] + solver.sol["BattBrown[0]"])
		print "\tNet meter:     %.1f W" % (solver.sol["NetGreen[0]"])
		print "\tBattery:       %.1f W = %.1f + %.1f - %.1f" % (battBrown0 + battGreen0 - loadBatt0, battBrown0, battGreen0, loadBatt0)
		
		print '\tLoad     ',  sol['Load[0]']
		print '\tLoadGreen',  sol['LoadGreen[0]']
		print '\tLoadBrown',  sol['LoadBrown[0]']
		print '\tLoadBatt ',   sol['LoadBatt[0]']
		print '\tBattBrown',  sol['BattBrown[0]']
		
		# Take actions
		# ============
		print
		print "State:"
		print "\tGrid:          ", (solver.sol["LoadBrown[0]"] + solver.sol["BattBrown[0]"]) > 0
		print "\tNet meter:     ", solver.sol["NetGreen[0]"] > 0
		print "\tBattery charge:", (solver.sol["BattBrown[0]"]+solver.sol["BattGreen[0]"]) > 0
		print "\tBattery dischr:", solver.sol["LoadBatt[0]"] > 0
		print "\tLoad:           %.1fW %d nodes" % (loadBatt0+loadBrown0+loadGreen0, (loadBatt0+loadBrown0+loadGreen0)/25.0)
		
		# Grid
		grid = False
		netmeter = False
		netmetergrid= False
		if solver.sol["LoadBrown[0]"] > 0 or solver.sol["BattBrown[0]"] > 0:
			grid = True
		elif solver.sol["NetGreen[0]"] > 0:
			grid = True
			netmeter = True
			netmetergrid = True
		# Battery charging
		batteryCharge = False
		if solver.sol["BattBrown[0]"] > 0  or solver.sol["BattGreen[0]"] > 0:
			batteryCharge = True
		if not grid and not netmeter:
			batteryCharge = True
		# Peak
		#if grid and not netmeter:
		if grid:
			if netmeter and not batteryCharge:
				# It is already like this, just to make it easy to understand
				grid = True
				batteryCharge = False
			elif netmeter and batteryCharge:
				grid = False
				batteryCharge = True
			else:
				maxCurrent = (solver.sol["LoadBrown[0]"] + solver.sol["BattBrown[0]"] + solver.sol["NetGreen[0]"])/250.0
				if maxCurrent > 48:
					maxCurrent = 48
				if solver.sol["LoadBatt[0]"] or batteryCharge:
					grid = maxCurrent
		
		print "Grid:", grid
		print "Battery:", batteryCharge
		
		
		# Workload delay
		if False:
			optfunction = 0
			for t in range(0, 24):
				optfunction += solver.sol["Load["+str(t)+"]"]-solver.sol["Workload["+str(t)+"]"]
				print t, solver.sol["Workload["+str(t)+"]"], solver.sol["Load["+str(t)+"]"], solver.sol["Load["+str(t)+"]"]-solver.sol["Workload["+str(t)+"]"], '=>', optfunction
			print "Result:", optfunction
