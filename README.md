# Xenon-Multiprocessing-Engine
Xenon-Multiprocessing-Engine (**XME** thereafter) is a (platform-independent) portable optimization interface based on **multiprocessing** for process pool operation, supports the most of **serializable-split** operations.

Version 3.3
Update: 2023-12-31

Author: Junxiang H. & Weihui L. <br>
Suggestion to: wacmkxiaoyi@gmail.com
Website: wacmk.cn/com


# Installation

Please make sure the packages/libraries has been installed before installing XME:

1. **os**,**copy**,**time**,**random**,**multiprocessing** ; XME will call those packages to perform process pool control, share variable proxies, etc (basic functions)
2.  **json,hashlib,traceback,threading** ; If you attempt to perform **shared memory proxy** operations through XME, especially manager-guard processes using XME, then these libraries should be included

and follow the blow parse to install:

```shell
pip3 install XME
```

# 1 Standard Interface 

## 1.1 Basic Structure

The basic idea of XME is similar to a pair of function table. Generally there are two solutions:

1. For a very large data set, we will perform some repeated operations on all data streams, and these operations are divisible and serializable, and the running time\>\>process awakening time; 
2. For multiple different types of operations, we need to perform them simultaneously. They can be related to each other but are generally independent. 
At those points we will create a process pool. The process pool associated with XME is based on functions. First, XME will store all function addresses in a list (similar to the virtual function table in C++, see the table):

key     |     function

fun1   ...    0x00000256

fun2   ...    0x000002a3

fun3   ...    0x0000030c

....   ...    .....

These functions can be entered as parameters of the initialization function (i.e., **\_\_init\_\_()**) when creating the XME object:

```python
import XME
xme=XME.XME(fun1,fun2,fun3,...,funN[,options=values...]) #insert into functions table by __init__()
'''

The **options** are mainly some other parameters involved in creating XME objects, such as:
key   |    type     |   default value   |   description
pnum        int         cpu cores number    Maximum number of calling threads for XME (<=cpu cores number)
do_with_log bool        Structure           Whether to perform log output
logfile     str         None                If not **None**, display the results to a specific file
show_version_info bool  False               Output XME version information when calling XME
print_in_screen bool    True                Output the results to the screen (such as doc window)

Note: Please refer to the **logger** section for log output operations.
'''
```

In order to ensure that the daemon process does not end before other processes, the processes in the process pool need to perform the **.join()** operation, so XME does not support awakening some processes first and then awakening other processes. That is to say, we need an extended function table to store the functions that need to be called and the corresponding parameters. The functions in this extended function table will be executed simultaneously:

key     |     function       |      args

funa   ...    0x00000256    ...     a=1, b=1, c=1

funa   ...    0x00000256    ...     a=2, b=1, c=1

funb   ...    0x000002a3    ...     v=10

Taking the above table as an example, XME will create three processes, two funa processes, and one funb process. But it is obviously not smart enough for the user to repeatedly define the two calls to funa (which does not satisfy any of the solutions mentioned above). XME provides a basic class **XME.Array** to declare what variables need to be split. The specific splitting operation will be completed in the XME sub-module **XME.ArrayOperator**, and the user does not need to perform additional operations. According to this rule, we can define the executions table as:

key     |     function       |      args

funa   ...    0x00000256    ...     a=xme.Array(range(2)), b=1, c=1

funb   ...    0x000002a3    ...     v=10

**Special case 1**: If multiple XME.Arrays appear in one extended table (such as **funa(a=xme.Array(range(10)), b=xme.Array(("b1","b2","b3") )**), then the number of processes will be allocated according to the maximum value of the key name of the current function (for example, 10 in the above example). Since the number of parameters b is less than 10, the b parameters for the 4th to 10th processes will all be b The last parameter in the parameter list (that is, "b3")

**Special case 2**: If the total number of allocated processes is greater than the maximum allowed number of core awakenings (i.e. pnum), then the table will be executed in a queue from top to bottom in the extended table. A simple example is if pnum=5, but the number of processes that need to be ventilated is 10, then the 1-5 processes will be executed first, while the 6-10 processes will be in the waiting queue.

After the executions table is created, the executions table will be passed as a parameter to the execution module of XME (ie **XME.Executor**), and XME.Executor will automatically allocate two processes to funa. Of course, this part is something that users don’t need to worry about. Usually, users need to define their own XME.Executor. When all processes are executed, XME.Executor will collect the return values of all functions and return them as results in the form of tuples (indexed according to the execution order of the executions table)

## 1.2 Examples in Standard Interface 
Next, we will introduce the use of standard interfaces with practical examples.

### 1.2.1 Single Function Model
**Note**: This example **is not recommended** for the truth multi-process operation, because the process wake-up time will be much longer than the execution time

```python
def fun(v): return sum([i for i in range(v+1,v+11)])
```

The very simple function fun shown above will return the cumulative value from v+1 to v+10. If you want to calculate the cumulative value from 1 to 100, it is obvious that a common way of writing it is

```python
if __name__=="__main__": 
  v=[v*10 for v in range(10)]
  print(sum([fun(i) for i in v])) #single process
```

If you want to implement the above functions through XME, the actual writing method is very similar, in the **single function model**, we will use **xme.fun(\*args)** to tell XME.Executor the call the first (or the top) function on the functions table:

```python
if __name__=="__main__":
  import XME
  xme=XME.XME(fun) # insert function `fun` into functions table
  v=xme.Array([v*10 for v in range(10)]) #set v is a splitable array
  print(sum(xme.fun(v))) #xme.fun will call the top function (i.e., fun(v)) in the functions table, and returns a tuple with fun(v)'s result in executions table

  '''
  xme.fun(*targ,**args):
  *targ, list of target function's paramters
  **args, dict of target function's keyword parameters
  '''
```

and result:

```DOC
>>>5050
```

**-------------------------------------------------------**

We need to remind you again that **multi-process operations are not recommended for overly simple logical operations**! The non-negligible process wake-up time will seriously affect execution efficiency! If we integrate the above examples:

```python
def fun(v): return sum([i for i in range(v+1,v+11)])
if __name__=="__main__":
  import XME,time
  v=[v*10 for v in range(10)]
  time_use_xme_0=time.time()
  xme=XME.XME(fun)
  print("xme",sum(xme.fun(xme.Array(v))))
  time_use_xme_1=time.time()

  time_no_xme_0=time.time()
  print("noxme",sum([fun(i) for i in v]))
  time_no_xme_1=time.time()

  print("xme",time_use_xme_1-time_use_xme_0)
  print("noxme",time_no_xme_1-time_no_xme_0)
```

and result:
```DOC
>>>xme 5050
>>>noxme 5050
>>>xme 2.2150542736053467
>>>noxme 0.000005324
```

It can be seen that the time required to arouse ten processes is much greater than the execution time of a single process. But let's make some simple modifications to this function. We calculate the accumulation from 1 to 100 million:

```DOC
>>>xme 5000000050000000
>>>noxme 5000000050000000
>>>xme 4.029731035232544
>>>noxme 6.781273126602173
```

At this point the advantages of using XME are shown. This corresponds exactly to solution 1 in section 1.1

**-------------------------------------------------------**

### 1.2.2 Multi-Functions Model
At some situations (**especially solution 2 in section 1.1**), a multi-function model will be more useful than a single-function model. For example, in the C/S model (client-server model), the server usually provides more than one service, and even if there is only one service, load balancing is required. Since load balancing needs to involve inter-process communication and sending and receiving functions (such as shared memory mentioned later), we will not discuss it too much here. We assume that a server provides two services (ServicesA, ServicesB) such as:

```python
class BasicServices:
  #some functions/attributes
  pass

class ServicesA(BasicServices):
  def Main(self,*args):
    while True:
      #do something
      continue

class ServicesB(BasicServices):
  def Main(self,*args):
    while True:
      #do something
      continue
```

At this time, if you need to call service A and service B at the same time, one way is to use multi-threading, and the other is to use multi-process. We first introduce the multi-threading method:

```python
if __name__=="__main__": #multi-thread models
  import threading
  ser=[ServicesA(),ServicesB()]
  th=[threading.Thread(target=i.Main) for i in ser]
  [i.start() for i in th]+['''daemon thread operations''']+[i.join() for i in th]
```

However, since python's multi-threading is actually bound to one process, the actual execution efficiency is not much different from that of a single process. If the service demand is large, congestion problems may easily occur. Next, we will introduce the use of multi-process concurrent service establishment based on solution 2 of section 1.1.

```python
if __name__=="__main__":
  import XME
  ser=[ServicesA(),ServicesB()] #similar to multi-thread models
  xme=XME.XME(*[i.Main for i in ser]) #insert function into functions table
  xme.funs(tagr_array=[['''args of serA'''],['''args of serB''']]) #call the server
  '''
  xme.funs(funum_array=range(len(<funtable.keys>)),tagr_array=[[]]*len(<funtable.keys>), args_array=[{}]*len(<funtable.keys>)
  funum_array: insert which functions from functions table into excution table, default: all functions in functions table
  tagr_array: *targ=tagr_array[i] is function with index "i" in functions table
  args_arrag: **args=args_array[i] ....
  '''
```

**Special note**: The parameters of the above function functions are arbitrary. When using XME, you need to pay attention to the following issues when calling such functions:



**1.** Generalized key-value pairs will no longer be generalized! For example:
```python
def example_fun(a0,a1=None,a2=None,**kwargs):
  print(a0) # i of range(10)
  print(a1) # a1
  print(a2) # a2
  print(kwargs) # {}, empty (Assignment failed)

if __name__=="__main__":
  import XME
  xme=XME.XME(example_fun)
  xme.fun(xme.Array(range(10)),a1="a1",a2="a2",kw1="kw1",kw2="kw2"):
```

solution:

```python
  #modify the execute function:
  xme.fun(xme.Array(range(10)),a1="a1",a2="a2",kwargs={kw1:"kw1",kw2:"kw2"}):
```



**2.** Once any list parameter type such as \*args is defined in a function, all parameters after args  will be invalid, such as:

```python
def example_fun(*args,a1=None,a2=None):
  print(args) # [0, 1, i of range(10), a1, a2]
  print(a1) # None, default (Assignment failed)
  print(a2) # None, default (Assignment failed)

if __name__=="__main__":
  import XME
  xme=XME.XME(example_fun)
  xme.fun(0,1,xme.Array(range(10)),a1="a1",a2="a2"):
```

solution:

```python
  def example_fun(*args,a1=None,a2=None):
  #dispatach the args list:
  a1,a2=args[-2:]
  args=args[:-2]
```

## 1.3 Examples of Using Special Parameters
In section 1.2.1, we briefly introduced that when the user defines the execution table, this table will be passed to XME.Executor. In the target function, we can specify some specific parameters to call the built-in functions or modules from XME. We will use XME’s built-in log outputter (XME.Logputter) as an example here.

### 1.3.1 Print
The print function that comes with XME is part of the XME.Logputter module. It has a more powerful output function than the python built-in function print, and also has a log file writing function. To call XME's built-in print we need to do two things:

```python
def fun(print=print) :#add a parameter print in parameter list, and default is built-in print to compatible with single process
  print("This is function fun")
  '''
  print *(*message,**args) = XME.Logger.write_log
  option of args:
    1. msgtype: default None, if None, do not show the message type
    2. indent: default 0, show the indent to mark sub logs
    3. pid: default os.getpid(), if None, do not show the pid mark
  '''
if __name__=="__main__":
  import XME
  xme=XME.XME(fun,do_with_log=True) #set the keyword do_with_log=True, but it's True defaultly, so normally no need to specify
  #...
```

and result:
```DOC
2023-10-20 03:34:27(pid@114796):This is function fun
2023-10-20 03:34:27(pid@139888):This is function fun
2023-10-20 03:34:27(pid@137936):This is function fun
2023-10-20 03:34:27(pid@108580):This is function fun
2023-10-20 03:34:27(pid@170120):This is function fun
2023-10-20 03:34:27(pid@92352):This is function fun
2023-10-20 03:34:27(pid@27896):This is function fun
2023-10-20 03:34:27(pid@36988):This is function fun
2023-10-20 03:34:27(pid@49688):This is function fun
2023-10-20 03:34:27(pid@170552):This is function fun
```

### 1.3.2 Logobj
If you need to modify the output style of XME.Logputter when the target function is executed (for example, you need each process to present a different log mode), we can write the following parameter names into the function definition.

```python
def fun(logobj=None) :
  #do something of logobj's attributes, see the table below
  '''
  logobj.logfile, default None, log in a certain file
  logobj.time, default True, log the Time in the log, e.g., 2023-10-20 03:34:27 
  logobj.msgtype, default True, log the message type
  logobj.default_msgtype, deault Message, default message type
  logobj.processing, default True, log the pid, e.g., (pid@27896
  logobj.indent, default True, sub log indent
    indent_type and num, "-"/4, sub log indent type
  '''
  if logobj!=None: print=logobj.write_log
  #do something
```

# 2 Advanced Interface
In the standard interface of XML, the design idea of the program should be based on the solution suggested in section 1.1. In this chapter we will introduce the use of XME advanced interface one by one.

## 2.1 Shared Memory
XME supports proxying from basic data types provided by multiprocessing.Manager. Users can define corresponding types of parameter types to insert into the execution table and achieve target functions. In addition to various proxy variables defined by users based on Manager(), XME also provides three functions for implementing the definition of proxy variables:

```python
import XME
shared_list=XME.xmem_list(init={}) #defind a shared memory list, same as multiprocessing.Manager().list(init)
shared_dict=XME.xmem_dict(init={}) #defind a shared memory dict, same as multiprocessing.Manager().dict(init)
class Class_Name:
  def __init__(self,*args,**kwargs):
    pass
shared_object=XME.xmem_object("Class_Name",Class_Name,*initargs=*[],**initkwargs=**{}) #defind a shared memory object
#Special note that all attributes in the shared class functions defined according to XME.xmem_object cannot be called directly, and private functions cannot be used, such as __str__, __add__, __get__, etc.
```

Then shared memory variables (proxy variables) such as shared_list will be inserted into the execution table in the form of proxy addresses and ordinary variable:

key     |     function       |      args

funa   ...    0x00000256    ...     a=shared_list (point to proxy address: 0x00000743),b=xme.Array(range(10))

funa   ...    0x000002a3    ...     a=shared_list (point to proxy address: 0x00000743)

### 2.1.1 Shared Memory Lock
The problem of reading and writing shared memory variables in multi-process programs usually encounters lock interaction problems that are more troublesome than those in multi-threads. We also strongly recommend using associated locking operations when using shared variables. Currently XME supports three types of locks, 1. Global lock from multiprocess.Manager().Lock(). 2. From user-defined multi-process lock 3. XME.Security module, a new module only supported in XME>=3.3.

```python
import XME.Security as Security
#defind a Security Object
'''
LockType:
Security.DISABLE, disable lock
Security.MUTEX, mutex lock
Security.AUTHORISATION, a group of authorisation operators can access the mutex-type lock
Security.READWRITE, readwrite lock, only an operator can access the mutex-type lock (default)
Security.SPIN, spin lock
'''
sec=Security.Security(LockType=Security.READWRITE) #defind a readwrite lock
'''
Common functions of Security class:
update_lock(LockType) # update a new lock
MuteTime(mutetime) #When a process fails to acquire the lock for the first time, how long does it take to acquire the lock for the second time (only in MUTEX Lock)
authorize(*Operator) #authorize a group of people to access the lock (only AUTHORISATION Lock, default Security().ADMIN)
registe(Operator) #point which one can access the lock (READWRITE lock, default Security().ADMIN)
WaitTime(waittime)# defind the max wait time during acquiring/releasing a lock, if the lock is not acquired within this time, it is determined to be a deadlock or illegal operator, and run the DeadLockFuns.
DeadLockFun(acquire=None,release=None) # defind the deadlock funs, which will be called after detecting a deadlock. Security.DEADLOCKMARK_ONLOCK and Security.DEADLOCKMARK_UNLOCK are returned by default DeadLockFuns.
acquire(Operator,WaitTime=None,DeadLockFun=None) #acquire a lock with Operator, eeturns true if locked successfully
release(Operator,WaitTime=None,DeadLockFun=None) #release a lock, the one who would like to release the lock must be the onlocker, eeturns true if released successfully
'''
if(sec.acquire(sec.ADMIN)): #acquire a lock, with operator the administractor
  #do something about share memory units, like:
  shared_list.append(0)
sec.release(sec.ADMIN) #release a lock, with operator the administractor
```

## 2.2 Monitor Module
XME.Monitor is a new module (version >=3.3) that XME aims to provide for interaction between different programs. This class has a shared memory variable XME.Monitor.\_\_Message\_\_. All processes can implement message passing and RPC (Remote Procedure Call) by accessing XME.Monitor.\_\_Message\_\_. In XME.Monitor, all data will be stored in the form of serializable messages (such as a list, a dictionary, etc.).

usage:

```python
import XME
from XME.Monitor import Monitor
if __name__=="__main__":
  mon=XME.xmem_object("Monitor",Monitor,security=sec) #defind a memory-shared monitor object, the definition of `sec` see section 2.1.1
  a="This is a string message"
  b=XME.xmem_list(["This is a list message"]) #initial a memory-shared list in __Message__
  c=XME.xmem_dict({"key":"This is a list message"}) #initial a memory-shared dict in __Message__
  mon.update({"a":a,"b":b,"c":c},Operator=sec.ADMIN) #usage == dict.update, 
  #Note: In subsequent modification operations by calling mon.update(), the reassignment of the shared memory key may cause the shared memory agent to fail.
  xme.fun(mon,other_parameters)
  '''
  Other common functions in XME.Monitor:
  get(*keys) #like dict[key], if len(keys)==0, returns whole __Message__ (copy version)
  items() #like dict.items()
  delete(*keys, Operator="Undef") #Obtain the lock with the specified operator and perform the data deletion operation. Note: Agent data (shared memory variable data) cannot be recovered once deleted. All elements will be deleted with len(keys)==0
  marshal() #Serialize and Compact __Message__ and get an encrypted binary data
  unmarshal(m_message) #Decrypt, deserialize and uncompact the reciving message
  '''
```

### 2.2.1 RPC (Remote Produce Call) Example
In this section, we will briefly outline the implementation of an RPC function. Before this, we assume that there is some mechanism that enables the sending and receiving of messages between different processes (even from different hosts) (such as sockets, etc.). Here we assume that the receiving function and sending function are **recv()** and **send(msg)**, and are controlled by a public class **Message**

Module Message:

```python
#Message.py
class Message:
  def recv(self):
    #do some work
    pass
  def send(self,msg):
    #do some work
    pass
```

Process in Server:
```python
#Process_server.py
from Message import Message
from XME.Monitor import Monitor
external_function_set={
  # here is a lot of function
}
def Main(self,*args):
  mon=args[0]
  def uncompact_function(m_msg):
    #It is highly recommended that users define this function, how to preprocess and unpack useful data after receiving the message, and update it to the local Monitor.
    tmpmon=Monitor()
    tmpmon.unmarshal(m_msg)
    return <some logic of __Message__>(tmpmon) #i.e., returns unique_mark, target_fun_key, *args, **kwargs
  def compact_function(unique_mark,result):
    tmpmon=Monitor()
    msg=<some logic of __Message__>(unique_mark,result) #i.e., returns unique_mark, target_fun_result
    tmpmon.update(msg)
    return tmpmon.marshal() 
  message=Message(<*someoptions>)
  while True:
    unique_mark,target_fun_key,args,kwargs=uncompact_function(message.recv())
    result=external_function_set[target_fun_key](*args,**kwargs)
    message.send(compact_function(unique_mark,result))
if __name__=="__main__":
  <...some functions...>
```

Process in Client:
```python
#Process_client.py
from Message import Message
from XME.Monitor import Monitor
def Main(self,*args):
  mon=args[0]
  def uncompact_function(m_msg):
    tmpmon=Monitor()
    tmpmon.unmarshal(m_msg)
    return <some logic of __Message__>(tmpmon) #i.e., returns result
  def compact_function(unique_mark,target_fun_key,args=[],**kwargs):
    tmpmon=Monitor()
    msg=<some logic of __Message__>(unique_mark,target_fun_key,args,kwargs) #i.e., returns unique_mark, target_fun_result
    tmpmon.update(msg)
    return tmpmon.marshal() 
  message=Message(<*someoptions>)
  <some logical parses>
  unique_mark=<a logical to get a unique mark>()
  message.send(compact_function(unique_mark,result,args,**kwargs))
  result=uncompact_function(message.recv())
  <some logical parses>
if __name__=="__main__":
  <...some functions...>
```

In this example, when the client process needs the execution result of a certain function from the service process at a certain moment, it will generate a unique identifier, package and encrypt all the information and send it to the service process. When the service process gets the message package, it will decrypt and unpack it, and call the functions and parameters specified by the client process. Finally, the call result and unique identification are packaged and returned to the client process, and the client process will continue to perform the remaining tasks based on the results.

It should be noted that the case shown in this section only provides a general framework of RPC and omits many key steps at each level, such as further information security, reliability, etc. are not considered. But it basically demonstrates the necessary factors to implement RPC. If readers need to engage in RPC development based on XME.Monitor, please design the corresponding functions according to their own needs!

## 2.3 XMEManager
XMEManager is a shared memory lower-level managed class provided by XME. For all developers working with XME, it is recommended to use XMEManager for shared memory operations. XMEManager is a predetermined shared library that is created when an XME object is created. Among them are the value table **\_\_valuetable\_\_** and the buffer table **\_\_Buffer\_Call\_\_**. It also includes the memory-sharing Security module and Monitor module. If you need to use XMEManager, you only need to add a parameter name **XMEManager** to the target function:

```python
import XME
def target_fun(XMEManger=None):
  print(XMEManger.get_str()) #output the status of XMEManager
if __name__=="__main__":
  xme=XME.XME(target_fun,xmemtable={"key":"the initial key-value pairs in __valuetable__"})
  xme.xmem.update({"a list key":XME.xmem_list(["a initial-memory-shared list in __valuetable__"])})
  xme.fun()
```

In the above situation, we assign values to XMEManager.\_\_valuetable\_\_ in two ways. In fact, \_\_valuetable\_\_ will not be an empty table at the beginning even without assignning. It is allocated three memory-shared dicts \_\_STATUS\_\_, \_\_GUARD\_\_, and \_\_XMEM\_\_ at the beginning.

**\_\_STATUS\_\_**: Save the status information of all processes. The process needs to update the status information through XMEManger.status(Operator=None,Status=None).

**\_\_GUARD\_\_**: XMEManger guardian class status (see section **2.3.1**)

**\_\_XMEM\_\_**: Mapping of all built-in functions of XMEManager

Other Functions in XMEManager:
```python
append(fun,Operator=None,**kwargs) # insert a fun_type_value in __Buffer_Call__["GUARD"] with **kwargs by Operator
exec() # exec the first function in __Buffer_Call__, save result in __Buffer_Call__[Operator], and delete it after executing
clean(Operator=None) #del __Buffer_Call__[Operator]
get(Operator=None,MaxWaitTime=0,LoopTime=0.1) #get __Buffer_Call__[Operator] until MaxWaitTime loop by LoopTime
status(Operator=None,status=None) #update process status
get_buffers() #return deepcopy(__Buffer_Call__)
len() #len(__Buffer_Call__["GUARD"])
get_table(*keys) #deepcopy(__valuetable__[*keys])
set(key,value) #__valuetable__[key]=value
items() #return __valuetable__.items()
update(newtable,Operator=None) #__valuetable__.update(newtable)
delete(*keys,Operator=None) #del __valuetable__[*keys]
get_msg(*kets) #return monitor.get(*keys)
update_msg(newmessage,Operator=None) #monitor.update(newmessage,Operator)
delete_msg(*keys,Operator=None) #monitor.delete(*keys,Operator)
copy_msg(Operator=None) #delete_msg(Operator) & update_msg(__valuetable__,Operator)
AllocOperator() #allocate a new operator
```

### 2.3.1 XMEGuard
XMEGuard is a collaborative process class provided by XME for automatically executing the XMEManager.exec function. If readers use XMEManager for function development and have high frequency of operations on shared memory variables and strict lock allocation requirements, it is recommended to use the XMEGuard process and cooperate with XMEManager.append() to implement it. At this time, XMEGuard will automatically host the call to XMEManager.exec to avoid complex lock interaction issues.

```python
import XME,time
class V:
  value=0
  def add(self,value): self.value+=value
  def get(self): return self.value

def fun(*args,XMEManager=None,print=print):
  #dispatch
  XMEManager=args[-2]
  print=args[-1]
  args=args[:-2]

  op=XMEManager.AllocOperator()#allocate a id
  v=XMEManager.get_table("v")
  for i in range(100):
    XMEManager.append(v.add,op,value=1)
  XMEManager.append(XMEManager.get_table("__XMEM__")["Table::update"],value=XME.xmem_dict({"__GUARD__":{"Status":False}})) #stop XMEGuard

if __name__=="__main__":
  xmeguard=XME.XMEGuard()
  '''
  args in XME.XMEGuard():
  ExitTime = 10, if XMEManager.__Buffer_Call__ is still empty after this time, XMEGuard will automatically exit
  LoopTime = 1e-6, If the current loop finds a value in the Buffer table, the time interval until the next check (it is recommended to set a smaller value)
  EmpLoopTime = 1e-1, If the current loop doesn't find any value in the Buffer table, the time interval until the next check (it is recommended to set a larger value)
  VerboseTime = 5, How often to display XMEGuard logs, 0 means never display
  script="", After the XMEGuard main thread is established, what collaboration script needs to be executed (__GUARD__ represents the XMEGuard process object itself)
  '''
  v=XME.xmem_object("Class_V",V)
  xme=XME.XME(fun,xmeguard.Guard,xmemtable={"v":v})
  xme.gfun(xme.Array(range(10)))
  print(xme.xmem.get_table("v").get())
```

### 2.3.2 XME.HeartJump
From the example in 2.3.1 we send an update command to XMEManger to update the status of XMEGuard and stop the XMEGuard process when the process ends (if we don't do this, the program will never stop). But in fact, this approach is risky, because both process A and B may have defined to stop XMEGuard when the process ends, but process A may have stopped XMEGuard after the end but process B has not, thus causing process B to submit to XMEManager The task is not processed, and may even get stuck when process B calls XMEManager.get(). In order to solve this problem, we recommend using the XME.HeartJump class in all processes that call XMEManager and XMEGuard. This class will be Create a thread under the child process to regularly submit a task that updates the status of the current child process. This also ensures that the XMEGuard process will automatically end only when all child processes have ended.

```python
import XME,time
class V:
  value=0
  def add(self,value): self.value+=value
  def get(self): return self.value

def fun(*args,XMEManager=None,print=print):
  #dispatch
  XMEManager=args[-2]
  print=args[-1]
  args=args[:-2]
  op=XMEManager.AllocOperator()#allocate a id
  xmehj=XME.HeartJump(op,XMEManager) #defind a heartjump object
  '''
  args of XME.HeartJump():
  Operator: target process' operator to XMEManager
  XMEManager: the XMEManager object
  LoopTime = 1: heartjump frequency, recommond with a larger value but it should less than XMEGuard.ExitTime 
  '''
  xmehj.start() #start the heart jump
  v=XMEManager.get_table("v")
  for i in range(100):
    XMEManager.append(v.add,op,value=1)
  xmehj.stop() #stop the heart jump, mark this subprocess is end

if __name__=="__main__":
  xmeguard=XME.XMEGuard()
  v=XME.xmem_object("Class_V",V)
  xme=XME.XME(fun,xmeguard.Guard,xmemtable={"v":v})
  xme.gfun(xme.Array(range(10)))
  print(xme.xmem.get_table("v").get())
```

# 3 Unavailable Situation

## 3.1 Open file as parameter or variable in targetfun

For security reasons, Python prohibits multi-process operations on open files pointer, multiprocess.Manager() and it's Lock() object 

```python
#This situation is prohibited in python MP
file=open("filename","w")
xme.fun(file)
file.close()
```

## 3.2 Inline local functions

The Multiprocess module will first serialize all non-proxy objects, copy them and pass them to each sub-process, so make sure that each parameter or function can be serialized. However, this type of function **cannot** be pickled by python MP:

```python
#This situation is prohibited in python MP
def fun():
  def targetfun(x,y): # or targetfun=lambda x,y:x+y
    return x+y
  x=50
  y=range(100)
  xme=XME(targetfun)
  return xme.fun(x,xme.Array(y)) # An error of connot pickle local function will be reported here! ! !
if __name__=="__main__":
  fun()
```
