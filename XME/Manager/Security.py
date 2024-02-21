#Monitor.py
__version__="1.0"
__author__="WacmkXiaoyi@gmail.com"
__doc__="""
Class Security: shared data operations protocol (SecProto)

Package Needs: time

All types of locks only allow one thread to operate on shared data
"""

import time,random
from multiprocessing import Manager

#LockType:
DISABLE=0 #disable lock, Please use built-in lock in module threading!!!!
MUTEX=1 #mutex lock
AUTHORISATION=2 #authorisation operators
READWRITE=3 #Readwrite lock
SPIN=4 #Spin Lock

DEADLOCKMARK_ONLOCK="Onlock failure: illegal operator or deadlock!"
DEADLOCKMARK_UNLOCK="Unlock failure: illegal operator or deadlock!"

class ADMIN:
	def __str__(self):
		return "<SecProto::Operator:ADMIN>"

class Security:
	def __default_Deadlockfun_onlock__(self): return DEADLOCKMARK_ONLOCK
	def __default_Deadlockfun_unlock__(self): return DEADLOCKMARK_UNLOCK
	def __init__(self,LockType=READWRITE):
		__manager__=Manager()
		self.set_lock(__manager__.RLock(),__manager__.RLock())
		#Lock status, Locker, Locktype, Spintime, Default Wait Time
		self.ADMIN=ADMIN()
		self.__status__=__manager__.list([False,self.ADMIN,LockType,0.1,0,self.__default_Deadlockfun_onlock__,self.__default_Deadlockfun_unlock__])
		self.__AuthMap__=__manager__.list([self.ADMIN])
		self.update_lock(LockType)

	def get_str(self):
		def getlocktype():
			return {
				DISABLE:"disable",
				MUTEX:"Mutex",
				AUTHORISATION:"Authorisation",
				SPIN:"Spin",
				READWRITE:"Read-write"
			}[self.__status__[2]]
		def getstatus():
			return{
				True:f"Onlock (Type: {getlocktype()}), Locker: {self.__status__[1]}",
				False:"Unlock"
			}[self.__status__[0]]
		return f"<SecProto (class Security) @ {hex(id(self))}: <status: {getstatus()}>>"
	def __str__(self):
		return self.get_str()
	def set_lock(self,lockpoc,lockaut):
		self.__poclock__=lockpoc
		self.__auxlock__=lockaut #aux lock
		
	def update_lock(self,LockType):
		"""
		Update Locktype, and reallocate the lockfun
		args: LockType
		"""
		#self.__poclock__.acquire()
		self.__status__[2]=LockType
		self.__LockFun__={
			DISABLE:lambda Operator:True,
			MUTEX:self.__Mutex__,
			AUTHORISATION:self.__Auth__,
			SPIN:self.__Spin__,
			READWRITE:self.__ReadWrite__
		}[LockType]
		self.__UnLockFun__={
			DISABLE:lambda Operator:True,
			MUTEX:self.__Mutex_Release__,
			AUTHORISATION:self.__Auth_Release__,
			SPIN:self.__Spin_Release__,
			READWRITE:self.__ReadWrite_Release__
		}[LockType]
		#self.__poclock__.release()

	#Spin Lock 
	def __Spin__(self, Operator):
		return self.__Mutex__(Operator)
	def __Spin_Release__(self, Operator):
		return self.__Mutex_Release__(Operator)

	#MUTEX LOCK (Recommond)
	
	def __Mutex__(self,Operator):
		if self.__status__[0]: return self.__status__[1] == Operator
		# Try to acquire the lock
		acquired = self.__poclock__.acquire()
		if acquired:
			# Lock acquired successfully
			self.__status__[0] = True
			self.__status__[1] = Operator
			return True
		return False

	def __Mutex_Release__(self, Operator):
		# Release the lock only if the current operator matches
		if self.__status__[0] and self.__status__[1] == Operator:
			# Release the lock
			self.__status__ [0] = False
			self.__status__ [1] = None
			try:
				self.__poclock__.release()
			except:
				pass
			return True
		return False

	def MuteTime(self,mutetime):
		self.__status__[3]=mutetime


	#AUTHORISATION Lock
	#Only Operator in __AuthMap__ can Change Data
	def authorize(self,*Operator):
		"""
		Authorize who can access data
		args: Operator
		"""
		[self.__AuthMap__.append(i) for i in Operator]
	def __Auth__(self,Operator):
		if Operator not in self.__AuthMap__: return False
		return self.__Mutex__(Operator)
	def __Auth_Release__(self, Operator):
		if Operator not in self.__AuthMap__: return False
		return self.__Mutex_Release__(Operator)

	
	#Readwrite lock
	def registe(self,Operator):
		"""
		Registe who (only one) can access data
		args: Operator
		"""
		self.__status__[1]=Operator
	def __ReadWrite__(self, Operator):
		if Operator!=self.__status__[1]: return False
		return self.__Mutex__(Operator)
	def __ReadWrite_Release__(self, Operator):
		if Operator!=self.__status__[1]: return False
		return self.__Mutex_Release__(Operator)

	def WaitTime(self,waittime):
		self.__status__[4]=waittime
	def DeadLockFun(self,acquire=None,release=None):
		if acquire!=None: self.__status__[5]=acquire
		if release!=None: self.__status__[6]=release
	def acquire(self,Operator,WaitTime=None,DeadLockFun=None):
		"""
		Determine whether to lock, and if it has already been locked by the current operator, do not take any action
		args: 	1. Operator
				2. WaitTime: if timer>WaitTime, call DeadLockFun() [option, default 0 -> no check]
				3. DeadLockFun [option, default do nothing]

		Please set `WaitTime` to avoid death lock

		Return bool:
		Ture : Onlock Successful 
		False: Onlock failure (AUTHORISATION & READWRITE only)
		
		Recommond Usage:
		1. sp.acquire(op[,WaitTime]) MUTEX & SPIN
		2. if sp.acquire(op[,WaitTime]): <...> AUTHORISATION & READWRITE
		"""
		#Check Disable
		'''
		if self.__status__[2] == DISABLE: return True 

		#check ReadWrite
		elif self.__status__[2] == READWRITE: return self.__LockFun__(Operator)

		#Check illegal operator in AUTHORISATION
		elif self.__status__[2] == AUTHORISATION and Operator not in self.__AuthMap__:return False

		#Check Onlock
		elif Operator==self.__status__[1]: return True
		'''
		#Legitimate operator
		if WaitTime==None: WaitTime=self.__status__[4]
		if DeadLockFun==None: DeadLockFun=self.__status__[5]
		time1=time.time()
		while not self.__LockFun__(Operator):
			if WaitTime!=0 and time.time()-time1>WaitTime: return DeadLockFun() #Detecting death lock
			if self.__status__[2] == MUTEX: time.sleep(self.__status__[3])

		return True # onlock successfully

	def release(self,Operator,WaitTime=None,DeadLockFun=None):
		"""
		The release operation of a lock, any lock (except DISABLE and READWRITE) that is not in use after being used should be released
		args: Operator

		Return bool
		True: Unlock successfully (including unlock status...)
		False: Unlock failure, e.g., illegal operator
		"""
		'''
		if self.__status__[2]==DISABLE: return True
		elif self.__status__[1]!=Operator: return False
		elif self.__status__[2]==READWRITE: return True
		self.__LockFun__(Operator)
		return not self.__status__[0]
		'''
		if WaitTime==None: WaitTime=self.__status__[4]
		if DeadLockFun==None: DeadLockFun=self.__status__[6]
		time1=time.time()
		while not self.__UnLockFun__(Operator):
			if WaitTime!=0 and time.time()-time1>WaitTime: return DeadLockFun()
		return True

if __name__=="__main__":
	a=0
	def debug(LockType):
		import threading,hashlib
		#initial debug...
		def testsp(Operator):
			global a
			time1=time.time()
			print("Operator:",Operator,"\n\tStatus->Unlock:",sp,"\n\tValue:",a,"\n")
			if sp.acquire(Operator):
				print("Operator:",Operator,"\n\tStatus->Onlock:",sp,"\n\tValue:",a,"\n")
				for i in range(10000000): a+=1
			else: print("Operator:",Operator,"\n\tOnlock failure:",sp)
			if sp.release(Operator): print("Operator:",Operator,"\n\tStatus->Release lock:",sp,"\n\tValue:",a,"\n")
			else: print("Operator:",Operator,"\n\tUnlock failure:",sp)
			time2=time.time()
			print("Operator",Operator,": finished, use time:",time2-time1,"\n")
		def get_thread_name(name,size=8):
			return "Thread-"+hashlib.md5(name.encode('utf-8')).hexdigest()[:size]
		global a
		a=0 #ideal result=40000000 (disable) 20000000(other)
		sp=Security(LockType)
		name1=get_thread_name("th1")
		th1=threading.Thread(target=testsp,args=(name1,),name=name1)
		name2=get_thread_name("th2")
		th2=threading.Thread(target=testsp,args=(name2,),name=name2)
		sp.authorize(name1)
		sp.registe(name2)
		th1.start()
		th2.start()
		th1.join()
		th2.join()
	debug(4)