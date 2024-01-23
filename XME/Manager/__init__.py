import multiprocessing
from .Object import Object
from .Monitor import Monitor
from .Security import Security
from copy import deepcopy
import hashlib,os,time,traceback,threading


GUARD_FUN_FAIL= "<-Guard Function Executes Failure->"
XMEM_GET_FAIL= "<-XMEM GET Failure->"
class XMEManager:
	def __init__(self,sec,mon,initialtable={},size=32):
		__manager__=multiprocessing.Manager()
		initialtable["__XMEM__"]={
			"Lock":{
				"initial":self.initial_lock,
				"update_onlock":self.update_onlock,
				"update_unlock":self.update_unlock,
				"update":self.update_lock
			},
			"Table":{
				"update":self.update,
				"set":self.set,
				"delete":self.delete,
				"items":self.items,
				"get":self.get_table
			},
			"Monitor":{
				"get":self.get_msg,
				"update":self.update_msg,
				"delete":self.delete_msg,
				"copy_msg":self.copy_msg
			}
		}
		initialtable["__GUARD__"]=__manager__.dict({"Status": True})
		initialtable["__STATUS__"]=__manager__.dict()
		fpc={}
		for key1,value1 in initialtable["__XMEM__"].items():
			for key2,value2 in value1.items(): fpc[f"{key1}::{key2}"]=value2
		initialtable["__XMEM__"].update(fpc)
		self.__valuetable__=__manager__.dict(initialtable)
		self.__Buffer_Call__=__manager__.dict({"GUARD":__manager__.list()})
		self.op_size=size
		self.security=sec
		self.monitor=mon
		self.update_onlock(self.security.acquire)
		self.update_unlock(self.security.release)

	def get_str(self):
		return f"<Class XMEManager @ {hex(id(self))} (Operator: {self.AllocOperator()}): <Values: {str(self.__valuetable__)}>; {self.security.get_str()}; {self.monitor.get_str()}>"
	def __str__(self):
		return self.get_str()

	# Buffer operation, usually call by Guard function
	def append(self,fun,Operator=None,**kwargs):
		#args,fun,
		if Operator==None: Operator=self.AllocOperator()
		self.__Buffer_Call__["GUARD"].append((fun,Operator,kwargs))
	def exec(self):
		Operator=self.__Buffer_Call__["GUARD"][0][1]
		if self.__Buffer_Call__["GUARD"][0][0]==__XMEHJ__:
			self.__valuetable__["__STATUS__"][Operator]=self.__Buffer_Call__["GUARD"][0][2]
			del self.__Buffer_Call__["GUARD"][0]
			return
		try:
			for key,value in self.__valuetable__["__XMEM__"]["Table"].items():
				if self.__Buffer_Call__["GUARD"][0][0]==value and "Operator" in value.__code__.co_varnames and Operator not in self.__Buffer_Call__["GUARD"][0][2]: 
					self.__Buffer_Call__["GUARD"][0][2]["Operator"]=self.security.ADMIN
					break
			for key,value in self.__valuetable__["__XMEM__"]["Monitor"].items():
				if self.__Buffer_Call__["GUARD"][0][0]==value and "Operator" in value.__code__.co_varnames and Operator not in self.__Buffer_Call__["GUARD"][0][2]: 
					self.__Buffer_Call__["GUARD"][0][2]["Operator"]=self.monitor.security.ADMIN
					break
			result=self.__Buffer_Call__["GUARD"][0][0](**self.__Buffer_Call__["GUARD"][0][2])
		except Exception as e:
			traceback.print_exc()
			result=GUARD_FUN_FAIL
		del self.__Buffer_Call__["GUARD"][0]
		self.__Buffer_Call__[Operator]=result
	def clean(self,Operator=None):
		if Operator==None: Operator=self.AllocOperator()
		try: del self.__Buffer_Call__[Operator]
		except: pass
	def get(self,Operator=None,MaxWaitTime=0,LoopTime=0.1):
		if Operator==None: Operator=self.AllocOperator()
		time1=time.time()
		while (Operator not in self.__Buffer_Call__): 
			if MaxWaitTime!=0 and time.time()-time1>MaxWaitTime: return XMEM_GET_FAIL
			time.sleep(LoopTime)
		result=self.__Buffer_Call__[Operator]
		del self.__Buffer_Call__[Operator]
		return result
	def status(self,Operator=None,status=None):
		if status==None: status=f"<-HeartJump::{time.time()}->"
		self.append(__XMEHJ__,Operator,status=status)
	def get_buffers(self):
		return deepcopy(self.__Buffer_Call__)
	def len(self):
		return len(self.__Buffer_Call__["GUARD"])
	def __len__(self):
		return self.len()

	# Lock operation functions, no suggest to call in manual!
	def update_onlock(self,onlock):
		self.__onlock__=onlock
	def update_unlock(self,unlock):
		self.__unlock__=unlock
	def update_lock(self,LockType):
		self.security.update_lock(LockType)
		self.monitor.security.update_lock(LockType)
	def initial_lock(self,Locks):
		self.security.set_lock(Locks[0],Locks[1])
		self.monitor.security.set_lock(Locks[2],Locks[3])
	
	#Table Operation
	def get_table(self,*keys):
		'''
		if self.security.acquire("Reader"):
			if len(keys)==0:  result=self.__valuetable__
			else:  #no modifiable!
				result={}
				for key,value in self.__valuetable__.items(): result[key]=value
		self.security.release("Reader")
		return result
		'''
		if len(keys)==0:  result=deepcopy(self.__valuetable__)
		elif len(keys) ==1 : result=self.__valuetable__[keys[0]]
		else: 
			result={}
			for key,value in self.__valuetable__.items(): 
				if key in keys: result[key]=value
		return result
	def set(self,key,value):
		self.__valuetable__[key]=value
	def __set__(self,key,value):
		self.set(key,value)
	def __getitem__(self,key):
		return self.get(get_table)
	def items(self):
		'''
		if self.__onlock__("Reader"): result=self.__valuetable__.items()
		self.__unlock__("Reader")
		return result
		'''
		return self.__valuetable__.items()
	def update(self,newtable,Operator=None):
		#if Operator=="Reader": return
		if Operator==None: Operator=self.AllocOperator()
		if self.security.acquire(Operator):
			self.__valuetable__.update(newtable)
		self.security.release(Operator)

	def delete(self,*keys,Operator=None):
		#if Operator=="Reader": return
		if Operator==None: Operator=self.AllocOperator()
		if len(keys)==0: keys=self.__valuetable__.keys()
		if self.security.acquire(Operator):
			for key in keys: 
				if key not in ("__STATUS__", "__GUARD__", "__XMEM__"): del self.__valuetable__[key]
		self.security.release(Operator)

	#Monitor Operation
	def get_msg(self,*keys):
		return self.monitor.get(*keys)
	def update_msg(self,newmessage,Operator=None):
		#if Operator=="Reader": return
		if Operator==None: Operator=self.AllocOperator()
		self.monitor.update(newmessage,Operator)
	def delete_msg(self,*keys,Operator=None):
		#if Operator=="Reader": return
		if Operator==None: Operator=self.AllocOperator()
		self.monitor.delete(*keys,Operator)
	def copy_msg(self,Operator=None):
		#if Operator=="Reader": return
		self.delete_msg(Operator)
		self.update_msg(self.__valuetable__,Operator)

	#Operator Name
	def AllocOperator(self,pid=os.getpid()):
		return f"<Operator::{hashlib.md5((str(pid)+str(time.time())).encode('utf-8')).hexdigest()[:self.op_size]}>"

class Guard:
	Status=True
	def __init__(self,ExitTime=10,LoopTime=1e-6,EmpLoopTime=1e-1,VerboseTime=5,script="#Scripts...\n"):
		self.script=script
		self.ExitTime=ExitTime
		self.LoopTime=LoopTime
		self.EmpLoopTime=EmpLoopTime
		self.VerboseTime=VerboseTime
	def __add__(self,newscript):
		self.script+=newscript
	def __Guard__(self,XMEManager,print=print):
		t_a=time.time()
		t_b=time.time()
		t0=time.time()
		while True:
			GuardInfo=XMEManager.get_table("__GUARD__")
			t1=time.time()
			if len(GuardInfo)==0 or "Status" not in GuardInfo or not GuardInfo["Status"] or not self.Status: break
			if XMEManager.len()>0: 
				t_a=t1
				t_b=t1
				XMEManager.exec()
				ex=True
			else: 
				t_b=t1
				ex=False
			if self.VerboseTime!=0 and t1-t0>self.VerboseTime:
				t0=t1
				print(f"XMEManager::Guard:: last heart jump: {round(t_b-t_a,2)} (Dead:> {self.ExitTime}); POC tasks: {XMEManager.len()}; Check time: {self.LoopTime} (empty: {self.EmpLoopTime})")
			if self.ExitTime!=0 and t_b-t_a>self.ExitTime:
				print("XMEManager::Guard:: Time exceeds heartbeat limit, process automatically ends")
				self.Status=False
				break
			time.sleep(self.LoopTime if ex else self.EmpLoopTime)
	def Guard(self, *args, print=print):
		XMEManager=args[-2]
		print=args[-1]
		args=args[:-2]
		Guth=threading.Thread(target=self.__Guard__,args=(XMEManager,print))
		Guth.start()
		__GUARD__=self
		exec(self.script)
		Guth.join()

def __XMEHJ__(status): return status
class HeartJump:
	def __init__(self,Operator,XMEManager,LoopTime=1):
		self.Operator=Operator
		self.Status=True
		self.XMEManager=XMEManager
		self.LoopTime=LoopTime
	def __do__(self):
		while True:
			if not self.Status: break
			self.XMEManager.status(self.Operator)
			time.sleep(self.LoopTime)
	def start(self):
		th=threading.Thread(target=self.__do__)
		th.start()
	def stop(self):
		self.Status=False

def XMEMBuilder(size=32,**initialtable): #automatically build a XMEManager
	sec=Object("Security",Security)
	mon=Object("Monitor",Monitor,sec)
	return Object("XMEManager",XMEManager,sec,mon,initialtable,size)