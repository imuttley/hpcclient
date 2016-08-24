"""
example module for remote procedure call with asyncronous response
"""
from Queue import Queue
import os,xmlrpclib,threading

if not 'fermiout' in globals(): fermiout=Queue()
if not 'fermierr' in globals(): fermierr=Queue()
if not 'agentname' in globals(): raise Exception('Agent name not set')

if agentname not "Kuka":
    #"/Users/muttley/fermi/."
    #POSTSERVER="http://192.107.94.227:5984"
    WORKDIR="{0}/fermi/.".format(os.environ.get("HOME"))
else:
    # TODO: postserver with public authenticated access
    #POSTSERVER="http://localhost:5984"
    WORKDIR="{0}/middleware-tn/.".format(os.environ.get("WORK"))

POSTSERVER="http://localhost:5984"
ME=os.environ['USER']
getattachs=[]
pushattachs=[]
DEBUG=False
REQ=True
QUEUE=True
filequeue=Queue()
excludequeue=Queue()
lockvar=threading.Lock()
statsqueue=Queue()

from . import th_dbevent,th_getattach,th_fsevent,th_pushattach,th_syncfs


def printfilequeue():
    for ind in range(excludequeue.qsize()):
        file=excludequeue.get()
        print file
        excludequeue.put(file)


def getattach(files,folder,stats):
    if DEBUG:print "folder {0}/".format(folder)
    lockvar.acquire()
    while not statsqueue.empty():
        statsqueue.get()
    statsqueue.put(stats)
    lockvar.release()
    if True:print "stats: {0}".format(stats)
    for filename in files:
        attrib=files[filename]
        if DEBUG:print "{0} {1} size: {2}".format(filename,attrib['digest'].replace("md5-","md5: "),attrib['length'])
        ttg=th_getattach(filename,folder,stats[filename],attrib)
        getattachs.append(ttg)
        ttg.start()



def log(event,filename,evnt,error):
    if error is not None:
        if DEBUG:print "error: {0}".format(error)
    else:
        if DEBUG:print "{0} {1}".format(filename,evnt)

URL=None
POSTDB="commands"
HANDLE="schedule"
OPERATION="append"
fermisessionid="4f5abbf08000cf9b9948dbf42c003415"
URL=POSTSERVER+"/"+POSTDB+"/_design/"+HANDLE+"/_update/"+OPERATION+"/"+fermisessionid
# input channel
if not 'fermirpc' in globals(): fermirpc=xmlrpclib.ServerProxy(URL)
if not 'th_out' in globals():
	th_out=th_dbevent('fermiout_thread',fermisessionid,'stdout',fermiout)
	th_out.daemon=True
	th_out.start() 
if not 'th_err' in globals():
        th_err=th_dbevent('fermiout_thread',fermisessionid,'stderr',fermierr)
        th_err.daemon=True
        th_err.start() 
if not 'th_fs' in globals():
	th_fs=th_syncfs('fs','1223')
	th_fs.daemon=True
	th_fs.start()
if not 'th_watch' in globals():
	th_watch=th_fsevent()
	th_watch.daemon=True
	th_watch.start()
if not 'th_push' in globals():
    th_push=th_pushattach("webfolder")
    th_push.daemon=True
    th_push.start()

