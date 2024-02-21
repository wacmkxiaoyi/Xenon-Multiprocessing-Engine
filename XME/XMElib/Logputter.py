import datetime
import os
from XME.XMElib import XME_Version
def get_par(args,name,default=None):
	try:
		return args[name]
	except:
		return default
class Logputter:
	logfile=None
	time=True
	msgtype=True
	default_msgtype="Message"
	processing=True
	indent=True
	indent_num=4
	indent_type="-"
	print_in_screen=True
	def __init__(self,logfile=None,show_version_info=True):
		self.logfile=logfile
		self.write_header(show_version_info)
	def write_header(self,show_version_info=True):
		strc="==============================================\n"
		strc+="========Xenon  Multiprocessing  Engine========\n"
		strc+="=================WACMK   Tech=================\n"
		strc+=f"================Version {XME_Version}=================\n"
		strc+="==============================================\n"
		if self.print_in_screen and show_version_info: print(strc)
		if self.logfile!=None:
			file=open(self.logfile,"a")
			file.writelines(strc+"\n")
			file.close()
	def write_log(self,*message,**args):
		strc=""
		msgtype=get_par(args,"msgtype")
		indent=get_par(args,"indent",0)
		pid=get_par(args,"pid",os.getpid())
		if msgtype==None: msgtype=self.default_msgtype
		if self.msgtype and not msgtype: strc+="("+msgtype+")"
		if self.time: strc+=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		if self.processing and pid!=None: strc+="(pid@"+str(pid)+")"
		if strc!="": strc+=":"
		if self.indent:
			for i in range(indent):
				for j in range(self.indent_num): strc+=self.indent_type
		for i in message: strc+=str(i)+" "
		if self.print_in_screen: print(strc)
		if self.logfile!=None:
			file=open(self.logfile,"a")
			file.writelines(strc+"\n")
			file.close()
if __name__=="__main__":
	logobj=Logputter("test.log")
	logobj.write_log("test_log")
