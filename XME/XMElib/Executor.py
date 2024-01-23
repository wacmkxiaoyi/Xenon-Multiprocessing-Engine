from multiprocessing import Pool,cpu_count#,Lock
import numpy
def tuplize(array):
	if type(array) in (list,tuple, numpy.ndarray):
		result=[]
		for i in array:
			if type(i) in (list, numpy.ndarray): result.append(tuplize(i))
			else: result.append(i)
		return tuple(result)
	return array
def get_par(args,name,default=None):
	try: return args[name]
	except: return default
class Executor:
	default_fun_strc="fun"
	def __init__(self,*fun,**args):
		self.clear_fun()
		self.add_fun(fun)
		self.pnum=get_par(args,"pnum",cpu_count())
		self.results=[]
	def do_fun(self,args=(),funname=None,returns=None):
		for i in args:
			if funname==None: funname=tuple(self.fun.keys())[-1]
			result=self.fun[funname](*i)
			if returns!=None: returns.append(result)
		if returns!=None: return returns
	def add_a_pool(self,args,funname=None,close=True,join=True,returns=None):
		pool=Pool(1)
		if funname==None: funname=tuple(self.fun.keys())[-1]
		result=pool.apply_async(self.do_fun,(args,funname,returns))
		if close: pool.close()
		if join: pool.join()
		return tuplize(result.get())
	def build_from_ao(self,ao,close=True,join=True,pnum=None):
		if pnum==None: pnum=self.pnum
		pool=Pool(pnum)
		results=[]
		infunname=tuple(self.fun.keys())
		if type(ao) is tuple or type(ao) is list:
			funname=[]
			for i in range(len(ao)):
				if i < len(infunname): funname.append(infunname[i])
			for i in range(len(infunname),len(ao)): funname.append(infunname[-1])
			new_ao={}
			for i in funname: new_ao[i]=()
			for i in range(len(funname)): new_ao[funname[i]]+=(ao[i],)
			ao=new_ao
		elif type(ao) is dict:
			new_ao={}
			for i in ao.keys():
				if i in infunname:
					if type(ao[i]) is tuple or type(ao[i]) is list: new_ao[i]=tuple(ao[i])
					else: new_ao[i]=(ao[i],)
				else: print("Warnning: fun name:",i,"no in library")
			ao=new_ao
		else: ao={infunname[-1]:(ao,)}
		for i in ao.keys():
			for j in ao[i]:
				for k in range(j.pnum): results.append(pool.apply_async(self.do_fun,(j.args[k],i,j.results[k])))
		if close: pool.close()
		if join: pool.join()
		new_results=[]
		for i in results:
			new_results.append(i.get())
		return new_results
	def add_fun(self,fun):
		if type(fun) is tuple or type(fun) is list:
			tvi=0
			for i in range(len(self.fun.keys()),len(self.fun.keys())+len(fun)):
				self.fun[self.default_fun_strc+str(i)]=fun[tvi]
				tvi+=1
		elif type(fun) is dict:
			for i in self.fun.keys(): self.fun[i]=fun[i]
		else: self.fun[self.default_fun_strc+str(len(self.fun.keys()))]=fun
	def clear_fun(self): self.fun={}