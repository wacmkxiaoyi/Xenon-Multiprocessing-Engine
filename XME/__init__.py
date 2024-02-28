from multiprocessing import cpu_count
from .XMElib.ArrayOperator import ArrayOperator
from .XMElib.Executor import Executor
from .XMElib.Logputter import Logputter
from .XMElib import get_par

class XME:
	aoobj_array=[]
	exobj_array=[]

	class Array(list):pass

	def __init__(self,*fun,**args):
		if get_par(args,"pnum",cpu_count())>cpu_count(): args["pnum"]=cpu_count()
		elif get_par(args,"pnum",cpu_count())<1: args["pnum"]=1
		self.pnum=get_par(args,"pnum",cpu_count())
		self.funs=[]
		if get_par(args,"do_with_log",True):
			self.logobj=Logputter(get_par(args,"logfile"),get_par(args,"show_version_info",False))
			self.logobj.print_in_screen=get_par(args,"print_in_screen",True)
		else: self.logobj=None
		def func(funum,*targ,**args):
			args.update({"logobj":self.logobj})
			if self.logobj!=None: args.update({"print":self.logobj.write_log})
			calnum=get_par(args,"calnum",0)
			if calnum==0:
				for i in targ:
					if type(i)==self.Array: calnum=max(calnum,len(i))
				for i in args.keys():
					if type(args[i])==self.Array: calnum=max(calnum,len(args[i]))
			if calnum==0: calnum+=1 #at least run once
			ao=self.ao(calnum,self.pnum)
			for i in targ: #first set
				if type(i)!=self.Array: ao.add_common_args(i)
				else: ao.add_argscut(i)
			for i in fun[funum].__code__.co_varnames: #follow sequence
				if i in args.keys():
					if type(args[i])!=self.Array: ao.add_common_args(args[i])
					else: ao.add_argscut(args[i])
			return ao
		if len(fun)>0:
			def run_funs(funum_array=range(len(fun)),args_array=[[]]*len(fun),kwargs_array=[{}]*len(fun)):
				if len(funum_array)!=len(args_array) or len(funum_array)!=len(kwargs_array):
					print("Error parameters number")
					return ()
				ao=[]
				results=[]
				tfuns=[]
				for i in range(len(funum_array)):
					tfuns.append(fun[funum_array[i]])
					ao.append(func(funum_array[i],*(args_array[i]),**(kwargs_array[i])))
				ex=self.ex(*tfuns,pnum=self.pnum)
				ex.build_from_ao(ao)
				results=[]
				for i in range(len(funum_array)):
					ao[i].result_combine()
					results.append(ao[i].results)
				return tuple(results)
			self.funs=run_funs
			def single_fun(*targ,**args): return run_funs([0],[targ],[args])[0]
			self.fun=single_fun
			def gfun(*fargs,gargs=[],gkwargs={},**fkwargs): return run_funs([-1,0],args_array=[gargs,fargs],kwargs_array=[gkwargs,fkwargs])
			self.gfun=gfun
			def gfuns(funum_array=range(len(fun)-1),fargs_array=[[]]*(len(fun)-1),fkwargs_array=[{}]*(len(fun)-1),gargs=[],gkwargs={}): return run_funs([-1]+funum_array,args_array=[gargs]+fargs_array,kwargs_array=[gkwargs]+fkwargs_array)
			self.gfuns=gfuns

	def __call__(self,*args,**kwargs): return self.fun(*args,**kwargs)

	def ao(self,calnum,pnum=None):
		if pnum==None: pnum=self.pnum
		self.aoobj_array.append(ArrayOperator(cal_num=calnum,pnum=pnum))
		return self.aoobj_array[-1]
	def ex(self,*fun,**args):
		self.exobj_array.append(Executor(*fun,**args))
		return self.exobj_array[-1]
	def clean(self):
		self.aoobj_array=[]
		self.exobj_array=[]

def build(*fun,**args):
	return XME(*fun,**args)
