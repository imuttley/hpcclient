""" trick for replace xattr on window system """
from config import *
import thread

XFILE='.xattr'
lockvar=thread.allocate_lock()

def _readxfile():
	try:
		with lockvar:
                	with open (XFILE,'r') as x:
                        	filelistobj=eval(x.read())
			return filelistobj
        except:
                return {}

def getxattr(file,attr):
	if DEBUG: print 'get xattr {0} of {2}'.format(k,v,file)
	try:
		return (listxattr(file))[attr]
	except:
		return {}

def listxattr(file):
	try:
		with lockvar:
			with open(XFILE,'r') as x:
				filelistobj=eval(x.read())
			return filelistobj[file]
	except:
		return {}

def removexattr(file,k):
	obj=_readxfile()
	if DEBUG: print 'remove xattr {0} to {2}'.format(k,v,file)
	try:
		obj[file].pop(k)
		with lockvar:
			with open (XFILE,'w') as x:
             			x.write('{0}'.format(obj))	
	except:
		pass

def setxattr(file,k,v):
	obj=_readxfile()
	if DEBUG: print 'set xattr {0}:{1} to {2}'.format(k,v,file)
	try:
		obj[file].update({k:v})
	except:
		obj.update({file:{k:v}})
	with lockvar:
		with open (XFILE,'w') as x:
			x.write('{0}'.format(obj))

