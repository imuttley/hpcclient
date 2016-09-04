""" trick for replace xattr on window system """
from config import *
import thread
import os

XFILE='.xattr'
xlockvar=thread.allocate_lock()

def _readxfile():
	try:
		with xlockvar:
                	with open (XFILE,'r') as x:
                        	filelistobj=eval(x.read())
		[attr for attr in filelistobj.keys() if listxattr(attr)]
		with xlockvar:
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
		with xlockvar:
			with open(XFILE,'r') as x:
				filelistobj=eval(x.read())
		if os.path.exists(file):return filelistobj[file]
		else: 
			filelistobj.pop(file)
			with xlockvar:
                        	with open (XFILE,'w') as x:
                                	x.write('{0}'.format(filelistobj))
                	[msgid for msgid in msgintf if msgintf[msgid](('deletexattr',file))]
			return{}
	except:
		return{}

def removexattr(file,k):
	obj=_readxfile()
	if DEBUG: print 'remove xattr {0} to {2}'.format(k,v,file)
	if os.path.exists(file):
		try:
			obj[file].pop(k)
			with xlockvar:
				with open (XFILE,'w') as x:
             				x.write('{0}'.format(obj))	
			[msgid for msgid in msgintf if msgintf[msgid](('removexattr',file,k))]
		except:
			pass

def setxattr(file,k,v):
	obj=_readxfile()
	if DEBUG: print 'set xattr {0}:{1} to {2}'.format(k,v,file)
	if os.path.exists(file):
		try:
			obj[file].update({k:v})
		except:
			obj.update({file:{k:v}})
		with xlockvar:
			with open (XFILE,'w') as x:
				x.write('{0}'.format(obj))
		[msgid for msgid in msgintf if msgintf[msgid](('setxattr',file,k,v))]

