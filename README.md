# Xenon-Multiprocessing-Engine
Xenon-Multiprocessing-Engine (**XME** thereafter) is a Python interface for process pool establishment, and result collection based on the Multiprocessing module.

Version 3.2
Update: 2023-10-20

Author: Junxiang H. & Weihui L. <br>
Suggestion to: huangjunxiang@mail.ynu.edu.cn
Website: wacmk.cn/com


# Install

```shell
pip3 install XME
```

# Useage 

If you want to run the following function with XME (**targetfun**)

```python
import numpy as np
def targetfun(x,y):
  return x+y
if __name__=="__main__": #this is necessary in multiprocessing tasks
  x=50
  y=np.array(100)
  z=targetfun(x,y)
  print(z)
```

You should update your main function and import **XME**

```python
from XME import XME
#import XME.XME as XME 
if __name__=="__main__":
  xme=XME(targetfun,pnum=3) #where targetfun is target function, pnum is how many cores you would like to do in this function (default - all cores callable of your computer)
  x=50
  y=np.array(100)
  z=xme.fun(x,xme.Array(y)) # The xme.Array class represents that the array y will be separated into pnum parts and run targetfun separately
  #For example:
  #core 0, y=: 0 3 6 9 12 ....
  #core 1: 1 4 7 10....
  #core 2: 2 5 8 11....
#result: <tuple>
#>>>(50,51,52,53....,147,148,149)
```

***Multi-funs mode*** (e.g., using in socket communications...)

```python
def fun1(*args1):
  pass
def fun2(*args2):
  pass
if __name__=="__main__":
  xme=XME(fun1,fun2,pnum=3) #fun index 0,1
  args1=(...)
  args2=(...)
  z=xme.funs((0,1),(*args1,*args2))#multi-funs mode
```

# Logger Output

XME has a built-in log output module. You can add **print** to targetfun's **argument list** and replace **print** (optional)

```python
def target(x,y,print=print):
  print("x=",x,"y=",y,"x+y",x+y) #useage is similar to the built-in function print
```

Default output takes pid, time and user defined output in **print**

## Advanced usage of logobj

You can define parameters for **logobj** when creating the XME object

```python
if __name__=="__main__":
  xme=XME(targetfun,
    do_with_log=True, #if set to False, the logger will be shutdowned (general switch), default True
    print_in_screen=True, #if set to False, the log will not show in your screen (or a terminal)
    logfile=None, #if set to a file (e.g., ***.log), the log will save into this file
    show_version_info=True #if set to False, the version info of XME will be hiden
  )
```

# Unavailable situation

## Open file as parameter or variable in targetfun

For security reasons, Python prohibits multi-process operations on open files! ! ! !

```python
#This situation is prohibited in python MP
file=open("filename","w")
xme.fun(file)
file.close()
```

## Inline local functions

This type of function **cannot** be pickled by python MP

```python
#This situation is prohibited in python MP
def fun():
  def targetfun(x,y):
    return x+y
  x=50
  y=range(100)
  xme=XME(targetfun)
  return xme.fun(x,xme.Array(y)) # An error of connot pickle local function will be reported here! ! !
if __name__=="__main__":
  fun()
```
