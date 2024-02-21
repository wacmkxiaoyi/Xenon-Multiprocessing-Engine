#Monitor.py
__version__="1.0"
__author__="WacmkXiaoyi@gmail.com"
__doc__="""
Monitor: Multi process/thread message monitor

Basic data atom: **Message

package needs: json
"""
import copy,json
from multiprocessing import Manager

class Monitor:
	security=None
	def __init__(self,security=None,onlock=lambda op:True,unlock=lambda op:True):
		"""
		update message
		args: 	security 
				onlock (fun), default disable (True)
				unlock (fun), default disable (True)
		"""
		self.__Message__=Manager().dict()
		if security!=None:
			self.security=security
			onlock=security.acquire
			unlock=security.release
		self.update_onlock(onlock)
		self.update_unlock(unlock)
	def __str__(self):
		return self.get_str()
	def get_str(self):
		str00=""
		return f"<class Monitor @ {hex(id(self))}: <Message: {self.__Message__}>; {str00 if self.security==None else self.security.get_str()}>"
	def __getitem__(self,key):
		return self.get(key)
	def get(self,*keys):
		'''
		if self.__onlock__("Reader"): 
			if len(keys)==0:result=self.__Message__
			else: 
				result={}
				for key,value in self.__Message__.items(): result[key]=value
		self.__unlock__("Reader")
		return result
		'''
		if len(keys)==0:result=copy.deepcopy(self.__Message__)
		elif len(keys) ==1 : result=self.__valuetable__[keys[0]]
		else: 
			result={}
			for key,value in self.__Message__.items():
				if key in keys: result[key]=value
		return result
	def items(self):
		'''
		if self.__onlock__("Reader"): result=self.__Message__.items()
		self.__unlock__("Reader")
		return result
		'''
		return self.__Message__.items()
	# lock update
	def update_onlock(self,onlock):
		self.__onlock__=onlock
	def update_unlock(self,unlock):
		self.__unlock__=unlock

	def update(self,newmessage, Operator="Undef"):
		"""
		update message
		args: 	message (dict)
				operator
		"""
		#if Operator=="Reader": return
		if self.__onlock__(Operator): self.__Message__.update(newmessage)
		self.__unlock__(Operator)
	def delete(self,*keys,Operator="Undef"):
		"""
		Delete message by key, default by all keys
		args: 	message (dict)
		"""
		#if Operator=="Reader": return
		if len(keys)==0: keys=self.__Message__.keys()
		if self.__onlock__(Operator): 
			for key in keys: del self.__Message__[key]
		self.__unlock__(Operator)
		
	def __compact_data__(self,b_msg):
		def convert(char):
			char=bin(char)[2:]
			char="0"*((8-len(char)%8)%8)+char
			char=int(char[int(len(char)/2):]+char[:int(len(char)/2)],2)
			return char
		return bytes([convert(cr) for cr in b_msg])
	def marshal(self):
		"""
		Serialize and Marshal to bytes:
		dict -> serialize => string -> encode() => UTF-8 list -> compact() => bytes group
		"""
		'''
		if self.__onlock__("Reader"):result=self.__compact_data__(json.dumps(self.__Message__).encode("utf-8"))
		self.__unlock__("Reader")
		return result
		'''
		return self.__compact_data__(json.dumps(self.__Message__).encode("utf-8"))
	def unmarshal(self,m_message):
		"""
		Unmarshal from Bytes and deserialize
		args: 	marshal message (string)
		"""
		m_message=self.__compact_data__(m_message).decode("utf-8")
		self.update(json.loads(m_message))
if __name__=="__main__":
	def debug():
		mm=Monitor()
		mm.update({"a":str(lambda:"a"),"b":str(lambda x:"b"*x)})
		print(mm,"\n")

		ma=mm.marshal()
		print(ma,"\n")

		mb=Monitor()
		mb.unmarshal(ma)
		print(mb["a"],mb["b"])
	debug()