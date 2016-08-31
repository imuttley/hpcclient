"""
example module for remote procedure call with asyncronous response
"""

if __name__=='__main__':
	print 'load as module'
	pass


from config import *
from Queue import Queue
import os,xmlrpclib,threading
imoprt sshtunnel as tunnel


if agentname not "Kuka":
    #"/Users/muttley/fermi/."
    #POSTSERVER="http://192.107.94.227:5984"
    WORKDIR="{0}/fermi/.".format(os.environ.get("HOME"))
else:
    # TODO: postserver with public authenticated access
    #POSTSERVER="http://localhost:5984"
    WORKDIR="{0}/middleware-tn/.".format(os.environ.get("WORK"))

from th_dbevent import *
from th_fsevent import *
from th_pushattach import *
from th_syncfs import *
from . import th_view as marconiview

"""TODO: ask for username and password"""
def starttunnel():
        server=tunnel(('login.marconi.cineca.it',22),ssh_pkey=('$HOME/.ssh/id_rsa'),ssh_username='tnicosia',local_bind_address=('localhost',9999),remote_bind_address=('r000u17l01',5984))
        server.start()

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

#start tunnel
if not 'tunnelconnect' in globals(): 
	tunnelconnect=starttunnel()
	tunnelconnect.start()

#define queue for message
if not 'hpcout' in globals(): hpcout=Queue()
if not 'hpcerr' in globals(): hpcerr=Queue()
if not 'agentname' in globals(): raise Exception('Agent name not set')


# input channel
if not 'fermirpc' in globals(): fermirpc=xmlrpclib.ServerProxy(COMMANDPOSTURL)
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

