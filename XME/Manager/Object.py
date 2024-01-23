from multiprocessing.managers import BaseManager
class __Manager__(BaseManager): pass
def __get_manager__():
	m=__Manager__()
	m.start()
	return m

def Object(class_name,class_type,*initargs,**initkwargs):
	__Manager__.register(class_name,class_type)
	return eval(f"__get_manager__().{class_name}(*initargs,**initkwargs)")