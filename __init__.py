"""
example module for remote procedure call with asyncronous response
"""

if __name__=='__main__':
	print 'load as module'
	pass


from config import *
from Queue import Queue
import os,xmlrpclib,threading
from sshtunnel import SSHTunnelForwarder as tunnel




#if agentname not "Kuka":
    #"/Users/muttley/fermi/."
    #POSTSERVER="http://192.107.94.227:5984"
#    WORKDIR="{0}/fermi/.".format(os.environ.get("HOME"))
#else:
    # TODO: postserver with public authenticated access
    #POSTSERVER="http://localhost:5984"
#    WORKDIR="{0}/middleware-tn/.".format(os.environ.get("WORK"))

from th_dbevent import *
from th_fsevent import *
from th_pushattach import *
from th_syncfs import *
from . import th_view as marconiview

"""TODO: ask for username and password"""
def definetunnel(user,passwd):
	return tunnel(('login.marconi.cineca.it',22),ssh_password=passwd,ssh_username=user,local_bind_address=('localhost',9999),remote_bind_address=('r000u17l01',5984))
        #return tunnel(('login.marconi.cineca.it',22),ssh_pkey=('.myid/id_rsa'),ssh_username='tnicosia',local_bind_address=('localhost',9999),remote_bind_address=('r000u17l01',5984))

def starttunnel(arg):
        #start tunnel
	if arg[0]=='verifypasswd':
		user=arg[1]
		passwd=arg[2]
		if not 'tunnelconnect' in globals():
                	tunnelconnect=definetunnel(user,passwd)
                	tunnelconnect.start()
msgintf.update({'onlogin':starttunnel})

def printfilequeue():
    for ind in range(excludequeue.qsize()):
        file=excludequeue.get()
        print file
        excludequeue.put(file)


def hpcclientlog(event,filename,evnt,error):
    if error is not None:
        if DEBUG:print "error: {0}".format(error)
    else:
        if DEBUG:print "{0} {1}".format(filename,evnt)


class execute():
	def __init__(self,function,arg):
		self._function=function
		self._arg=arg
	@property
	def result(self):
		try:
			self._function(self._arg)
			return True
		except:
			return False



threads=['tunnelconnect','hpcout','hpcerr','getparams','th_out','th_err','hpcrpc','th_fs','th_watch','th_push']
#result=[k for k in initseq if initseq.k]



#define queue for message
if not 'hpcout' in globals(): hpcout=Queue()
if not 'hpcerr' in globals(): hpcerr=Queue()
#if not 'agentname' in globals(): raise Exception('Agent name not set')


# input channel
if not 'hpcrpc' in globals(): hpcrpc=xmlrpclib.ServerProxy(COMMANDPOSTURL)
if not 'th_out' in globals():
	th_out=th_dbeventlisten('marconistdout_thread',HPCSESSIONID,'stdout',hpcout)
	th_out.daemon=True
	th_out.start() 
if not 'th_err' in globals():
        th_err=th_dbeventlisten('marconistderr_thread',HPCSESSIONID,'stderr',hpcerr)
        th_err.daemon=True
        th_err.start() 
if not 'th_fs' in globals():
	th_fs=th_syncfilesystem('fs','1223')
	th_fs.daemon=True
	th_fs.start()
if not 'th_watch' in globals():
	th_watch=th_fsevent()
	th_watch.daemon=True
	th_watch.start()
if not 'th_push' in globals():
	th_push=th_pushattach(DEFAULTFOLDER)
	th_push.daemon=True
	th_push.start()

