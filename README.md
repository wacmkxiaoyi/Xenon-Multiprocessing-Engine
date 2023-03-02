# Xenon-Multiprocessing-Engine (XME)

Version 2.1

Author: Junxiang H. & Weihui L. <br>
Suggestion: huangjunxiang@mail.ynu.edu.cn

A multiprocessing interface for python.

You can download the package at **"Releases"** in your right hand.

# How to use XME

## Single function (version > 1.0)

You should unpack XME and copy it to your programe dir at first. If somewhere in your programe you need to import XME for this file

```python
from XME import XME 
# from XME.XME import XME #library version
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
#fun-the function need to be executed, dowithlog- see log output
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

## Multiple functions & AOP (version > 2.0)

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

## Log output

XME has a object to support log output. You can definde **dowithlog=True** when build Executor

In main() function
```python
ex=xme.ex(fun, dowithlog=True)
```

In run(args) function
```python
log=args[-1] #when set dowithlog=True, the last term of args is log output object
log.write_log("This is a log")
```

The log print in your screen in default, you should set anorther value **logfile** if you want to output log in a file. If you dont want to see log in your screen, you should set **print_in_screen=False**.

```python
ex=xme.ex(fun, dowithlog=True,logfile="log.log",print_in_screen=False)
```

The log.write_log also support indent (multiple level) and message type output.

```python
log.write_log("message",indent=(indent level),msgtype="warning")
```

For orther uncommon cases of log object, you can refer to the source code.

## Warning

XME does **not support** sharing-openning file mode (including some relative object, e.g. astropy.io.fits object). For example:

```python
def do(args):
    value,file=args
    file.writeline(value)
def main():
    xme=XME()
    ao=xme.ao(5)
    ao.add_args(range(5))
    file=open("test","a")
    ao.add_common_args(file)
    ex=xme.ex(do)
    ex.build_from_ao(ao)
    file.close()
```

In this case, a error about **"cannot pickle '_io.BufferedReader' object"** will be reported! This is because each process cannot communicate with each orther directly, even through file.

One of the solution is you can operate this object in function **do** (always in write mode),

```python
def do(args):
    value=args[0]
    file=open("test","a")
    file.writeline(value)
    file.close()
def main():
    xme=XME()
    ao=xme.ao(5)
    ao.add_args(range(5))
    ex=xme.ex(do)
    ex.build_from_ao(ao)
```

Anorther solution is you can pickle a non-sharing-openning object (always in read mode),

```python
def do(args):
    print(args[0])
def main():
    file=open("test","r")
    data=file.readlines()
    file.close()
    xme=XME()
    ao=xme.ao(len(data))
    ao.add_args(data)
    ex=xme.ex(do)
    ex.build_from_ao(ao)
```

## Update in version 2.1: Support inner_args mode

Execute mode one: (traditional)

```python
def fun(args):
    pass
if __name__=="__main__":
    xme=XME()
    ao=xme.ao(100)
    ao.add_argscut(range(100))
    ex=xme.ex(fun)
    ex.build_from_ao(ao)
```

In mode one, the function **fun** will be executed for 100 times.

Execute mode two: (support >=2.1)

```python
def fun(args):
    args_div=args[0]
    for i in args_div:
        pass
if __name__=="__main__":
    xme=XME()
    ao=xme.ao(xme.pnum)
    ao.add_argscut(range(100),**inner_args=True**)
    ex=xme.ex(fun)
    ex.build_from_ao(ao)
```

In this case, the function **fun** will be executed for **xme.pnum** times.

However, you should definde the funciton in **fun**.

## Some test files (You can donwload those files in <2.0):
```shell
python XME_test.py
python XME_test2.py
```



 
