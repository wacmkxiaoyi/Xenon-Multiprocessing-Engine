# Xenon-Multiprocessing-Engine
Xenon-Multiprocessing-Engine (**XME** thereafter) is a Python interface for process pool establishment, and result collection based on the Multiprocessing module.

Version 3.1
Update: 2023-07-11

Author: Junxiang H. & Weihui L. <br>
Suggestion to: huangjunxiang@mail.ynu.edu.cn
Website: wacmk.cn/com

A multiprocessing interface for python.
You can download the **outdate** package at **"Releases"** in your right hand.

# Install

```shell
pip3 install XME
```

# Useage 

If you want to run the function (**targetfun**) below with XME

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

You should update your main function and call **XME**

```python
from XME import XME
#import XME.XME as XME 
if __name__=="__main__":
  xme=XME(targetfun,pnum=3) #where targetfun is target function, pnum is how many cores you would like to do in this function (default - all cores callable of your computer)
  x=50
  y=np.array(100)
  z=xme.fun(x,xme.Array(y)) # xme.Array class indicates the array y will be detached into pnum parts, and run targetfun eachself
  #For example:
  #core 0, y=: 0 3 6 9 12 ....
  #core 1: 1 4 7 10....
  #core 2: 2 5 8 11....
#result: <tuple>
#>>>(50,51,52,53....,147,148,149)
```

# Logger Output

XME has a built-in log output module. You can add the **print** into targetfun's **parameters' list**, and replace **print** (optional)

```python
def target(x,y,print=print):
  print("x=",x,"y=",y,"x+y",x+y) #useage like built-in function print
```

The default output takes the pid, time and the user-def output in **print**

## Advanced usage of logobj

You can define the **logobj**'s parameters when create a XME object

```python
if __name__=="__main__":
  xme=XME(targetfun,
    do_with_log=True, #if set to False, the logger will be shutdowned (general switch), default True
    print_in_screen=True, #if set to False, the log will not show in your screen (or a terminal)
    logfile=None, #if set to a file (e.g., ***.log), the log will save into this file
    show_version_info=True #if set to False, the version info of XME will be hiden
  )
```

# Unavailabe cases

## Openning fileas a parameter or variable in targetfun

For security reasons, Python prohibits multi-process operations on a openning file!!!!

```python
#This case prohibits in python MP
file=open("filename","w")
xme.fun(file)
file.close()
```

## Inline Local function

This type function **cannot** be pickle of python MP

```python
#This case prohibits in python MP
def fun():
  def targetfun(x,y):
    return x+y
  x=50
  y=range(100)
  xme=XME(targetfun)
  return xme.fun(x,xme.Array(y)) # in here will report an error of connot pickle local function!!!!
if __name__=="__main__":
  fun()
```
