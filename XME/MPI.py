import XME,time,numpy as np,traceback
try:
	import _pickle as pickle
except:
	try:
		import cPickle as pickle
	except:
		import pickle
from multiprocessing import cpu_count,Pipe,Manager
from threading import Thread,Event,Lock

ALL_PROCESSES="<XME-MPI-MARK: ALL PROCESSES>"
ANY_PROCESS="<XME-MPI-MARK: ANY PROCESS>"
TASK_END="<XME-MPI-MARK: TASK END>"
REQUEST_ACQUIRE="<XME-MPI-MARK: REQUEST ACQUIRE>"
REQUEST_SUCCESSFUL="<XME-MPI-MARK: REQUEST SUCCESSFUL>"
REQUEST_FAILURE="<XME-MPI-MARK: REQUEST FAILURE>"
REQUEST_EXIT="<XME-MPI-MARK: REQUEST EXIT>"
STATUS_BEGIN="<XME-MPI-STATUS: BEGIN>"
STATUS_IDLE="<XME-MPI-STATUS: IDLE>"
STATUS_ALLOCATED="<XME-MPI-STATUS: ALLOCATED>"
STATUS_INRUN="<XME-MPI-STATUS: INRUN>"
STATUS_END="<XME-MPI-STATUS: END>"
TASK_NO_REGISTERED="<XME-MPI-RUN: TASK_NO_REGISTERED>"
TASK_RUN_FAILURE="<XME-MPI-RUN: TASK_NO_REGISTERED>"
BUFFER_EMPTY="<XME-MPI-BUFFER: EMPTY>"
BUFFER_ALLOCATED="<XME-MPI-BUFFER: ALLOCATED>"
BUFFER_EOF="<XME-MPI-BUFFER: EOF"
def get_process_mark(tpid):
	if tpid==0: return "<XME-MPI-MARK: MAIN PROCESS>"
	else: return f"<XME-MMPI-MARK: TASK PROCESS {tpid}>"
class __XMEMPI__:
	def __init__(self,mpi,status,Main_Connector,Main_Request_Connector):
		self.mpi=mpi
		self.status=status
		self.Main_Connector=Main_Connector
		self.Main_Request_Connector=Main_Request_Connector
	def acquire(self, funid, args=(), kwargs={}, to=ANY_PROCESS,block=False): return self.mpi.acquire(self.status,self.Main_Connector,self.Main_Request_Connector, funid, args, kwargs, to, block)
	def close(self, to=ALL_PROCESSES): return self.mpi.close(self.status,self.Main_Connector,self.Main_Request_Connector,to)
	def get(self,pos): return self.mpi.get(pos)

class __XMEBUFFER__:
	def __init__(self,buffersize):
		self.size=buffersize
		self.locks=None
		self.last_alloc=-1
		for pos in range(self.size): exec(f"self.buffer_{pos}=BUFFER_EMPTY")

	def initial_locks(self): self.locks=[Lock() for _ in range(self.size)]

	def allocate(self):
		lls=list(range(self.size))
		lls=lls[self.last_alloc+1:]+lls[:self.last_alloc+1]
		for pos in lls:
			if self.__getitem__(pos)==BUFFER_EMPTY:
				if self.locks[pos].acquire(blocking=False):
					self.__setitem__(pos,BUFFER_ALLOCATED)
					self.locks[pos].release()
					self.last_alloc=pos
					if self.last_alloc== self.size-1: self.last_alloc=-1
					return pos
		return None

	def __getitem__(self,pos): return eval(f"self.buffer_{pos}")

	def __setitem__(self,pos,value): exec(f"self.buffer_{pos}=value")


class MPI:
	def __init__(self,mainfun,**xmeargs):
		self.Tasks={}
		self.buffer=__XMEBUFFER__(XME.get_par(xmeargs,"mpi_buffer_size",0xff))
		self.mainfun=mainfun
		self.xmeargs=xmeargs
		self.tasklocks=None
		self.global_buffer_lock=None
		self.global_task_lock=None
		self.pnum=XME.get_par(xmeargs,"pnum",cpu_count())
		if self.pnum>cpu_count():
			self.xmeargs["pnum"]=cpu_count()
			self.pnum=cpu_count()
		elif self.pnum<2: 
			raise ValueError("XME-MPI need at least 2 processes (1 main process + 1 task process)!")
			exit(0)

	def run(self,*args,**kwargs):
		m=Manager()
		status=m.dict()
		# pnum : task_processes: pnum-1
		Main_Connector={} #pipes to main process
		Task_Connector=[] #pipes to tasks processes
		Main_Request_Connector={}
		Task_Request_Connector=[] #pipes to tasks processes
		tpids=[]
		for i in range(1,self.pnum):
			tpid=get_process_mark(i)
			tpids.append(tpid)
			status[tpid]=STATUS_BEGIN
			pc,cc=Pipe()
			Main_Connector[tpid]=pc
			Task_Connector.append(cc)
			pc,cc=Pipe()
			Main_Request_Connector[tpid]=pc
			Task_Request_Connector.append(cc)
		xme=XME.XME(self.__task__,self.mainfun,**self.xmeargs)
		kwargs.update({"XMEMPI":__XMEMPI__(self,status,Main_Connector,Main_Request_Connector)})
		return xme.gfun(xme.Array(tpids),status,xme.Array(Task_Connector),xme.Array(Task_Request_Connector),garg=args,gargs=kwargs)[0][0]

	def __str__(self): return f"<class XME::MPI @ {hex(id(self))}: Task processes: {self.pnum}; Registed Tasks: {len(self.Tasks)}>"
	def __setitem__(self,key,value): self.Tasks[key]=value
	def __getitem__(self,key): return self.Tasks[key]

	def acquire(self, status,connets,req, funid, args=(), kwargs={}, to=ANY_PROCESS,block=False):
		def initial_locks():
			#each Event() object has 48 bytes size
			if self.global_buffer_lock: return
			self.buffer.initial_locks()
			self.global_buffer_lock=Event()
			self.global_task_lock=Event()
			self.tasklocks={tpid:Event() for tpid in status.keys()}

		def allocate_buffer():
			while True:
				pos=self.buffer.allocate()
				if pos!=None: return pos
				else: self.global_buffer_lock.wait()

		def send_and_recv(to,pos):
			with self.buffer.locks[pos]:
				connets[to].send(self.__encode__((funid,args,kwargs)))
				self.buffer[pos]=connets[to].recv()
				self.global_task_lock.set()
				self.tasklocks[to].set()
		
		initial_locks()
		if to==ALL_PROCESSES: return [self.acquire(status, connets, funid, args, kwargs,tpid) for tpid in status.keys()]
		elif type(to) in (list,tuple): return [self.acquire(status, connets, funid, args, kwargs,tpid) for tpid in to]
		elif to==ANY_PROCESS:
			closed=[]
			while True:
				wait=True
				for tpid,sta in status.items():
					if sta==STATUS_BEGIN: #means at least one task processes can be called in the future
						wait=False
						continue
					elif sta==STATUS_IDLE:
						req[tpid].send(self.__encode__(REQUEST_ACQUIRE))
						if self.__decode__(req[tpid].recv())!=REQUEST_SUCCESSFUL:continue
						status[tpid]=STATUS_ALLOCATED
						pos=allocate_buffer()
						if not block: Thread(target=send_and_recv,args=(tpid,pos)).start()
						else: send_and_recv(tpid,pos)
						return pos
					elif sta==STATUS_END and tpid not in closed: closed.append(tpid)
					if set(status.keys())==set(closed):return
				if wait: self.global_task_lock.wait()
		else:
			while True:
				if status[to]==STATUS_BEGIN: continue
				elif status[to]==STATUS_IDLE:
					req[to].send(self.__encode__(REQUEST_ACQUIRE))
					if self.__decode__(req[to].recv())!=REQUEST_SUCCESSFUL:continue
					status[to]=STATUS_ALLOCATED
					pos=allocate_buffer()
					if not block: Thread(target=send_and_recv,args=(to,pos)).start()
					else: send_and_recv(tpid,pos)
					return pos
				elif status[to]==STATUS_END:return
				self.tasklocks[to].wait()

	def get(self,pos):
		if not self.global_buffer_lock:raise ValueError("The XME.MPI Locks are undefinded that buffer cannot be accessed, please use acquire function to initialize.")
		if pos==None or pos>=self.buffer.size: return BUFFER_EOF
		elif self.buffer[pos]==BUFFER_EMPTY: return BUFFER_EOF 
		with self.buffer.locks[pos]: 
			result=self.__decode__(self.buffer[pos])
			self.buffer[pos]=BUFFER_EMPTY
			self.global_buffer_lock.set()
		return result

	def close(self, status,connets,req, to=ALL_PROCESSES): 
		if to==ALL_PROCESSES:
			closed=[]
			while True:
				for tpid,sta in status.items():
					if tpid not in closed:
						if sta==STATUS_IDLE:
							req[tpid].send(self.__encode__(REQUEST_EXIT))
							if self.__decode__(req[tpid].recv())!=REQUEST_SUCCESSFUL:continue
							connets[tpid].send(self.__encode__(TASK_END))
							closed.append(tpid)
						elif sta == STATUS_END: closed.append(tpid)
					if set(status.keys())==set(closed):return
		else:
			if status[to] == STATUS_END: return
			while True:
				if status[to]==STATUS_IDLE:
					req[to].send(self.__encode__(REQUEST_EXIT))
					if self.__decode__(req[to].recv())!=REQUEST_SUCCESSFUL:continue
					connets[to].send(self.__encode__(TASK_END))
					return

	def __encode__(self,data): return pickle.dumps(data)

	def __decode__(self,data): return pickle.loads(data)

	def __task__(self, tpid, status, connect, req, print=print):
		class request_status: value=True
		reqstatus=request_status()
		def process_request():
			while True:
				request=self.__decode__(req.recv())
				if request in (REQUEST_ACQUIRE,REQUEST_EXIT) and reqstatus.value:
					reqstatus.value=False
					req.send(self.__encode__(REQUEST_SUCCESSFUL))
					if request==REQUEST_EXIT: break
				else: req.send(self.__encode__(REQUEST_FAILURE))
		Thread(target=process_request).start()
		while True:
			try:
				reqstatus.value=True
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