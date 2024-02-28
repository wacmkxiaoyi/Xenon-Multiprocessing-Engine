XME_Version="4.2.5"
@staticmethod
def get_par(args,name,default=None):
	try:
		return args[name]
	except:
		return default

@staticmethod
def tuplize(array):
	if type(array) in (list,tuple, numpy.ndarray):
		result=[]
		for i in array:
			if type(i) in (list, numpy.ndarray): result.append(tuplize(i))
			else: result.append(i)
		return tuple(result)
	return array