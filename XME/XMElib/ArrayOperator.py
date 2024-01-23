from multiprocessing import cpu_count,Manager
def get_par(args,name,default=None):
	try:
		return args[name]
	except:
		return default
class ArrayOperator:
	def __init__(self,**args):
		self.pnum=get_par(args,"pnum",cpu_count())
		self.results=[]
		self.args=[]
		self.cal_num=get_par(args,"cal_num",0)
		manager=Manager()
		for i in range(self.pnum):
			self.results.append(manager.list())
			self.args.append([])
		pn=0
		for i in range(self.cal_num):
			self.args[pn].append([])
			pn+=1
			if pn==self.pnum: pn=0
	def add_argscut(self,args,default_args=None):
		pnum=0
		co=0
		cal_n=0
		for i in args:
			if cal_n<self.cal_num: self.args[pnum][co].append(i)
			pnum+=1
			cal_n+=1
			if pnum==self.pnum:
				pnum=0
				co+=1
		for i in range(cal_n,self.cal_num):
			self.args[pnum][co].append(default_args)
			pnum+=1
			if pnum==self.pnum:
				pnum=0
				co+=1
	def add_common_args(self,*args):
		if len(args)>1:
			for i in args: self.add_common_args(i)
		else:
			pnum=0
			co=0
			for i in range(self.cal_num):
				self.args[pnum][co].append(args[0])
				pnum+=1
				if pnum==self.pnum:
					pnum=0
					co+=1
	def result_combine(self):
		new_result=[]
		for j in range(len(self.results[0])):
			for i in range(len(self.results)):
				try: new_result.append(self.results[i][j])
				except: continue
		self.results=tuple(new_result)