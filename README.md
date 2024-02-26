# Xenon-Multiprocessing-Engine
Xenon-Multiprocessing-Engine (**XME** thereafter) is a (platform-independent) portable optimization IO intensive interface (**XMESI**) based on **multiprocessing** for process pool operation, supports the most of **serializable-split** operations.

Version 4.2.2
Update: 2024-02-22

Author: Junxiang H. & Weihui L. <br>
Suggestion to: wacmkxiaoyi@gmail.com
Website: wacmk.cn/com

**Update in 4.2: Use security-token communication and thread lock to increase data operation security, and optimize the usage of MPI modules**

**Update in 4.1: The MPI mode blocking calculation function acquire\block is merged into the acquire function (block=True can be specified) as blocking (results are called through the mpi.get() function). Also add broadcast function.**

**New feature in 4.0: A new MPI module based on IO from multiprocess.Pipe is added to enable computing-intensive multi-process programming. (see section 3)**

# Installation

Please make sure the packages/libraries has been installed before installing XME:

1. **os**,**copy**,**time**,**random**,**multiprocessing** ; XME will call those packages to perform process pool control, share variable proxies, etc (basic functions)
2.  **json,hashlib,traceback,threading** ; If you attempt to perform **shared memory proxy** operations through XME, especially manager-guard processes using XME, then these libraries should be included

and follow the blow parse to install:

```shell
pip3 install XME
```

# 1 Standard Interface (XMESI) 

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


# 2 Shared-Memory and XMEManager
## 2.1 Shared-Memory Variables and Objects
XME supports all memory sharing mechanisms of all multiprocess module as variables input to each process (such as Queue, Pipe, Value, Manager and the shared_memory module supported after python 3.8.3). Users can define corresponding types of parameter types to insert into the execution table and achieve target functions. In addition to various proxy variables defined by users based on multiprocessing module, XME also provides a way to define a shared-memory object:

**Note: In XME<4.0, class Object: XME.xmem_object**


```python
from XME.Manager.Object import Object
class Class_Name:
  def __init__(self,*args,**kwargs):
    pass
shared_object=Object("Class_Name",Class_Name,*initargs=*[],**initkwargs=**{}) #defind a shared memory object
#Special note that all attributes in the shared class functions defined according to XME.xmem_object cannot be called directly, and private functions cannot be used, such as __str__, __add__, __get__, etc.
```

Then shared memory variables (e.g., proxy variables) such as shared_list will be inserted into the execution table in the form of proxy addresses and ordinary variable:

key     |     function       |      args

funa   ...    0x00000256    ...     a=shared_list (point to proxy address: 0x00000743),b=xme.Array(range(10))

funa   ...    0x000002a3    ...     a=shared_list (point to proxy address: 0x00000743)


## 2.2 XMEManager
XMEManager is a shared memory low-level managed class provided by XME. For all developers using XME, it is recommended to use the XMEManager for IO-intensive shared memory operations. The XMEManager is a predetermined shared library created when an XME object is created. There are value table **\_\_valuetable\_\_** and buffer table **\_\_Buffer\_Call\_\_**. It also includes a memory sharing security module and a monitoring module. At the same time, the XMEManager object created through **XME.Manager.XMEMBuilder** itself is memory shared, that is to say, the XMEManager referenced by all processes can point to the same memory address.

**Note: In XME<4.0, class XMEManager: XME.XMEManager**

```python
import XME
from XME.Manager import XMEMBuilder
def target_fun(xmem):
  print(xmem.get_str()) #output the status of XMEManager
if __name__=="__main__":
  initialtable={"key":"the initial key-value pairs in __valuetable__"}
  xmem=XMEMBuilder(size=32,**initialtable)
  '''
  size: the size of operator name (see the section 2.1 Security)
  initialtable: the initial key-value pairs in memory-shared dict __valuetable__
  '''
  xme=XME.XME(target_fun)
  xmem.update({"a list key":"value of this key"}) #usage like a dict 
  xme.fun(xmem)
```

In the above situation, we assign values to XMEManager.\_\_valuetable\_\_ in two ways. In fact, \_\_valuetable\_\_ will not be an empty table at the beginning even without assignning. It is allocated three memory-shared dicts \_\_STATUS\_\_, \_\_GUARD\_\_, and \_\_XMEM\_\_ at the beginning.

**\_\_STATUS\_\_**: Save the status information of all processes. The process needs to update the status information through XMEManger.status(Operator=None,Status=None).

**\_\_GUARD\_\_**: XMEManger guardian class status (see section **2.5**)

**\_\_XMEM\_\_**: Mapping of all built-in functions of XMEManager

Other Functions in XME.Manager.XMEManager: (create object manually)
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

## 2.3 Security Module
The problem of reading and writing shared memory variables in multi-process programs usually encounters lock interaction problems that are more troublesome than those in multi-threads. We also strongly recommend using associated locking operations when using shared variables. Currently XME supports three types of locks, 1. Global lock from multiprocess.Manager().Lock(). 2. From user-defined multi-process lock 3. Security module, a new module only supported in XME>=3.3  (**Security object will be created automatically when calling XMEMBuilder to create the XMEManager, and is also memory shared**).

**Note: In XME<4.0, class Security: XME.XMElib.Security**

```python
from XME.Manager.Security import *
#defind a Security Object
'''
LockType:
Security.DISABLE, disable lock
Security.MUTEX, mutex lock
Security.AUTHORISATION, a group of authorisation operators can access the mutex-type lock
Security.READWRITE, readwrite lock, only an operator can access the mutex-type lock (default)
Security.SPIN, spin lock
'''
sec=Security(LockType=READWRITE) #defind a readwrite lock
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

## 2.4 Monitor Module
Monitor is a new module (version >=3.3) of XME designed to provide interaction between different programs (generally processes located on the local computer). This class has a shared memory variable Monitor.\_\_Message\_\_All processes can implement message passing (such as status reporting) and RPC (remote procedure call) by network. In Monitor communication, all data will be stored in the form of serializable messages (via the json module) (such as lists, dictionaries, np.ndarray, etc.). At the same time, all data in Monitor.\_\_Message\_\_ should be able to be serialized by json. The reason why pickle module is not used for serialization and json is used here is to consider the platform-independent feature. (**Monitor object will be created automatically when calling XMEMBuilder to create the XMEManager, and is also memory shared**)

**Note: In XME<4.0, class Monitor: XME.XMElib.Monitor**

usage:

```python
import XME
from XME.Manager.Monitor import Monitor
from XME.Manager.Object import Object
from multiprocessing import Manager
if __name__=="__main__":
  mon=Object("Monitor",Monitor,security=sec) #defind a memory-shared monitor object, the definition of `sec` see section 2.3
  a="This is a string message"
  mm=Manager()
  b=mm.list(["This is a list message"]) #initial a memory-shared list in __Message__
  c=mm.dict({"key":"This is a list message"}) #initial a memory-shared dict in __Message__
  mon.update({"a":a,"b":b,"c":c},Operator=sec.ADMIN) #usage == dict.update, 
  #Note: In subsequent modification operations by calling mon.update(), the reassignment of the shared memory key may cause the shared memory agent to fail.
  xme.fun(mon,**other_parameters)
  '''
  Other common functions in XME.Manager.Monitor:
  get(*keys) #like dict[key], if len(keys)==0, returns whole __Message__ (copy version)
  items() #like dict.items()
  delete(*keys, Operator="Undef") #Obtain the lock with the specified operator and perform the data deletion operation. Note: Agent data (shared memory variable data) cannot be recovered once deleted. All elements will be deleted with len(keys)==0
  marshal() #Serialize and Compact __Message__ and get an encrypted binary data
  unmarshal(m_message) #Decrypt, deserialize and uncompact the reciving message
  '''
```

### 2.4.1 RPC (Remote Produce Call) Example by Monitor Object
In this section, we will provide a brief overview of the RPC functionality over network connections implemented through the Monitor module. Before this, we assume that there is some mechanism to send and receive messages between different hosts (such as sockets, etc., this practice is common in load balancing servers). Here we assume that the receiving function and sending function are **recv()** and **send(msg)**, and are controlled by a public class **Message**

```python
#Message.py
class Message:
  def conn(self,address):
    #do some work to connect the server
    pass
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
from XME.Manager.Monitor import Monitor
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
from XME.Manager.Monitor import Monitor
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
  message.conn(<address of service>)
  <some logical parses>
  unique_mark=<a logical to get a unique mark>()
  message.send(compact_function(unique_mark,result,args,**kwargs))
  result=uncompact_function(message.recv())
  <some logical parses>
if __name__=="__main__":
  <...some functions...>
```

In this example, the client needs to connect to the server firstly. When the client needs the execution result of a certain function from the service at a certain moment, it will generate a unique identifier, package and encrypt all the information and send it to the service. When the service gets the message package, it will decrypt and unpack it, and call the functions and parameters specified by the client. Finally, the call result and unique identification are packaged and returned to the client, and the client will continue to perform the remaining tasks based on the results.

It should be noted that the case shown in this section only provides a general framework of RPC and omits many key steps at each level, such as further information security, reliability, etc. are not considered. But it basically demonstrates the necessary factors to implement RPC. If readers need to engage in RPC development based on Monitor, please design the corresponding functions according to their own needs! 

## 2.5 XME.Manager.Guard
XME.Manager.Guard is a collaborative process class provided by XME for automatically executing the XMEManager.exec function. If readers use XMEManager for function development and have high frequency of operations on shared memory variables and strict lock allocation requirements, it is recommended to use the XME.Manager.Guard process and cooperate with XMEManager.append() to implement it. At this time, XME.Manager.Guard will automatically host the call to XMEManager.exec to avoid complex lock interaction issues. 

**Note 1: XME.Manager.Guard is usually suitable for situations where the frequency of access to shared memory is not so high but there are strict data synchronization requirements.**

**Note 2: In XME<4.0, class Guard: XME.XMEGuard**

```python
import XME,time
from XME.Manager import XMEMBuilder,Guard
from XME.Manager.Object import Object
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
  XMEManager.append(XMEManager.get_table("__XMEM__")["Table::update"],value={"__GUARD__":{"Status":False}}) #stop XMEGuard

if __name__=="__main__":
  v=Object("Class_V",V)
  xmem=XMEMBuilder(v=v)
  xmeguard=Guard()
  xme=XME.XME(fun,xmeguard.Guard)
  '''
  args in XME.Manager.Guard():
  ExitTime = 10, if XMEManager.__Buffer_Call__ is still empty after this time, Guard will automatically exit
  LoopTime = 1e-6, If the current loop finds a value in the Buffer table, the time interval until the next check (it is recommended to set a smaller value)
  EmpLoopTime = 1e-1, If the current loop doesn't find any value in the Buffer table, the time interval until the next check (it is recommended to set a larger value)
  VerboseTime = 5, How often to display Guard logs, 0 means never display
  script="", After the Guard main thread is established, what collaboration script needs to be executed (__GUARD__ represents the Guard process object itself)
  '''
  xme.gfun(xme.Array(range(10)),xmem,garg=(xmem,))
  print(xmem.get_table("v").get())
```

### 2.5.1 HeartJump
From the example in 2.5 we send an update command to XMEManger to update the status of Guard and stop the Guard process when the process ends (if we don't do this, the program will never stop). But in fact, this approach is risky, because both process A and B may have defined to stop Guard when the process ends, but process A may have stopped Guard after the end but process B has not, thus causing process B to submit to XMEManager The task is not processed, and may even get stuck when process B calls XMEManager.get(). In order to solve this problem, we recommend using the XME.HeartJump class in all processes that call XMEManager and Guard. This class will be Create a thread under the child process to regularly submit a task that updates the status of the current child process. This also ensures that the Guard process will automatically end only when all child processes have ended.

**Note: In XME<4.0, class HeartJump: XME.HeartJump**

```python
import XME,time,numpy as np
from XME.Manager import *
from XME.Manager.Object import Object
class V:
  value=np.array([0])
  def add(self,value): self.value+=value
  def get(self): return self.value

def fun(*args,print=print):
  #dispatch
  XMEManager=args[-2]
  print=args[-1]
  args=args[:-2]
  op=XMEManager.AllocOperator()#allocate a id
  xmehj=HeartJump(op,XMEManager)
  '''
  args of XME.Manager.HeartJump():
  Operator: target process' operator to XMEManager
  XMEManager: the XMEManager object
  LoopTime = 1: heartjump frequency, recommond with a larger value but it should less than XMEGuard.ExitTime 
  '''
  xmehj.start()# start the heartjump thread
  v=XMEManager.get_table("v")
  for i in range(100):
    print("i",i)
    XMEManager.append(v.add,op,value=np.array([i]))
  xmehj.stop()

if __name__=="__main__":
  v=Object("Class_V",V)
  xmem=XMEMBuilder(v=v)
  xmeguard=Guard()
  xme=XME.XME(fun,xmeguard.Guard)
  xme.gfun(xme.Array(range(10)),xmem,garg=(xmem,))
  print(xmem.get_table("v").get())
```

# 3 Message Passing Interface (MPI)
In Section 2.4, we gave a simple model of RPC, but message passing and RPC calls through XMEManager.Monitor are not suitable for situations where shared variable access is fast and the size of the data stream increases. At the same time, XMEManager.Monitor is more suitable for the first process connected through the network. For RPC calls from the local process pool (**such as computationally intensive tasks**), XME4.0 provides a new interface designed in accordance with the MPI specification.

In order to facilitate developers to understand how XME.MPI implements RPC, we will provide a detailed overview of the architecture here. First, we consider a simple physical calculation model, which can perform relevant calculation logic by the main function main()

```python
import numpy as np
def distance(p1,p2):
  return np.sum((p2-p1)**2)**0.5
def main():
  points=[np.array([0,0]),np.array([3,0]),np.array([0,4])] #define a triangle
  l01=distance(points[0],points[1])
  l02=distance(points[0],points[2])
  l12=distance(points[1],points[2])
  print(l01**2+l02**2==l12**2 || l01**2+l12**2==l02**2 || l12**2+l02**2==l01**2)
if __name__ == '__main__':
  main()
```

In the above code, we define three points. We will calculate the distance between the three points to determine whether it is a right triangle. We find that we will call the function **distance()** multiple times, based on the idea of parallel computing. We can assume that the **distance** function represents a complex computational logic unit (such as solving differential equations through RK4). At the same time, the parameters used each time distance is called have no substantial relationship with the previous results, so we can bind these three computing units to three different processes. 

computing units    args     Processid

fun1               args1    0

fun1               args2    1

fun2               args3    2

....               ...    .....

This approach is actually similar to the use of the XMESI  introduced in section 1. The difference is that the use of all functions in the **process pool established by the XMESI is completely static**, and it will execute all static stacks defined by developers. But **MPI's call to the process pool is completely dynamic** (can be regarded as a simplified version of XMEManager):

XMESI:  Process initialization - awakening - static stack execution - return result - process shutdown
MPI (logical process):    Process initialization - awakening - dynamic stack loop (insert, execute, return) - process shutdown
    (main process):       Process initialization - awakening - static stack execution -  process shutdown  

***Therefore, XMESI is more suitable for programs with complete structure, while MPI is suitable for situations where you only want to use parallel computing for one or two calculation logics.*** Next, we will use the above example to introduce the use of **XME.MPI**

## 3.1 Creation of MPI Object and Registration of Computing Units
The creation of MPI is similar to the creation of XMESI and has similar creation methods, and what we need when creating is to specify the main function. Also note that process allocation is different from XMESI when using MPI. **The MPI process pool consists of a main process and several logical processes**, while there is no primary-secondary relationship between XMESI processes. Therefore, MPI should allocate at least 2 processes (**pnum>=2**), namely a main process and a logical process. When using XME.MPI, you must add the parameter **XMEMPI** to the main function **main(...)**, which is a derived class from XME.MPI

```python
from XME.MPI import MPI
#... codes from section 3
def distance(p1,p2):
  return np.sum((p2-p1)**2)**0.5
def main(XMEMPI):
  #.... some logical
  XMEMPI.close()
if __name__ == '__main__':
  mpi=MPI(main,pnum=3)#register function "main" as the main function
  mpi["distance"]=distance
  mpi.run(#args of function main
    ) # return's same as the function main's return
```

In the above code, mpi=MPI(main,pnum=3) means creating an XME.MPI object and using 1 main process and 2 logical processes, where **main** means the main function. mpi["distance"]=distance means registering the logical computing unit **distance(...)**.

## 3.2 MPI Logical Computing Unit Call
According to the MPI specification, process A will send the data packet to process B, and process B will parse the data packet and perform related operations, and then send the result back to process A. XME.MPI also implements related functions. It should be noted that the inter-process communication of XME.MPI is limited to the main process and the logical process. Direct communication is not allowed between the logical process and the logical process, so deadlock is avoided to a certain extent. XME.MPI provides two ways to insert stacks into logical computing units. One is blocking (**XME.MPI.block_acquire**) and the other is non-blocking (**XME.MPI.acquire**). They have the same parameters. Developers can use it according to their own needs.

```python
def main(XMEMPI):
  points=[np.array([0,0]),np.array([3,0]),np.array([0,4])]
  bufferpos01=XMEMPI.acquire("distance", args=(points[0],points[1]),block=True)
  bufferpos02=XMEMPI.acquire("distance", args=(points[0],points[2]),to=list(status.keys())[0])
  bufferpos12=XMEMPI.acquire("distance", args=(points[1],points[2]))
  l01=XMEMPI.get(bufferpos01)
  l02=XMEMPI.get(bufferpos02)
  l12=XMEMPI.get(bufferpos12)
  XMEMPI.close()
  #....
```

Both block_acquire and acquire are composed of 3 required parameters and 2 functions involved in logical calculation units. Among them, they must be given the status of the logical process, the connection of the logical process and the target logical computing unit. During this process, XME.MPI will call XME.MPI.\_\_encode\_\_ to serialize the call parameters (fun, \*arg, \*\*kwarg) through pickle, and then pass them to the target logical process. The logical process will deserialize the obtained data. ization, thereby completing the insertion into the stack operation, then executing the relevant logical computing unit, and reserializing the results and returning them to the main process. The difference is that block_acquire will return the execution result at once until the entire logical computing unit is executed, while acquire will allocate a buffer pointer to the result due to non-blocking, and then automatically store the result at the address pointed to by the pointer when the calculation is completed. So acquire will return the pointer corresponding to the address and can be obtained through XME.MPI.get (blocking). The size of the buffer can be set by specifying the mpi_buffer_size parameter when creating the XME.MPI object. The default is 255. The parameter to points to one of the XME.MPI logical processes corresponding to the keys of status and conns. It can also be used by XME.MPI to automatically search for idle logical processes (ANY\_PROCESS)

MPI should be closed after all stack operations are completed (**mpi.close(XMEMPI,to=ALL\_PROCESSES)**), otherwise all logical processes will continue to execute and form a deadlock. The parameter to points to one of the XME.MPI logical processes corresponding to the keys of status and conns. It can also be used by XME.MPI to automatically search for idle logical processes (ALL\_PROCESSES)

## 3.3 Example Usage of XME.MPI
In this section we will introduce a probabilistic way to find pi. We assume that there are N small balls, and this small ball will fall into a box with length and width [-r, r]. We assume that the number of small balls falling into a circle with radius r is n, then it is not difficult to prove that pi=4\*n/N. The following will be based on this theory, through XME.MPI, and create a thread for loading results from the buffer regularly.

Test sample (i7-13700kf):

nums=10\*\*8

subnums=10\*\*6

pnum=1 (no XME mode), calculation time: 35s

pnum=8 (7 logical processes), calculation time: 6s

```python
# Xenon-Multiprocessing-Engine
Xenon-Multiprocessing-Engine (**XME** thereafter) is a (platform-independent) portable optimization IO intensive interface (**XMESI**) based on **multiprocessing** for process pool operation, supports the most of **serializable-split** operations.

Version 4.2.1
Update: 2024-02-21

Author: Junxiang H. & Weihui L. <br>
Suggestion to: wacmkxiaoyi@gmail.com
Website: wacmk.cn/com

**Update in 4.2: Use security-token communication and thread lock to increase data operation security, and optimize the usage of MPI modules**

**Update in 4.1: The MPI mode blocking calculation function acquire\block is merged into the acquire function (block=True can be specified) as blocking (results are called through the mpi.get() function). Also add broadcast function.**

**New feature in 4.0: A new MPI module based on IO from multiprocess.Pipe is added to enable computing-intensive multi-process programming. (see section 3)**

# Installation

Please make sure the packages/libraries has been installed before installing XME:

1. **os**,**copy**,**time**,**random**,**multiprocessing** ; XME will call those packages to perform process pool control, share variable proxies, etc (basic functions)
2.  **json,hashlib,traceback,threading** ; If you attempt to perform **shared memory proxy** operations through XME, especially manager-guard processes using XME, then these libraries should be included

and follow the blow parse to install:

```shell
pip3 install XME
```

# 1 Standard Interface (XMESI) 

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


# 2 Shared-Memory and XMEManager
## 2.1 Shared-Memory Variables and Objects
XME supports all memory sharing mechanisms of all multiprocess module as variables input to each process (such as Queue, Pipe, Value, Manager and the shared_memory module supported after python 3.8.3). Users can define corresponding types of parameter types to insert into the execution table and achieve target functions. In addition to various proxy variables defined by users based on multiprocessing module, XME also provides a way to define a shared-memory object:

**Note: In XME<4.0, class Object: XME.xmem_object**


```python
from XME.Manager.Object import Object
class Class_Name:
  def __init__(self,*args,**kwargs):
    pass
shared_object=Object("Class_Name",Class_Name,*initargs=*[],**initkwargs=**{}) #defind a shared memory object
#Special note that all attributes in the shared class functions defined according to XME.xmem_object cannot be called directly, and private functions cannot be used, such as __str__, __add__, __get__, etc.
```

Then shared memory variables (e.g., proxy variables) such as shared_list will be inserted into the execution table in the form of proxy addresses and ordinary variable:

key     |     function       |      args

funa   ...    0x00000256    ...     a=shared_list (point to proxy address: 0x00000743),b=xme.Array(range(10))

funa   ...    0x000002a3    ...     a=shared_list (point to proxy address: 0x00000743)


## 2.2 XMEManager
XMEManager is a shared memory low-level managed class provided by XME. For all developers using XME, it is recommended to use the XMEManager for IO-intensive shared memory operations. The XMEManager is a predetermined shared library created when an XME object is created. There are value table **\_\_valuetable\_\_** and buffer table **\_\_Buffer\_Call\_\_**. It also includes a memory sharing security module and a monitoring module. At the same time, the XMEManager object created through **XME.Manager.XMEMBuilder** itself is memory shared, that is to say, the XMEManager referenced by all processes can point to the same memory address.

**Note: In XME<4.0, class XMEManager: XME.XMEManager**

```python
import XME
from XME.Manager import XMEMBuilder
def target_fun(xmem):
  print(xmem.get_str()) #output the status of XMEManager
if __name__=="__main__":
  initialtable={"key":"the initial key-value pairs in __valuetable__"}
  xmem=XMEMBuilder(size=32,**initialtable)
  '''
  size: the size of operator name (see the section 2.1 Security)
  initialtable: the initial key-value pairs in memory-shared dict __valuetable__
  '''
  xme=XME.XME(target_fun)
  xmem.update({"a list key":"value of this key"}) #usage like a dict 
  xme.fun(xmem)
```

In the above situation, we assign values to XMEManager.\_\_valuetable\_\_ in two ways. In fact, \_\_valuetable\_\_ will not be an empty table at the beginning even without assignning. It is allocated three memory-shared dicts \_\_STATUS\_\_, \_\_GUARD\_\_, and \_\_XMEM\_\_ at the beginning.

**\_\_STATUS\_\_**: Save the status information of all processes. The process needs to update the status information through XMEManger.status(Operator=None,Status=None).

**\_\_GUARD\_\_**: XMEManger guardian class status (see section **2.5**)

**\_\_XMEM\_\_**: Mapping of all built-in functions of XMEManager

Other Functions in XME.Manager.XMEManager: (create object manually)
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

## 2.3 Security Module
The problem of reading and writing shared memory variables in multi-process programs usually encounters lock interaction problems that are more troublesome than those in multi-threads. We also strongly recommend using associated locking operations when using shared variables. Currently XME supports three types of locks, 1. Global lock from multiprocess.Manager().Lock(). 2. From user-defined multi-process lock 3. Security module, a new module only supported in XME>=3.3  (**Security object will be created automatically when calling XMEMBuilder to create the XMEManager, and is also memory shared**).

**Note: In XME<4.0, class Security: XME.XMElib.Security**

```python
from XME.Manager.Security import *
#defind a Security Object
'''
LockType:
Security.DISABLE, disable lock
Security.MUTEX, mutex lock
Security.AUTHORISATION, a group of authorisation operators can access the mutex-type lock
Security.READWRITE, readwrite lock, only an operator can access the mutex-type lock (default)
Security.SPIN, spin lock
'''
sec=Security(LockType=READWRITE) #defind a readwrite lock
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

## 2.4 Monitor Module
Monitor is a new module (version >=3.3) of XME designed to provide interaction between different programs (generally processes located on the local computer). This class has a shared memory variable Monitor.\_\_Message\_\_All processes can implement message passing (such as status reporting) and RPC (remote procedure call) by network. In Monitor communication, all data will be stored in the form of serializable messages (via the json module) (such as lists, dictionaries, np.ndarray, etc.). At the same time, all data in Monitor.\_\_Message\_\_ should be able to be serialized by json. The reason why pickle module is not used for serialization and json is used here is to consider the platform-independent feature. (**Monitor object will be created automatically when calling XMEMBuilder to create the XMEManager, and is also memory shared**)

**Note: In XME<4.0, class Monitor: XME.XMElib.Monitor**

usage:

```python
import XME
from XME.Manager.Monitor import Monitor
from XME.Manager.Object import Object
from multiprocessing import Manager
if __name__=="__main__":
  mon=Object("Monitor",Monitor,security=sec) #defind a memory-shared monitor object, the definition of `sec` see section 2.3
  a="This is a string message"
  mm=Manager()
  b=mm.list(["This is a list message"]) #initial a memory-shared list in __Message__
  c=mm.dict({"key":"This is a list message"}) #initial a memory-shared dict in __Message__
  mon.update({"a":a,"b":b,"c":c},Operator=sec.ADMIN) #usage == dict.update, 
  #Note: In subsequent modification operations by calling mon.update(), the reassignment of the shared memory key may cause the shared memory agent to fail.
  xme.fun(mon,**other_parameters)
  '''
  Other common functions in XME.Manager.Monitor:
  get(*keys) #like dict[key], if len(keys)==0, returns whole __Message__ (copy version)
  items() #like dict.items()
  delete(*keys, Operator="Undef") #Obtain the lock with the specified operator and perform the data deletion operation. Note: Agent data (shared memory variable data) cannot be recovered once deleted. All elements will be deleted with len(keys)==0
  marshal() #Serialize and Compact __Message__ and get an encrypted binary data
  unmarshal(m_message) #Decrypt, deserialize and uncompact the reciving message
  '''
```

### 2.4.1 RPC (Remote Produce Call) Example by Monitor Object
In this section, we will provide a brief overview of the RPC functionality over network connections implemented through the Monitor module. Before this, we assume that there is some mechanism to send and receive messages between different hosts (such as sockets, etc., this practice is common in load balancing servers). Here we assume that the receiving function and sending function are **recv()** and **send(msg)**, and are controlled by a public class **Message**

```python
#Message.py
class Message:
  def conn(self,address):
    #do some work to connect the server
    pass
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
from XME.Manager.Monitor import Monitor
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
from XME.Manager.Monitor import Monitor
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
  message.conn(<address of service>)
  <some logical parses>
  unique_mark=<a logical to get a unique mark>()
  message.send(compact_function(unique_mark,result,args,**kwargs))
  result=uncompact_function(message.recv())
  <some logical parses>
if __name__=="__main__":
  <...some functions...>
```

In this example, the client needs to connect to the server firstly. When the client needs the execution result of a certain function from the service at a certain moment, it will generate a unique identifier, package and encrypt all the information and send it to the service. When the service gets the message package, it will decrypt and unpack it, and call the functions and parameters specified by the client. Finally, the call result and unique identification are packaged and returned to the client, and the client will continue to perform the remaining tasks based on the results.

It should be noted that the case shown in this section only provides a general framework of RPC and omits many key steps at each level, such as further information security, reliability, etc. are not considered. But it basically demonstrates the necessary factors to implement RPC. If readers need to engage in RPC development based on Monitor, please design the corresponding functions according to their own needs! 

## 2.5 XME.Manager.Guard
XME.Manager.Guard is a collaborative process class provided by XME for automatically executing the XMEManager.exec function. If readers use XMEManager for function development and have high frequency of operations on shared memory variables and strict lock allocation requirements, it is recommended to use the XME.Manager.Guard process and cooperate with XMEManager.append() to implement it. At this time, XME.Manager.Guard will automatically host the call to XMEManager.exec to avoid complex lock interaction issues. 

**Note 1: XME.Manager.Guard is usually suitable for situations where the frequency of access to shared memory is not so high but there are strict data synchronization requirements.**

**Note 2: In XME<4.0, class Guard: XME.XMEGuard**

```python
import XME,time
from XME.Manager import XMEMBuilder,Guard
from XME.Manager.Object import Object
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
  XMEManager.append(XMEManager.get_table("__XMEM__")["Table::update"],value={"__GUARD__":{"Status":False}}) #stop XMEGuard

if __name__=="__main__":
  v=Object("Class_V",V)
  xmem=XMEMBuilder(v=v)
  xmeguard=Guard()
  xme=XME.XME(fun,xmeguard.Guard)
  '''
  args in XME.Manager.Guard():
  ExitTime = 10, if XMEManager.__Buffer_Call__ is still empty after this time, Guard will automatically exit
  LoopTime = 1e-6, If the current loop finds a value in the Buffer table, the time interval until the next check (it is recommended to set a smaller value)
  EmpLoopTime = 1e-1, If the current loop doesn't find any value in the Buffer table, the time interval until the next check (it is recommended to set a larger value)
  VerboseTime = 5, How often to display Guard logs, 0 means never display
  script="", After the Guard main thread is established, what collaboration script needs to be executed (__GUARD__ represents the Guard process object itself)
  '''
  xme.gfun(xme.Array(range(10)),xmem,garg=(xmem,))
  print(xmem.get_table("v").get())
```

### 2.5.1 HeartJump
From the example in 2.5 we send an update command to XMEManger to update the status of Guard and stop the Guard process when the process ends (if we don't do this, the program will never stop). But in fact, this approach is risky, because both process A and B may have defined to stop Guard when the process ends, but process A may have stopped Guard after the end but process B has not, thus causing process B to submit to XMEManager The task is not processed, and may even get stuck when process B calls XMEManager.get(). In order to solve this problem, we recommend using the XME.HeartJump class in all processes that call XMEManager and Guard. This class will be Create a thread under the child process to regularly submit a task that updates the status of the current child process. This also ensures that the Guard process will automatically end only when all child processes have ended.

**Note: In XME<4.0, class HeartJump: XME.HeartJump**

```python
import XME,time,numpy as np
from XME.Manager import *
from XME.Manager.Object import Object
class V:
  value=np.array([0])
  def add(self,value): self.value+=value
  def get(self): return self.value

def fun(*args,print=print):
  #dispatch
  XMEManager=args[-2]
  print=args[-1]
  args=args[:-2]
  op=XMEManager.AllocOperator()#allocate a id
  xmehj=HeartJump(op,XMEManager)
  '''
  args of XME.Manager.HeartJump():
  Operator: target process' operator to XMEManager
  XMEManager: the XMEManager object
  LoopTime = 1: heartjump frequency, recommond with a larger value but it should less than XMEGuard.ExitTime 
  '''
  xmehj.start()# start the heartjump thread
  v=XMEManager.get_table("v")
  for i in range(100):
    print("i",i)
    XMEManager.append(v.add,op,value=np.array([i]))
  xmehj.stop()

if __name__=="__main__":
  v=Object("Class_V",V)
  xmem=XMEMBuilder(v=v)
  xmeguard=Guard()
  xme=XME.XME(fun,xmeguard.Guard)
  xme.gfun(xme.Array(range(10)),xmem,garg=(xmem,))
  print(xmem.get_table("v").get())
```

# 3 Message Passing Interface (MPI)
In Section 2.4, we gave a simple model of RPC, but message passing and RPC calls through XMEManager.Monitor are not suitable for situations where shared variable access is fast and the size of the data stream increases. At the same time, XMEManager.Monitor is more suitable for the first process connected through the network. For RPC calls from the local process pool (**such as computationally intensive tasks**), XME4.0 provides a new interface designed in accordance with the MPI specification.

In order to facilitate developers to understand how XME.MPI implements RPC, we will provide a detailed overview of the architecture here. First, we consider a simple physical calculation model, which can perform relevant calculation logic by the main function main()

```python
import numpy as np
def distance(p1,p2):
  return np.sum((p2-p1)**2)**0.5
def main():
  points=[np.array([0,0]),np.array([3,0]),np.array([0,4])] #define a triangle
  l01=distance(points[0],points[1])
  l02=distance(points[0],points[2])
  l12=distance(points[1],points[2])
  print(l01**2+l02**2==l12**2 || l01**2+l12**2==l02**2 || l12**2+l02**2==l01**2)
if __name__ == '__main__':
  main()
```

In the above code, we define three points. We will calculate the distance between the three points to determine whether it is a right triangle. We find that we will call the function **distance()** multiple times, based on the idea of parallel computing. We can assume that the **distance** function represents a complex computational logic unit (such as solving differential equations through RK4). At the same time, the parameters used each time distance is called have no substantial relationship with the previous results, so we can bind these three computing units to three different processes. 

computing units    args     Processid

fun1               args1    0

fun1               args2    1

fun2               args3    2

....               ...    .....

This approach is actually similar to the use of the XMESI  introduced in section 1. The difference is that the use of all functions in the **process pool established by the XMESI is completely static**, and it will execute all static stacks defined by developers. But **MPI's call to the process pool is completely dynamic** (can be regarded as a simplified version of XMEManager):

XMESI:  Process initialization - awakening - static stack execution - return result - process shutdown
MPI (logical process):    Process initialization - awakening - dynamic stack loop (insert, execute, return) - process shutdown
    (main process):       Process initialization - awakening - static stack execution -  process shutdown  

***Therefore, XMESI is more suitable for programs with complete structure, while MPI is suitable for situations where you only want to use parallel computing for one or two calculation logics.*** Next, we will use the above example to introduce the use of **XME.MPI**

## 3.1 Creation of MPI Object and Registration of Computing Units
The creation of MPI is similar to the creation of XMESI and has similar creation methods, and what we need when creating is to specify the main function. Also note that process allocation is different from XMESI when using MPI. **The MPI process pool consists of a main process and several logical processes**, while there is no primary-secondary relationship between XMESI processes. Therefore, MPI should allocate at least 2 processes (**pnum>=2**), namely a main process and a logical process. When using XME.MPI, you must add the parameter **XMEMPI** to the main function **main(...)**, which is a derived class from XME.MPI

```python
from XME.MPI import MPI
#... codes from section 3
def distance(p1,p2):
  return np.sum((p2-p1)**2)**0.5
def main(XMEMPI):
  #.... some logical
  XMEMPI.close()
if __name__ == '__main__':
  mpi=MPI(main,pnum=3)#register function "main" as the main function
  mpi.run(#args of function main
    ) # return's same as the function main's return

  #usage in short:
  #MPI(main,pnum=3)(...)
```

In the above code, mpi=MPI(main,pnum=3) means creating an XME.MPI object and using 1 main process and 2 logical processes, where **main** means the main function.

## 3.2 MPI Logical Computing Unit Call
According to the MPI specification, process A will send the data packet to process B, and process B will parse the data packet and perform related operations, and then send the result back to process A. XME.MPI also implements related functions. It should be noted that the inter-process communication of XME.MPI is limited to the main process and the logical process. Direct communication is not allowed between the logical process and the logical process, so deadlock is avoided to a certain extent. XME.MPI provides two ways to insert into logical computing command to **task stacks** by **XME.MPI.acquire**. It should be noting that the when all the buffers of XME.MPI are used, the insert procedure is blocking until at least one buffer is available. One is blocking and the other is non-blocking by using parameter **block=True or False (default)**. Developers can use it according to their own needs. 

```python
def main(XMEMPI):
  points=[np.array([0,0]),np.array([3,0]),np.array([0,4])]
  bufferpos01=XMEMPI.acquire(distance, args=(points[0],points[1]),block=True)
  bufferpos02=XMEMPI.acquire(distance, args=(points[0],points[2]),to=list(status.keys())[0])
  bufferpos12=XMEMPI.acquire(distance, args=(points[1],points[2]))
  l01=XMEMPI.get(bufferpos01)
  l02=XMEMPI.get(bufferpos02)
  l12=XMEMPI.get(bufferpos12)
  XMEMPI.close()
  #....
```

Both block_acquire and acquire are composed of 3 required parameters and 2 functions involved in logical calculation units. Among them, they must be given the status of the logical process, the connection of the logical process and the target logical computing unit. During this process, XME.MPI will call XME.MPI.\_\_encode\_\_ to serialize the call parameters (fun, \*arg, \*\*kwarg) through pickle, and then pass them to the target logical process. The logical process will deserialize the obtained data. ization, thereby completing the insertion into the stack operation, then executing the relevant logical computing unit, and reserializing the results and returning them to the main process. The difference is that block_acquire will return the execution result at once until the entire logical computing unit is executed, while acquire will allocate a buffer pointer to the result due to non-blocking, and then automatically store the result at the address pointed to by the pointer when the calculation is completed. So acquire will return the pointer corresponding to the address and can be obtained through XME.MPI.get (blocking). The size of the buffer can be set by specifying the mpi_buffer_size parameter when creating the XME.MPI object. The default is 255. The parameter to points to one of the XME.MPI logical processes corresponding to the keys of status and conns. It can also be used by XME.MPI to automatically search for idle logical processes (ANY\_PROCESS)

MPI should be closed after all stack operations are completed (**mpi.close(XMEMPI,to=ALL\_PROCESSES)**), otherwise all logical processes will continue to execute and form a deadlock. The parameter to points to one of the XME.MPI logical processes corresponding to the keys of status and conns. It can also be used by XME.MPI to automatically search for idle logical processes (ALL\_PROCESSES)

## 3.3 Example Usage of XME.MPI
In this section we will introduce a probabilistic way to find pi. We assume that there are N small balls, and this small ball will fall into a box with length and width [-r, r]. We assume that the number of small balls falling into a circle with radius r is n, then it is not difficult to prove that pi=4\*n/N. The following will be based on this theory, through XME.MPI, and create a thread for loading results from the buffer regularly.

Test sample (i7-13700kf):

nums=10\*\*8

subnums=10\*\*6

pnum=1 (no XME mode), calculation time: 35s

pnum=8 (7 logical processes), calculation time: 6s

```python
from XME.MPI import MPI
from random import uniform
import time,threading,sys
r=1
def scatter(nums):
  result=0
  for i in range(nums):
    if uniform(-r,r)**2+uniform(-r,r)**2<=r**2: result+=1
  return result

def main(nums,subnums=0,XMEMPI=None):
  t0=time.time()
  class res: 
    value=0
    lens=0
  result=res()
  if XMEMPI:
    buffpos=[]
    run=True
    event=threading.Event()
    def autoupdate():
      while run:
        newlens=len(buffpos)
        if result.lens==newlens: event.wait()
        for i in buffpos[result.lens:newlens]: result.value+=XMEMPI.get(i)
        result.lens=newlens
    threading.Thread(target=autoupdate).start()
    for i in range(0,nums,subnums):
      buffpos.append(XMEMPI.acquire(scatter, args=(subnums,)))
      event.set()
    result.value+=scatter(nums%subnums)
    while result.lens<len(buffpos): continue
    XMEMPI.close()
    run=False
    event.set()
  else: result.value=scatter(nums)
  print("pi:",4*result.value/nums)
  print("Time usage:",time.time()-t0)

if __name__ == '__main__':
  nums=100000000
  subnums=10000
  pnum=8
  for i in range(1,len(sys.argv),2):
    if sys.argv[i]=="-n": nums=int(sys.argv[i+1])
    elif sys.argv[i]=="-s": subnums=int(sys.argv[i+1])
    elif sys.argv[i]=="-p": pnum=int(sys.argv[i+1])
  if pnum>=2:
    MPI(main,pnum=pnum)(nums,subnums)
  else:
    main(nums,subnums)
```

# 4 Unavailable Situation


## 4.1 Open file as parameter or variable in targetfun

For security reasons, Python prohibits multi-process operations on open files pointer, multiprocess.Manager() and it's Lock() object 

```python
#This situation is prohibited in python MP
file=open("filename","w")
xme.fun(file)
file.close()
```

## 4.2 Inline local functions
In this section we will outline some objects that cannot be serialized. They are mainly composed of local functions or lambda functions. These objects that cannot be serialized will not be called by XMESI and XME.MPI.

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

# 4 Unavailable Situation


## 4.1 Open file as parameter or variable in targetfun

For security reasons, Python prohibits multi-process operations on open files pointer, multiprocess.Manager() and it's Lock() object 

```python
#This situation is prohibited in python MP
file=open("filename","w")
xme.fun(file)
file.close()
```

## 4.2 Inline local functions
In this section we will outline some objects that cannot be serialized. They are mainly composed of local functions or lambda functions. These objects that cannot be serialized will not be called by XMESI and XME.MPI.

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
