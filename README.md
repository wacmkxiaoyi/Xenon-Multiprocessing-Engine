# Xenon-Multiprocessing-Engine (XME)

Version 1.2

A multiprocessing interface for python which I used to use it, I call it Xenon Engine because data transport in the code like **X**.

# Guide

## File structure

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
