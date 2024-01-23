import XME,time,numpy as np,traceback
try:
	import _pickle as pickle
except:
	try:
		import cPickle as pickle
	except:
		import pickle
from multiprocessing import cpu_count,Pipe,Manager
from threading import Thread

ALL_PROCESSES="<XME-MPI-MARK: ALL PROCESSES>"
ANY_PROCESS="<XME-MPI-MARK: ANY PROCESS>"
TASK_END="<XME-MPI-MARK: TASK END>"
STATUS_BEGIN="<XME-MPI-STATUS: BEGIN>"
STATUS_IDLE="<XME-MPI-STATUS: IDLE>"
STATUS_ALLOCATED="<XME-MPI-STATUS: ALLOCATED>"
STATUS_INRUN="<XME-MPI-STATUS: INRUN>"
STATUS_END="<XME-MPI-STATUS: END>"
TASK_NO_REGISTERED="<XME-MPI-RUN: TASK_NO_REGISTERED>"
TASK_RUN_FAILURE="<XME-MPI-RUN: TASK_NO_REGISTERED>"
BUFFER_EMPTY="<XME-MPI-BUFFER: EMPTY>"
BUFFER_EOF="<XME-MPI-BUFFER: EOF"
def get_process_mark(tpid):
	if tpid==0: return "<XME-MPI-MARK: MAIN PROCESS>"
	else: return f"<XME-MMPI-MARK: TASK PROCESS {tpid}>"
class MPI:
	def __init__(self,mainfun,**xmeargs):
		self.Tasks=Manager().dict()
		self.buffersize=XME.get_par(xmeargs,"mpi_buffer_size",0xff)
		self.buffer=Manager().list([BUFFER_EMPTY for i in range(self.buffersize)])
		self.bufferpos=0

		self.mainfun=mainfun
		self.xmeargs=xmeargs
		self.pnum=XME.get_par(xmeargs,"pnum",cpu_count())
		if self.pnum>cpu_count():
			self.xmeargs["pnum"]=cpu_count()
			self.pnum=cpu_count()
		elif self.pnum<2: 
			raise ValueError("XME-MPI need at least 2 processes (1 main process + 1 task process)!")
			exit(0)

	def run(self,*arg,**kwargs):
		m=Manager()
		status=m.dict()
		# pnum : task_processes: pnum-1
		Main_Connector={} #pipes to main process
		Task_Connector=[] #pipes to tasks processes
		tpids=[]
		for i in range(1,self.pnum):
			tpid=get_process_mark(i)
			tpids.append(tpid)
			status[tpid]=STATUS_BEGIN
			pc,cc=Pipe()
			Main_Connector[tpid]=pc
			Task_Connector.append(cc)
		xme=XME.XME(self.__task__,self.mainfun,**self.xmeargs)
		kwargs.update({"XMEMPI":(self,status,Main_Connector)})
		xme.gfun(status,xme.Array(tpids),xme.Array(Task_Connector),garg=arg,gargs=kwargs)

	def __str__(self): return f"<class XME::MPI @ {hex(id(self))}: Task processes: {self.pnum}; Registed Tasks: {len(self.Tasks)}>"
	def __setitem__(self,key,value): self.Tasks[key]=value
	def __getitem__(self,key): return self.Tasks[key]

	def acquire(self, status, connets, funid, arg=(), kwargs={}, to=ANY_PROCESS,block=False):
		def send_and_recv(to,pos):
			connets[to].send(self.__encode__((funid,arg,kwargs)))
			self.buffer[pos]=connets[to].recv()
		if to==ALL_PROCESSES: return [self.acquire(status, connets, funid, arg, kwargs,tpid) for tpid in status.keys()]
		elif type(to) in (list,tuple): return [self.acquire(status, connets, funid, arg, kwargs,tpid) for tpid in to]
		elif to==ANY_PROCESS:
			closed=[]
			while True:
				for tpid,sta in status.items():
					if sta==STATUS_IDLE:
						status[tpid]=STATUS_ALLOCATED
						pos=self.bufferpos
						if not block: Thread(target=send_and_recv,args=(tpid,pos)).start()
						else: send_and_recv(tpid,pos)
						self.bufferpos+=1
						if self.bufferpos==self.buffersize: self.bufferpos=0
						return pos
					elif sta==STATUS_END and tpid not in closed: closed.append(tpid)
					if set(status.keys())==set(closed):return
		else:
			while True:
				if status[to]==STATUS_IDLE:
					status[to]=STATUS_ALLOCATED
					pos=self.bufferpos
					if not block: Thread(target=send_and_recv,args=(to,pos)).start()
					else: send_and_recv(tpid,pos)
					self.bufferpos+=1
					if self.bufferpos==self.buffersize: self.bufferpos=0
					return pos
				elif status[to]==STATUS_END:return

	def get(self,pos, timeout=0,looptime=0.1):
		if pos==None or pos>=self.buffersize: return BUFFER_EOF
		t0=time.time()
		while self.buffer[pos]==BUFFER_EMPTY:
			if timeout!=0 and time.time()-t0>timeout: 
				print(f"Warning: timeout for getting result from buffer at position {pos}")
				return
			time.sleep(looptime)
		result=self.__decode__(self.buffer[pos])
		self.buffer[pos]=BUFFER_EMPTY
		return result

	def close(self, status, connets, to=ALL_PROCESSES):
		if to==ALL_PROCESSES:
			closed=[]
			while True:
				for tpid,sta in status.items():
					if tpid not in closed:
						if sta==STATUS_IDLE:
							connets[tpid].send(self.__encode__(TASK_END))
							closed.append(tpid)
						elif sta == STATUS_END: closed.append(tpid)
					if set(status.keys())==set(closed):return
		else:
			if status[to] == STATUS_END: return
			while True:
				if status[to]==STATUS_IDLE:
					connets[to].send(self.__encode__(TASK_END))
					return

	def __encode__(self,data): return pickle.dumps(data)

	def __decode__(self,data): return pickle.loads(data)

	def __task__(self, status, tpid, connect, print=print):
		while True:
			try:
				status[tpid]=STATUS_IDLE
				request=self.__decode__(connect.recv())
				status[tpid]=STATUS_INRUN
				#request message: (funname, arglist, kwargdict)
				if request==TASK_END: 
					status[tpid]=STATUS_END
					break
				funid, arg, kwargs=request
				if funid in self.Tasks: 
					result=self.Tasks[funid](*arg,**kwargs)
					connect.send(self.__encode__(result))
				else: connect.send(self.__encode__(TASK_NO_REGISTERED))
			except Exception as err:
				traceback.print_exc()
				connect.send(self.__encode__(TASK_RUN_FAILURE))