# Xenon-Multiprocessing-Engine (XME)

Version 2.0

A multiprocessing interface for python which I used to use it, I call it Xenon Engine because data transport in the code like **X**.

You can download the package at **"Releases"** in your right hand.

# Guide

New feature: Support different functions and AOPs, change function name build_ao to ao and build_ex to ex.

## How to use XME

### Single function (version > 1.0)

You should unpack XME and copy it to your programe dir at first. If somewhere in your programe you need to import XME for this file

```python
from XME import XME
```

In somewhere you want to call XME, you should create a XME object.

```python
xme=XME()
```

Secondly, you must build a args_set to your tasks, for example there are a function:

```python
def fun(args):
    a,b,c,d=args
    return b**2+2*a*b+c*d
```

If the b=range(30)/15, a=1, c=0.5 and d=5 for each case, the tasks number is len(b)=30. And if you would like to run the cases with 4 processing (default is your cpu_count), a **ArrayOperator object** should be created to store the parameters.

```python
a=1
c=0.5
d=5
#v1.2: xme.build_ao(), v2.0: xme.ao() or xme.build_ao()
#build a ArrayOperator object, 30-tasks numbers, 4-processing numbers
ao=xme.build_ao(30,4) 
b=[]
for i in range(30):
    b.append(i/15)
ao.add_common_args(a) #add a constant arg
ao.add_argscut(b) #add a various arg
ao.add_common_args(args_array=(c,d)) #add a series constant arg
```

Before you run the tasks, you shuld **create a Executor**.

```python
#v1.2: xme.build_ex(), v2.0: xme.ex() or xme.build_ex()
#fun-the function need to be executed, dowithlog- see XMEv1/Executor.py
ex=xme.ex(fun, dowithlog=True) 
```

And then take **ao** into **ex** to build pool

```python
results=ex.build_from_ao(ao) #build pool
ao.result_combine() #result combine
print(ao.results) #results tuple
for result in results:
    print(result) #result for each processing
```

### Multiple functions & AOP (version > 2.0)

You **cannot** establish some pools to realize many functions. For example:

**Incorrect code, do not use!**
```python
ex1.build_from_ao(ao1)
ex2.build_from_ao(ao2)
```

Because the pool establishment processings of ex2 will not start until all subprograms in the pool established by ex1 are completely completed in above code. 

So in XME 1.2, you need to nested use the Executor object or use **fun array** and **ao array** in XME 2.0 to realize it. For example, there are functions fun1 and fun2.

```python
ex=xme.ex((fun1,fun2))
#the Executor object will create two functions in a dict with default function name
#{"fun0":fun1,"fun1":fun2}
#if you want to definde function name by yourself
#ex=xme.ex({"fun1":fun1,"fun2":fun2})
```

After creating Executor object, the ArrayOperator objects have similar form. See code:

```python
ex.build_from_ao((ao1,ao2))
#If len(ao)<len(fun), e.g., fun=(fun0,fun1,fun2,fun3), ao=(ao0,ao1,ao2) => {"fun0":(ao0,),"fun1":(ao1,),"fun2":(ao2,)}
#If len(ao)>len(fun), e.g., fun=(fun0,fun1), ao=(ao0,ao1,ao2)=>{"fun0":(ao0,),"fun1":(ao1,ao2)}
#You can run with a more stringent form:
#ex.build_from_ao({"fun1":ao1,"fun2":ao2})
####################
#If you want to ao1 & ao2 execute with fun1 only
#ex.build_from_ao({"fun1":(ao1,ao2)})
```

### A test file:
```shell
python XME_test.py
```

**==============================File strcture OF OLD VERSION==============================**

## File structure v1.2

### XME.py

This file is the main file of XME, which consists of two objects (in array format): **ArrayOperator** (see section XMEv1/ArrayOperator.py) and **Executor** (see section XMEv1/Executor.py). Actually, you only do with this file in most cases.

XME.py contains a class **XME** with properties:

**aoobj_array** (array, default=[]): The array of ArrayOperator objects.<br>
**exobj_array** (array, default=[]): The array of Executor objects.<br>
**has_been_print** (bool, default=False): When it set to **True**, the header infomation of XME will not be shown in the screen, if you set **dowithlog**=True and **print_in_screen**=True on **build_ex** function. 

And function:

**__init__**:{<br>
  pnum (option, default=cpu_count()), int, how many processing you need<br>
}

**build_ao**:{build a ArrayOperator object<br>
  calnum, int, the tasks number<br>
  pnum (option, default=cpu_count()), int, same as above<br>
}

**build_ex**:{build a Exectuor object<br>
  fun, function, which function you want to execute<br>
  dowithlog (option, default=False), bool, log output open when set to True<br>
  print_in_screen (option, default=True), bool, the log print in screen when set dowithlog to True<br>
  logfile (option, default=None), str, the dir of log<br>
  pnum (option, default=cpu_count()), int, same as above<br>
}

**clean**: reset aoobj_array and exobj_array

### XMEv1/Logputter.py

Logputter is a class to output log and message in the screen and log file during the process. However you must set **dowithlog** to true when build Executor object, if you want to use it.

properties:

  **logfile**, str, None<br>
  **time**, bool, True, print time<br>
  **msgtype**, bool, True, print message type<br>
  **processing**, bool, True, print pid<br>
  **indent**, bool, True, open indent output<br>
  **indent_num**, int, 4, the indent level<br>
  **indent_type**, str, "-", the indent char<br>
  **print_in_screen**, bool, True, same as above<br>
  **module_version_info**, dict, no default value, load from __init__()
 
functions:

**__init__**:{ <br>
  logfile=None<br>
  module_version_info={}<br>
  has_been_print=False<br>
}

**write_header**:{ Output version infomation<br>
  has_been_print=False<br>
}

**write_log**:{ Output a message<br>
  message=""<br>
  pid=0<br>
  indent=0<br>
  msgtype="Message"<br>
}

### XMEv1/ArrayOperator.py

ArrayOperator is a class, used to store args and results for each tasks.

properties:

  **pnum**, int, cpu_count(), same as above<br>
  **results**, list, [], the results of tasks<br>
  **args**, list, [], args of each tasks<br>
  **cal_num**, int, no default value, tasks number
  
functions:

**__init__**:{<br>
  cal_num<br>
  pnum=cpu_count()<br>
}

**add_agrscut**:{ add args from a array, if len(array)<cal_num, args for orther task will be set to default_args<br>
  args<br>
  default_args=None<br>
}

**add_common_args**:{add a (series) constant args<br>
  args=None<br>
  args_array=None<br>
}

**result_combine**: Combine results after finishing tasks.

### XMEv1/Executor.py

Executor object is used to build/run/close a pool

properties:

  **fun**, function, no default, the function need to be executed<br>
	**pnum**, int, cpu_count, same as above<br>
	**results**, list, [], the Pool.Applyset array<br>
	**dowithlog**, bool, False, same as above<br>
	**logfile**, str, None<br>
	**logobj**, Logputter, no default
  
functions:

**do_fun**:{ run self.fun and save result to a Manager.list object<br>
  args=()<br>
  returns=None<br>
}

**add_a_pool**:{ Build a single pool<br>
  args<br>
  returns=None<br>
  close=True
  join=True<br>
}

**build_from_ao**:{ Build pools from a ArrayOperator object<br>
  ao<br>
  close=True<br>
  join=True<br>
  pnum=None<br>
}
 
