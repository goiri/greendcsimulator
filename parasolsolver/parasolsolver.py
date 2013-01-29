#!/usr/bin/env python

import os
import sys
import math
import socket

from parasolsolvercommons import *

from datetime import datetime



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

class ParasolModel:
	def __init__(self):
		self.options = SolverOptions()
		self.obj = None
		self.sol = None
		self.jobs = None
		self.load = None
		self.greenAvail = None
		self.brownPrice = None
	
	"""
	def solvePeak(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False, previousPeak=0.0, stateChargeBattery=False, stateNetMeter=False):
		# Boundaries for dicotomic search
		bottom = previousPeak # 0 Watt
		top = self.options.maxSize + self.options.batChargeRate
		bottomCost = None
		middleCost = None
		topCost = topCostAux = None
		
		# Calculate top and bottom
		# Top
		obj, sol = self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, peak=top)
		if obj != None:
			topCost = self.calculateElectricityBill(sol, previousPeak)
			topCostAux = topCost
		# Bottom
		obj, sol = self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, peak=bottom)
		if obj != None:
			bottomCost = self.calculateElectricityBill(sol, previousPeak)
		
		if self.options.peakCost!=None and self.options.peakCost!=0.0:
			# Find bottom using dicomotic search
			while (top-bottom) > 0.5:
				middle = bottom + (top-bottom)/4.0
				obj, sol = self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, peak=middle)
				if obj != None:
					middleCost = self.calculateElectricityBill(sol, previousPeak)
					if middleCost <= topCost:
						top = middle
						topCost = middleCost
					else:
						#bottom = middle
						#bottomCost = middleCost
						top = middle
						topCost = middleCost
				else:
					middleCost = None
					bottom = middle
					bottomCost = middleCost
		
			# Set valid area	
			bottom = middle
			bottomCost = middleCost
			if bottomCost == None:
				bottom = top
				bottomCost = topCost
			top = self.options.maxSize + self.options.batChargeRate
			topCost = topCostAux

			# Start dicotomic search in valid area
			while (top-bottom) > 0.5:
				middle = bottom + (top-bottom)/4.0
				obj, sol = self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, peak=middle)
				if obj != None:
					middleCost = self.calculateElectricityBill(sol, previousPeak)
					if middleCost <= topCost+0.0000001:
						top = middle
						topCost = middleCost
					else:
						bottom = middle
						bottomCost = middleCost
				else:
					# No solution
					bottom = middle
					bottomCost = None
					middle = top
					middleCost = topCost
		
		# Check solution
		if bottomCost != None:
			middle = bottom
			middleCost = bottomCost
		if middleCost == None:
			middle = top
			middleCost = topCost
		middle = math.ceil(middle)
		
		# Calculate final value
		self.obj, self.sol = self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, peak=middle, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
		
		return self.obj, self.sol
		
	def calculateElectricityBill(self, sol, previousPeak):
		# Calculate electricity cost
		peakBrown = 0.0 # Watts
		energyCost = 0.0 # Dollars
		netMeterMoney = 0.0 # Dollars
		peakCost = 0.0 # Dollars
		# Energy cost
		for t in range(0, self.options.maxTime):
			if self.brownPrice != None:
				# Peak and energy
				brown = 0
				if "LoadBrown["+str(t)+"]" in sol:
					brown += sol["LoadBrown["+str(t)+"]"]
				if "BattBrown["+str(t)+"]" in sol:
					brown += sol["BattBrown["+str(t)+"]"]
				if brown > peakBrown:
					peakBrown = brown
				energyCost += brown*(self.options.slotLength/3600.0)*sol["BrownPrice["+str(t)+"]"]/1000.0
				# Net metering
				if self.greenAvail != None and self.options.netMeter != None:
					netMeterMoney += sol["NetGreen["+str(t)+"]"]*self.options.netMeter*(self.options.slotLength/3600.0)*sol["BrownPrice["+str(t)+"]"]/1000.0
		# Peak cost
		if peakBrown > previousPeak and self.options.peakCost!=None:
			peakCost = ((peakBrown-previousPeak)/1000.0)*self.options.peakCost
			peakCost = peakCost/(30*24) * self.options.maxTime # 30 days distributed in the window
		return energyCost + peakCost - netMeterMoney
	"""
	
	
	def solvePeak(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False, previousPeak=0.0, stateChargeBattery=False, stateNetMeter=False):
		return self.solve(jobs=jobs, load=load, greenAvail=greenAvail, brownPrice=brownPrice, initial=initial, steps=steps, previousPeak=previousPeak, stateChargeBattery=stateChargeBattery, stateNetMeter=stateNetMeter)
	
	# Gurobi solver
	#def solve(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False, peak=None, stateChargeBattery=False, stateNetMeter=False):
	def solve(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False, previousPeak=0.0, stateChargeBattery=False, stateNetMeter=False):
		self.obj = None
		self.sol = None
			
		# Init
		self.jobs = jobs
		self.load = load
		
		self.greenAvail = greenAvail
		self.brownPrice = brownPrice
		
		# Model
		m = Model("parasol")
		m.setParam("OutputFlag", 0)
		if self.options.timeLimit > 0:
			m.setParam("TimeLimit", self.options.timeLimit)

		# Variables
		# var Load {t in TIME}  >= 0;
		Load = {}
		for t in range(0, self.options.maxTime):
			Load[t] = m.addVar(lb=self.options.minSize, ub=self.options.maxSize, name="Load["+str(t)+"]")
		if self.greenAvail != None:
			# var LoadGreen {t in TIME}  >= 0;
			LoadGreen = {}
			for t in range(0, self.options.maxTime):
				LoadGreen[t] = m.addVar(ub=self.options.maxSize, name="LoadGreen["+str(t)+"]")
		if self.brownPrice != None:
			# var LoadBrown {t in TIME}  >= 0;
			LoadBrown = {}
			for t in range(0, self.options.maxTime):
				LoadBrown[t] = m.addVar(ub=self.options.maxSize, name="LoadBrown["+str(t)+"]")
		# Battery
		if self.options.batCap > 0:
			if self.greenAvail != None:
				# var BattGreen  {t in XTIME} >= 0;
				BattGreen = {}
				for t in range(-1, self.options.maxTime):
					BattGreen[t] = m.addVar(name="BattGreen["+str(t)+"]")
			if self.brownPrice != None:
				# var BattBrown  {t in XTIME} >= 0;
				BattBrown = {}
				for t in range(-1, self.options.maxTime):
					BattBrown[t] = m.addVar(name="BattBrown["+str(t)+"]")
			# var LoadBatt   {t in XTIME} >= 0;
			LoadBatt = {}
			for t in range(-1, self.options.maxTime):
				LoadBatt[t] = m.addVar(name="LoadBatt["+str(t)+"]")
			# var CapBattery {t in XTIME} >= 0;
			CapBattery = {}
			for t in range(-1, self.options.maxTime):
				CapBattery[t] = m.addVar(name="CapBattery["+str(t)+"]")
		
		# Peak cost
		if self.options.peakCost != None and self.brownPrice != None:
			PeakBrown = m.addVar(lb=0.0, ub=self.options.maxSize+self.options.batChargeRate, name="PeakBrown")
			
		# Net metering
		if self.greenAvail != None and self.brownPrice != None:
			# var NetGreen  {t in TIME} >= 0;
			NetGreen = {}
			for t in range(0, self.options.maxTime):
				NetGreen[t] = m.addVar(name="NetGreen["+str(t)+"]")
		# Jobs
		if self.jobs != None:
			maxLength = 0
			for job in self.jobs:
				if job.length > maxLength:
					maxLength = job.length
			StartJob = {}
			LoadJob = {}
			LoadJobIni = {}
			LoadJobFin = {}
			for j in self.jobs:
				#StartJob[j.id] = m.addVar(ub=self.options.maxTime+1, vtype=GRB.INTEGER, obj=0.0, name="StartJob["+str(j.id)+"]")
				StartJob[j.id] = m.addVar(ub=self.options.maxTime+1, vtype=GRB.INTEGER, name="StartJob["+str(j.id)+"]")
				for t in range(0, self.options.maxTime+1+(maxLength/self.options.slotLength)):
					LoadJob[j.id, t] = m.addVar(vtype=GRB.BINARY, name="LoadJob["+str(j.id)+","+str(t)+"]")
					LoadJobIni[j.id, t] = m.addVar(vtype=GRB.BINARY, name="LoadJobIni["+str(j.id)+","+str(t)+"]")
					LoadJobFin[j.id, t] = m.addVar(vtype=GRB.BINARY, name="LoadJobFin["+str(j.id)+","+str(t)+"]")

		# Auxiliar variables for MILP constraints
		auxvar1 = {}
		auxbin1 = {}
		for t in range(0, self.options.maxTime):
			auxvar1[t] = m.addVar(name="auxvar1["+str(t)+"]")
			auxbin1[t] = m.addVar(vtype=GRB.BINARY, name="auxbin1["+str(t)+"]")
		auxvar2 = {}
		auxbin2 = {}
		for t in range(0, self.options.maxTime):
			auxvar2[t] = m.addVar(name="auxvar2["+str(t)+"]")
			auxbin2[t] = m.addVar(vtype=GRB.BINARY, name="auxbin2["+str(t)+"]")
		auxvar3 = {}
		auxbin3 = {}
		for t in range(0, self.options.maxTime):
			auxvar3[t] = m.addVar(name="auxvar3["+str(t)+"]")
			auxbin3[t] = m.addVar(vtype=GRB.BINARY, name="auxbin3["+str(t)+"]")
		
		# Finish variables declaration
		m.update()
		
		# Starting solution
		if initial != None and self.jobs != None:
			#for j in jobs:
				#StartJob[j.id].start = self.options.maxTime
			for j in initial:
				StartJob[j].start = initial[j]
			m.update()
		
		# Parameters
		# Green availability
		if self.greenAvail != None:
			GreenAvail = {}
			jG = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(self.greenAvail)>jG+1 and self.greenAvail[jG+1].t <= ts: jG += 1
				GreenAvail[t] = self.greenAvail[jG].v
		# Brown prices
		if self.brownPrice != None:
			BrownPrice = {}
			jB = 0
			for t in range(0, self.options.maxTime):
				# Look for current values
				ts = t*self.options.slotLength
				while len(self.brownPrice)>jB+1 and self.brownPrice[jB+1].t <= ts: jB += 1
				BrownPrice[t] = self.brownPrice[jB].v
			
		# Workload
		if self.load != None:
			Workload = {}
			jW = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(self.load)>jW+1 and self.load[jW+1].t <= ts: jW += 1
				Workload[t] = self.load[jW].v
		
		# Integrate new variables
		m.update()
		
		# Optimization function
		optFunction = 0
		if self.options.optCost > 0 and self.brownPrice != None:
			#optFunction += -self.options.optCost * quicksum(aux*BrownPrice[t] for t in range(0, self.options.maxTime))
			for t in range(0, self.options.maxTime):
				aux = LoadBrown[t]
				if self.options.batCap > 0:
					aux += BattBrown[t]
				if self.greenAvail != None and self.options.netMeter!=None:
					aux += -self.options.netMeter*NetGreen[t]
				optFunction += -self.options.optCost * aux * BrownPrice[t]/1000.0
			# Add peak power cost in a linear way
			if self.options.peakCost != None:
				optFunction += -self.options.optCost * (PeakBrown-previousPeak)/1000.0 * self.options.peakCost
		if self.options.optBat > 0 and self.options.batCap > 0:
			for t in range(0, self.options.maxTime):
				aux = 0
				if self.greenAvail != None:
					aux += BattGreen[t]
				if self.brownPrice != None:
					aux += BattBrown[t]
				optFunction += (-1.0*self.options.optBat/self.options.maxTime) * aux
			#optFunction += (-1.0*self.options.optBat/self.options.maxTime) * quicksum(aux for t in range(0, self.options.maxTime))
		if self.options.optBatCap > 0 and self.options.batCap > 0:
			optFunction += -float(self.options.optBatCap)/self.options.maxTime * quicksum(CapBattery[t] for t in range(0, self.options.maxTime))
		if self.options.optBatCapEnd > 0 and self.options.batCap > 0:
			optFunction += -self.options.optBatCapEnd * CapBattery[self.options.maxTime-1]
		if self.options.optPrior > 0 and self.jobs != None:
			for j in self.jobs:
				for t in range(0, self.options.maxTime):
					optFunction += self.options.optPrior * (j.priority+1) * LoadJob[j,t]/int(math.ceil(job.length/(1.0*self.options.slotLength)))
		if self.options.optSlowdown > 0:
			optFunction += self.options.optSlowdown * quicksum((1-StartJob[j.id]/self.options.maxTime) for j in self.jobs)
		if self.options.optLoad > 0:
			optFunction += self.options.optLoad * quicksum(Load[t] for t in range(0, self.options.maxTime))
		if self.options.optPerf > 0:
			# TODO we add an extra weight to avoid delay
			# Load_down - Load_up
			optFunction += quicksum((self.options.maxTime - t)*0.1 * (Load[t]-Workload[t]) for t in range(0, self.options.maxTime))

		
		# Avoid net metering and battery changes
		if self.greenAvail != None:
			if stateChargeBattery:
				optFunction += 0.001*(BattGreen[0]+LoadGreen[0])
			elif stateNetMeter:
				if  self.brownPrice != None:
					optFunction += 0.001*(NetGreen[0]+LoadGreen[0])

		# Dump objective function
		m.setObjective(optFunction, GRB.MAXIMIZE)
		
		m.update()
		
		# Constraints
		# Constraints for load
		if self.jobs != None:
			# Always grows
			# s.t. LoadJobIniInc {j in JOBS, t in TIMEALL} :  LoadJobIni[j,t] <= LoadJobIni[j,t+1];
			# s.t. LoadJobFinInc {j in JOBS, t in TIMEALL} :  LoadJobFin[j,t] <= LoadJobFin[j,t+1];
			# Aggregate load
			# s.t. LoadGen       {j in JOBS, t in TIMEXALL} : LoadJob[j,t] = LoadJobIni[j,t] -  LoadJobFin[j,t];
			# Barrier
			# s.t. LoadBarrier   {j in JOBS} : LoadJob[j,T] = 0;
			# Job start
			# s.t. JobStart      {j in JOBS} : sum{t in TIME} LoadJobIni[j,t] = T - StartJob[j];
			# Job length
			# s.t. MaxLength     {j in JOBS} : sum{t in TIMEXALL} LoadJob[j,t] = LengthJobs[j];
			for j in self.jobs:
				for t in range(0, self.options.maxTime+(maxLength/self.options.slotLength)):
					m.addConstr(LoadJobIni[j.id, t] <= LoadJobIni[j.id, t+1], "LoadJobIniInc["+str(j.id)+","+str(t)+"]")
					m.addConstr(LoadJobFin[j.id, t] <= LoadJobFin[j.id, t+1], "LoadJobFinInc["+str(j.id)+","+str(t)+"]")
				for t in range(0, self.options.maxTime+1+(maxLength/self.options.slotLength)):
					m.addConstr(LoadJob[j.id, t] == LoadJobIni[j.id, t] -  LoadJobFin[j.id, t], "LoadGen["+str(j.id)+","+str(t)+"]")
				# Barrier
				m.addConstr(LoadJob[j.id, self.options.maxTime] == 0, "LoadBarrier["+str(j.id)+"]")
				# Job start
				m.addConstr(quicksum(LoadJobIni[j.id,t] for t in range(0, self.options.maxTime)) == (self.options.maxTime - StartJob[j.id]), "JobStart["+str(j.id)+"]")
				# Job length
				m.addConstr(quicksum(LoadJob[j.id,t] for t in range(0, self.options.maxTime+1+(maxLength/self.options.slotLength))) == int(math.ceil(job.length/(1.0*self.options.slotLength))), "MaxLength["+str(j.id)+"]")
			
			# The load is composed by the internal loads
			# s.t. LoadPower {t in TIME} :     sum{j in JOBS} LoadJob[j,t] * PowerJobs[j] = Load[t];
			for t in range(0, self.options.maxTime):
				m.addConstr(quicksum((LoadJob[j.id,t] * j.power) for j in self.jobs) == Load[t], "LoadPower["+str(t)+"]")
		
		# Load constraints
		if self.load != None:
			if not self.options.loadDelay:
				for t in range(0, self.options.maxTime):
					m.addConstr(Load[t] >= Workload[t], "WorkloadMin["+str(t)+"]")
					#m.addConstr(Load[t] == Workload[t], "WorkloadMin["+str(t)+"]")
			else:
				# Summation of powers have to be the power required by the workload
				# Checking previous load is actually executed
				if self.options.optPerf == 0:
					sumLoad = quicksum(Load[t] for t in range(0, self.options.maxTime))
					sumWorkload = self.options.prevLoad + quicksum(Workload[t] for t in range(0, self.options.maxTime))
					m.addConstr(sumLoad >= sumWorkload, "WorkloadMin")
				else:
					# We don't need to run everything if we try to minimize the difference
					pass
				
				# Guarrantee that the load is already there
				#for t in range(0, self.options.maxTime):
				for t in range(1, self.options.maxTime):
					sumLoadT = quicksum(Load[t] for t in range(0, t))
					sumWorkloadT = self.options.prevLoad + quicksum(Workload[t] for t in range(0, t))
					m.addConstr(sumLoadT <= sumWorkloadT, "WorkloadMin["+str(t)+"]") # +1 to have some margin
		
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
			m.addConstr(Load[t] == aux,  "LoadProvide["+str(t)+"]")
			#m.addConstr(Load[t] <= self.options.maxSize, "MaxSize["+str(t)+"]")
		
		# Maximum green availability
		# s.t. MaxGreen {t in TIME} :      LoadGreen[t] + BattGreen[t] + NetGreen[t] <= GreenAvail[t]"
		for t in range(0, self.options.maxTime):
			if self.greenAvail != None:
				aux = 0
				if self.options.batCap > 0:
					aux += BattGreen[t]
				if self.greenAvail != None and self.brownPrice != None:
					aux += NetGreen[t]
				m.addConstr(LoadGreen[t] + aux <= GreenAvail[t], "MaxGreen["+str(t)+"]")
		
		# Battery
		if self.options.batCap > 0:
			# s.t. IniBattery :                CapBattery[-1] = 0;
			# s.t. IniBatteryL :               LoadBatt[-1]   = 0;
			# s.t. MaxBattery {t in TIME} :    CapBattery[t] <= self.options.batCap);
			# s.t. CapBatteryT {t in TIME} :   LoadBatt[t] <= CapBattery[t];
			m.addConstr(CapBattery[-1] == self.options.batIniCap, "IniBattery")
			m.addConstr(LoadBatt[-1] == 0, "IniBatteryL")
			for t in range(0, self.options.maxTime):
				m.addConstr(CapBattery[t] <= self.options.batCap, "MaxBattery["+str(t)+"]")
				m.addConstr(LoadBatt[t] <= CapBattery[t], "CapBatteryT["+str(t)+"]")
			if self.greenAvail != None:
				# s.t. IniBatteryG :               BattGreen[-1]  = 0;
				m.addConstr(BattGreen[-1] == 0, "IniBatteryG")
			if self.brownPrice != None:
				# s.t. IniBatteryB :               BattBrown[-1]  = 0;
				m.addConstr(BattBrown[-1] == 0, "IniBatteryB")
			# s.t. ChargeBattery {t in TIME} : CapBattery[t] = CapBattery[t-1] + "+str(batFactor)+" * (BattGreen[t-1] + BattBrown[t-1]) - LoadBatt[t-1];
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
			# Maximum depth of discharge to enlarge battery
			if self.options.batDischargeMax != None:
				for t in range(0, self.options.maxTime):
					m.addConstr(CapBattery[t] >= self.options.batCap*(1-self.options.batDischargeMax), "Batt["+str(t)+"]")
			# System protection: usually 15+10 = 25%
			if self.options.batDischargeProtection != None:
				for t in range(0, self.options.maxTime):
					m.addConstr(CapBattery[t] >= self.options.batCap*self.options.batDischargeProtection, "BattProtection["+str(t)+"]")
		
		# Peak cost constraints
		"""
		if peak != None:
			if self.brownPrice != None:
				for t in range(0, self.options.maxTime):
					aux = LoadBrown[t]
					if self.options.batCap > 0:
						aux += BattBrown[t]
					m.addConstr(aux <= peak, "Peak["+str(t)+"]")
		"""
		if self.options.peakCost != None and self.brownPrice != None:
			for t in range(0, self.options.maxTime):
				aux = LoadBrown[t]
				if self.options.batCap > 0:
					aux += BattBrown[t]
				m.addConstr(aux <= PeakBrown, "Peak["+str(t)+"]")
			m.addConstr(previousPeak <= PeakBrown)
				
		# Parasol constraints
		# Constraints
		for t in range(0, self.options.maxTime):
			# We can only do one thing at a time
			# X > 0 => Y = 0
			# X >= 0
			# Y >= 0
			# X <= bin * inf
			# bin <= X * inf
			# Y <= 1-bin * inf
			# aux - Y >= 0
			# Y - aux >= bin * -inf 
			
			LARGE = 99999999
			# LoadBrown > 0  => NetGreen = 0
			if self.brownPrice != None and self.greenAvail != None:
				m.addConstr(LoadBrown[t] <= auxbin1[t] * LARGE, "1auxconstraint1["+str(t)+"]")
				m.addConstr(auxbin1[t] <= LoadBrown[t] * LARGE, "1auxconstraint2["+str(t)+"]")
				m.addConstr(NetGreen[t] <= (1-auxbin1[t]) * LARGE, "1auxconstraint3["+str(t)+"]")
				m.addConstr(auxvar1[t] - NetGreen[t] >= 0, "1auxconstraint4["+str(t)+"]")
				m.addConstr(NetGreen[t] - auxvar1[t] >= auxbin1[t] * -LARGE, "1auxconstraint5["+str(t)+"]")
			# LoadBatt > 0  => NetGreen + BattBrown + BattGreen = 0 
			if self.options.batCap > 0 and self.greenAvail != None:
				auxtozero = BattGreen[t]
				if self.brownPrice != None:
					auxtozero += NetGreen[t] + BattBrown[t]
				m.addConstr(LoadBatt[t] <= auxbin2[t] * LARGE, "2auxconstraint1["+str(t)+"]")
				m.addConstr(auxbin2[t] <= LoadBatt[t] * LARGE, "2auxconstraint2["+str(t)+"]")
				m.addConstr(auxtozero <= (1-auxbin2[t]) * LARGE, "2auxconstraint3["+str(t)+"]")
				m.addConstr(auxvar2[t] - auxtozero >= 0, "2auxconstraint4["+str(t)+"]")
				m.addConstr(auxtozero - auxvar2[t] >= auxbin2[t] * -LARGE, "2auxconstraint5["+str(t)+"]")
		# Solve
		m.update()
		
		#m.write('test.lp')
		
		m.optimize()
		
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
				if self.jobs != None:
					for j in self.jobs:
						self.sol["StartJob["+j.id+"]"] = StartJob[j.id].x
						for t in range(0, self.options.maxTime):
							self.sol["LoadJob["+j.id+","+str(t)+"]"] = LoadJob[j.id, t].x
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
						self.sol["BrownPrice["+str(t)+"]"] = BrownPrice[t]
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
						
					# Workload
					if self.load != None:
						self.sol["Workload["+str(t)+"]"] = Workload[t]
				if self.options.peakCost!=None and self.brownPrice != None:
					self.sol["PeakBrown"] = PeakBrown.x
				else:
					self.sol["PeakBrown"] = 0.0
					for t in range(0, self.options.maxTime):
						self.sol["PeakBrown"] += self.sol["LoadBrown["+str(t)+"]"] + self.sol["BattBrown["+str(t)+"]"]
		except Exception, e:
			print 'Error reading solution. State=%d. Message: %s.' % (m.status, str(e))
		
		# Return result
		if steps:
			return m.status, self.obj, self.sol
		else:
			return self.obj, self.sol

	def printJobs(self):
		if self.jobs != None:
			print "Jobs:"
			for job in self.jobs:
				executed = True
				out = job.id + "\t" + str(job.length/self.options.slotLength)+ "\t"
				
				if "StartJob["+job.id+"]" in solver.sol:
					out += str(int(solver.sol["StartJob["+job.id+"]"])) + "\t"
					if solver.sol["StartJob["+job.id+"]"] >= solver.options.maxTime:
						executed = False
				for t in range(0, solver.options.maxTime):
					if "LoadJob["+job.id+","+str(t)+"]" in solver.sol:
						out += str(int(solver.sol["LoadJob["+job.id+","+str(t)+"]"]))
				if not executed:
					out += "|"
				#for t in range(maxTime, maxTime+maxLength+1):
					#if "LoadJob["+job.id+","+str(t)+"]" in solver.sol:
						#out += str(solver.sol["LoadJob["+job.id+","+str(t)+"]"])
				print out
	
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
				
				# Jobs
				if jobs != None:
					for job in jobs:
						executed = True
						out = job.id + "\t" + str(job.length/self.options.slotLength)+ "\t" + str(job.power)+ "\t"
						if "StartJob["+job.id+"]" in self.sol:
							out += str(int(self.sol["StartJob["+job.id+"]"])) + "\t"
							if self.sol["StartJob["+job.id+"]"] >= self.options.maxTime:
								executed = False
						for t in range(0, self.options.maxTime):
							if "LoadJob["+job.id+","+str(t)+"]" in self.sol:
								out += str(int(self.sol["LoadJob["+job.id+","+str(t)+"]"]))
						if not executed:
							out += "|"
						report.write(out+"\n")
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
	jobs = None
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
	
	# Solve model
	solver = ParasolModel()
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
	
	#solver.options.batDischargeMax = 1.0
	tnow = datetime.now()
	#obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, load=workload)
	obj, sol = solver.solvePeak(greenAvail=greenAvail, brownPrice=brownPrice, load=workload, previousPeak=solver.options.previousPeak, stateChargeBattery=False)
	#obj, sol = solver.solve(greenAvail=greenAvail, brownPrice=brownPrice, load=workload, stateChargeBattery=False)
	print datetime.now()-tnow
	
	# Solution
	print "Time: %s" % (str(datetime.now()-start))
	if solver.obj == None:
		print "Opti: No solution"
	else:
		print "Opti: %.3f" % (solver.obj)

		# Print jobs
		solver.printJobs()
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
