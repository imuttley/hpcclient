from Queue import Queue
import threading,os

POSTSERVER="http://localhost:9999"
ME=os.environ['USER']
getattachs=[]
pushattachs=[]
DEBUG=False
DBDEBUG=False
EVNTDEBUG=False
RJDEBUG=False
REQ=True
QUEUE=True
filequeue=Queue()
excludequeue=Queue()
lockvar=threading.Lock()
statsqueue=Queue()

def msgintflog(msg):
	if EVNTDEBUG: print 'event:{0}'.format(msg)

#function to evaluate for event
msgintf={'onevnt':msgintflog} 

kernel=get_ipython().kernel

URL=None
POSTDB="commands"
HANDLE="schedule"
OPERATION="append"
HPCSESSIONID="4f5abbf08000cf9b9948dbf42c003415"
URL=POSTSERVER+"/"+POSTDB+"/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID
WORKDIR="{0}/fermi/.".format(os.environ.get("HOME"))
COMMANDPOSTURL=POSTSERVER+"/commands/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID
RUNJOBPOSTURL=POSTSERVER+"/commands/_design/"+HANDLE+"/_update/pbssub/"+HPCSESSIONID
DEFAULTFOLDER="webfolder"
