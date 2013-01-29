#!/usr/bin/env python

import os
import sys

from parasolsolvercommons import *

from datetime import datetime

# Gurobi
# export LD_LIBRARY_PATH="/home/goiri/hadoop-parasol/solver/gurobi500/linux64/lib"
SIMULATOR_PATH = "/home/goiri/hadoop-parasol/solver/gurobi500/linux64"
os.environ["LD_LIBRARY_PATH"] = SIMULATOR_PATH+"/lib/"
#os.environ["GRB_LICENSE_FILE"] = SIMULATOR_PATH+"/gurobi.lic"
os.environ["GRB_LICENSE_FILE"] = SIMULATOR_PATH+"/gurobi-urca.lic"
os.environ["GRB_LICENSE_FILE"] = SIMULATOR_PATH+"/gurobi-sol000.lic"
sys.path.append(SIMULATOR_PATH+"/lib")
sys.path.append(SIMULATOR_PATH+"/lib/python2.7")

try:
	from gurobipy import *
except ImportError, e:
	print 'export LD_LIBRARY_PATH='+SIMULATOR_PATH+'/lib'

class ParasolModel:
	def __init__(self):
		self.options = SolverOptions()
		self.obj = None
		self.sol = None
		self.jobs = None
		self.load = None
	
	# Gurobi solver
	def solveOriginal(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False):
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
		if greenAvail != None:
			# var LoadGreen {t in TIME}  >= 0;
			LoadGreen = {}
			for t in range(0, self.options.maxTime):
				LoadGreen[t] = m.addVar(ub=self.options.maxSize, name="LoadGreen["+str(t)+"]")
		if brownPrice != None:
			# var LoadBrown {t in TIME}  >= 0;
			LoadBrown = {}
			for t in range(0, self.options.maxTime):
				LoadBrown[t] = m.addVar(ub=self.options.maxSize, name="LoadBrown["+str(t)+"]")
		# Battery
		if self.options.batCap > 0:
			if greenAvail != None:
				# var BattGreen  {t in XTIME} >= 0;
				BattGreen = {}
				for t in range(-1, self.options.maxTime):
					BattGreen[t] = m.addVar(name="BattGreen["+str(t)+"]")
			if brownPrice != None:
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
		# Net metering
		if self.options.netMeter > 0:
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
		if greenAvail != None:
			GreenAvail = {}
			jG = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(greenAvail)>jG+1 and greenAvail[jG+1].t <= ts: jG += 1
				GreenAvail[t] = greenAvail[jG].v
		# Brown prices
		if brownPrice != None:
			BrownPrice = {}
			jB = 0
			for t in range(0, self.options.maxTime):
				# Look for current values
				ts = t*self.options.slotLength
				while len(brownPrice)>jB+1 and brownPrice[jB+1].t <= ts: jB += 1
				BrownPrice[t] = brownPrice[jB].v
		
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
		if self.options.optCost > 0 and brownPrice != None:
			for t in range(0, self.options.maxTime):
				aux = LoadBrown[t]
				if self.options.batCap > 0:
					aux += BattBrown[t]
				if self.options.netMeter > 0:
					aux += -self.options.netMeter*NetGreen[t]
				optFunction += -self.options.optCost * aux * BrownPrice[t]
			#optFunction += -self.options.optCost * quicksum(aux*BrownPrice[t] for t in range(0, self.options.maxTime))
		if self.options.optBat > 0 and self.options.batCap > 0:
			for t in range(0, self.options.maxTime):
				aux = 0
				if greenAvail != None:
					aux += BattGreen[t]
				if brownPrice != None:
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
			else:
				# Summation of powers have to be the power required by the workload
				# Checking previous load is actually executed
				sumLoad = quicksum(Load[t] for t in range(0, self.options.maxTime))
				sumWorkload = self.options.prevLoad + quicksum(Workload[t] for t in range(0, self.options.maxTime))
				m.addConstr(sumLoad >= sumWorkload, "WorkloadMin")
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
			if greenAvail != None:
				aux += LoadGreen[t]
			if brownPrice != None:
				aux += LoadBrown[t]
			if self.options.batCap > 0:
				aux += LoadBatt[t]
			m.addConstr(Load[t] == aux,  "LoadProvide["+str(t)+"]")
			#m.addConstr(Load[t] <= self.options.maxSize, "MaxSize["+str(t)+"]")
		
		# Maximum green availability
		# s.t. MaxGreen {t in TIME} :      LoadGreen[t] + BattGreen[t] + NetGreen[t] <= GreenAvail[t]"
		for t in range(0, self.options.maxTime):
			if greenAvail != None:
				aux = 0
				if self.options.batCap > 0:
					aux += BattGreen[t]
				if self.options.netMeter > 0:
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
			if greenAvail != None:
				# s.t. IniBatteryG :               BattGreen[-1]  = 0;
				m.addConstr(BattGreen[-1] == 0, "IniBatteryG")
			if brownPrice != None:
				# s.t. IniBatteryB :               BattBrown[-1]  = 0;
				m.addConstr(BattBrown[-1] == 0, "IniBatteryB")
			# s.t. ChargeBattery {t in TIME} : CapBattery[t] = CapBattery[t-1] + "+str(batFactor)+" * (BattGreen[t-1] + BattBrown[t-1]) - LoadBatt[t-1];
			for t in range(0, self.options.maxTime):
				aux = 0
				if brownPrice != None:
					aux += BattBrown[t-1]
				if greenAvail != None:
					aux += BattGreen[t-1]
				m.addConstr(CapBattery[t] == CapBattery[t-1] + self.options.batEfficiency*aux - LoadBatt[t-1], "ChargeBattery["+str(t)+"]")
			# Maximum battery charge rate (kW)
			if self.options.batChargeRate > 0 and (greenAvail != None or brownPrice != None):
				# s.t. BattRate {t in TIME} :  <= self.options.batChargeRate
				for t in range(0, self.options.maxTime):
					aux = 0
					if greenAvail != None:
						aux += BattGreen[t]
					if brownPrice != None:
						aux += BattBrown[t]
					m.addConstr(aux <= self.options.batChargeRate, "BattRate["+str(t)+"]")
			# Maximum depth of discharge
			for t in range(0, self.options.maxTime):
				m.addConstr(CapBattery[t] >= self.options.batCap*(1-self.options.batDischargeMax), "Batt["+str(t)+"]")
		
		# Solve
		m.update()
		
		m.optimize()
		
		if m.status == GRB.status.LOADED:
			print "Loaded"
		elif m.status == GRB.status.INFEASIBLE:
			print "Infeasible"
		elif m.status == GRB.status.OPTIMAL:
			if self.options.debug > 0:
				print "Optimal"
		elif m.status == GRB.status.INF_OR_UNBD:
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
		#if m.status == GRB.status.OPTIMAL or m.status == GRB.status.TIME_LIMIT:
		if m.status != GRB.status.INF_OR_UNBD:
			self.obj = m.objVal
			self.sol = {}
			if self.jobs != None:
				for j in self.jobs:
					self.sol["StartJob["+j.id+"]"] = StartJob[j.id].x
					for t in range(0, self.options.maxTime):
						self.sol["LoadJob["+j.id+","+str(t)+"]"] = LoadJob[j.id, t].x
			for t in range(0, self.options.maxTime):
				if greenAvail != None:
					self.sol["LoadGreen["+str(t)+"]"] = LoadGreen[t].x
				if brownPrice != None:
					self.sol["LoadBrown["+str(t)+"]"] = LoadBrown[t].x
				if self.options.batCap > 0:
					self.sol["LoadBatt["+str(t)+"]"] = LoadBatt[t].x
					if greenAvail != None:
						self.sol["BattGreen["+str(t)+"]"] = BattGreen[t].x
					if brownPrice != None:
						self.sol["BattBrown["+str(t)+"]"] = BattBrown[t].x
					self.sol["CapBattery["+str(t)+"]"] = CapBattery[t].x
				if self.options.netMeter > 0:
					self.sol["NetGreen["+str(t)+"]"] = NetGreen[t].x

		if steps:
			return m.status, self.obj, self.sol
		else:
			return self.obj, self.sol

	
	# Gurobi solver
	# TODO new
	def solve(self, jobs=None, load=None, greenAvail=None, brownPrice=None, initial=None, steps=False):
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
		Grid = {}
		for t in range(0, self.options.maxTime):
			Grid[t] = m.addVar(lb=-10000, ub=10000, name="Grid["+str(t)+"]")
		
		# Battery
		if self.options.batCap > 0:
			Battery = {}
			for t in range(-1, self.options.maxTime):
				Battery[t] = m.addVar(lb=-10000, ub=10000, name="Battery["+str(t)+"]")

				
		# Parasol TODO
		PanelsConnection = {}
		#BatteryWire = {}
		#GridWire = {}
		for t in range(0, self.options.maxTime):
			PanelsConnection[t] = m.addVar(lb=-10000, ub=10000, name="PanelsConnection["+str(t)+"]")
			#BatteryWire[t] = m.addVar(lb=-GRB.INFINITY, ub=GRB.INFINITY, name="BatteryWire["+str(t)+"]")
			#GridWire[t] = m.addVar(lb=-GRB.INFINITY, ub=GRB.INFINITY, name="GridWire["+str(t)+"]")
		
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
		if greenAvail != None:
			GreenAvail = {}
			jG = 0
			for t in range(0, self.options.maxTime):
				ts = t*self.options.slotLength
				while len(greenAvail)>jG+1 and greenAvail[jG+1].t <= ts: jG += 1
				GreenAvail[t] = greenAvail[jG].v
		# Brown prices
		if brownPrice != None:
			BrownPrice = {}
			jB = 0
			for t in range(0, self.options.maxTime):
				# Look for current values
				ts = t*self.options.slotLength
				while len(brownPrice)>jB+1 and brownPrice[jB+1].t <= ts: jB += 1
				BrownPrice[t] = brownPrice[jB].v
		
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
		if self.options.optCost > 0 and brownPrice != None:
			for t in range(0, self.options.maxTime):
				#aux = LoadBrown[t]
				#if self.options.batCap > 0:
					#aux += BattBrown[t]
				#if self.options.netMeter > 0:
					#aux += -self.options.netMeter*NetGreen[t]
				#optFunction += -self.options.optCost * aux * BrownPrice[t]
				optFunction += -self.options.optCost * BrownPrice[t] * Grid[t]
			#optFunction += -self.options.optCost * quicksum(aux*BrownPrice[t] for t in range(0, self.options.maxTime))
		"""
		if self.options.optBat > 0 and self.options.batCap > 0:
			for t in range(0, self.options.maxTime):
				aux = 0
				if greenAvail != None:
					aux += BattGreen[t]
				if brownPrice != None:
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
		"""
		# Dump objective function
		m.setObjective(optFunction, GRB.MAXIMIZE)
		
		m.update()
		
		# Constraints
		for t in range(0, self.options.maxTime):
			m.addConstr(Load[t] == GreenAvail[t] + PanelsConnection[t], "LoadPanel["+str(t)+"]")
			m.addConstr(PanelsConnection[t] == Battery[t] + Grid[t], "BatteryPanel["+str(t)+"]")
		
		
		for t in range(0, self.options.maxTime):
			#m.addConstr(Load[t] >= Workload[t], "WorkloadMin["+str(t)+"]")
			m.addConstr(Load[t] == Workload[t], "WorkloadMin["+str(t)+"]")
		
		# Solve
		m.update()
		
		m.write('test.lp')
		
		m.optimize()
		
		if m.status == GRB.status.LOADED:
			print "Loaded"
		elif m.status == GRB.status.INFEASIBLE:
			print "Infeasible"
		elif m.status == GRB.status.OPTIMAL:
			if self.options.debug > 0:
				print "Optimal"
		elif m.status == GRB.status.INF_OR_UNBD:
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
		#if m.status == GRB.status.OPTIMAL or m.status == GRB.status.TIME_LIMIT:
		if m.status != GRB.status.INF_OR_UNBD:
			self.obj = m.objVal
			self.sol = {}
			if self.jobs != None:
				for j in self.jobs:
					self.sol["StartJob["+j.id+"]"] = StartJob[j.id].x
					for t in range(0, self.options.maxTime):
						self.sol["LoadJob["+j.id+","+str(t)+"]"] = LoadJob[j.id, t].x
			for t in range(0, self.options.maxTime):
				"""
				if greenAvail != None:
					self.sol["LoadGreen["+str(t)+"]"] = LoadGreen[t].x
				if brownPrice != None:
					self.sol["LoadBrown["+str(t)+"]"] = LoadBrown[t].x
				if self.options.batCap > 0:
					self.sol["LoadBatt["+str(t)+"]"] = LoadBatt[t].x
					if greenAvail != None:
						self.sol["BattGreen["+str(t)+"]"] = BattGreen[t].x
					if brownPrice != None:
						self.sol["BattBrown["+str(t)+"]"] = BattBrown[t].x
					self.sol["CapBattery["+str(t)+"]"] = CapBattery[t].x
				if self.options.netMeter > 0:
					self.sol["NetGreen["+str(t)+"]"] = NetGreen[t].x
				"""
					
				# TODO
				self.sol["PanelsConnection["+str(t)+"]"] = PanelsConnection[t].x
				self.sol["Grid["+str(t)+"]"] = Grid[t].x
				self.sol["Battery["+str(t)+"]"] = Battery[t].x
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
				out.write("#t\tuseGree\tuseBrow\tuseChea\tuseExpe\tuseBatt\tcapBatt\tavGreen\tcurLoad\tpriceBr\tnetMet\tqos\n")
				out.write("0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")
			
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
					prevLine = str(useGreen)+"\t"+str(useBrown)+"\t"+str(useBrownCheap)+"\t"+str(useBrownExpen)+"\t"+str(useBatte)+"\t"+str(capBatte)+"\t"+str(curGreen)+"\t"+str(curLoad)+"\t"+str(priceBrown)+"\t"+str(netMeter)+"\t"+str(fraction)
					out.write(str(ts/(1.0*self.options.slotLength))+"\t"+prevLine+"\n")

			if self.options.output != None:
				out.write(str(ts/(1.0*self.options.slotLength))+"\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n")
			
			# Result summary
			print "Summary:"
			print "\tBrown: %s $%.2f" % (toEnergyString(totalUseBrown*self.options.slotLength), totalUseBrownCost)
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
				prevLine = str(useGreen)+"\t"+str(useBrown)+"\t"+str(useBrownCheap)+"\t"+str(useBrownExpen)+"\t"+str(useBatte)+"\t"+str(capBatte)+"\t"+str(curGreen)+"\t"+str(curLoad)+"\t"+str(priceBrown)+"\t"+str(netMeter)+"\t"+str(fraction)
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
	solver.options.loadDelay = False
	solver.options.minSize = 400 # Covering subset
	solver.options.batCap = 32000 # 32 kWh
	solver.options.batIniCap = 1.0 * solver.options.batCap # 32 kWh
	
	
	solver.options.prevLoad = 50.0
	
	#solver.options.batDischargeMax = 1.0
	obj, sol = solver.solveOriginal(greenAvail=greenAvail, brownPrice=brownPrice, load=workload)
	
	# Solution
	if solver.obj == None:
		print "Opti: No solution"
	else:
		print "Opti: %.3f" % (solver.obj)
	print "Time: %s" % (str(datetime.now()-start))

	# Print jobs
	solver.printJobs()
	solver.printResults()

	print
	print "Current status:"
	print "Load:", solver.sol["LoadBatt[0]"]+solver.sol["LoadBrown[0]"]+solver.sol["LoadGreen[0]"], "kW"
	print "Grid:", solver.sol["LoadBrown[0]"] + solver.sol["BattBrown[0]"], "kW"
	print "Battery charge:", solver.sol["BattBrown[0]"]+solver.sol["BattGreen[0]"], "kW"
	print "Battery discharge:", solver.sol["LoadBatt[0]"], "kW"
	print "Net metering", solver.sol["NetGreen[0]"], "kW"
	
	if "PanelsConnection[0]" in solver.sol:
		print
		print "PanelsConnection", solver.sol["PanelsConnection[0]"], "kW"
		print "GridWire        ", solver.sol["GridWire[0]"], "kW"
		print "BatteryWire     ", solver.sol["BatteryWire[0]"], "kW"
	
	print
	print "Actions:"
	print "Grid:", (solver.sol["LoadBrown[0]"] + solver.sol["BattBrown[0]"])>0
	print "Battery charge:", solver.sol["BattBrown[0]"]+solver.sol["BattGreen[0]"]>0
	print "Load: %.1fkW %d nodes" % (solver.sol["LoadBatt[0]"]+solver.sol["LoadBrown[0]"]+solver.sol["LoadGreen[0]"], (solver.sol["LoadBatt[0]"]+solver.sol["LoadBrown[0]"]+solver.sol["LoadGreen[0]"])/25.0)

	
	
	
	
	print
	print "Current status:"
	print "Load:", solver.sol["LoadBatt[15]"]+solver.sol["LoadBrown[15]"]+solver.sol["LoadGreen[15]"], "kW"
	print "Grid:", solver.sol["LoadBrown[15]"] + solver.sol["BattBrown[15]"], "kW"
	print "Battery charge:", solver.sol["BattBrown[15]"]+solver.sol["BattGreen[15]"], "kW"
	print "Battery discharge:", solver.sol["LoadBatt[15]"], "kW"
	print "Net metering", solver.sol["NetGreen[15]"], "kW"
	
	if "PanelsConnection[15]" in solver.sol:
		print
		print "PanelsConnection", solver.sol["PanelsConnection[15]"], "kW"
		print "GridWire        ", solver.sol["GridWire[15]"], "kW"
		print "BatteryWire     ", solver.sol["BatteryWire[15]"], "kW"
		print "LoadBrown       ", solver.sol["LoadBrown[15]"], "kW"
		print "BattBrown       ", solver.sol["BattBrown[15]"], "kW"
		print "NetGreen        ", solver.sol["NetGreen[15]"], "kW"
