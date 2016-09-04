from Queue import Queue
import threading,os

POSTSERVER="http://localhost:9999"
try:
	ME=os.environ['USER']
except:
	ME='windows'

try:
	HOME=os.environ['HOME']
except:
	HOME='.'

getattachs=[]
pushattachs=[]
DEBUG=False
DBDEBUG=False
EVNTDEBUG=True
FSDEBUG=True
RJDEBUG=False
REQ=False
QUEUE=False
filequeue=Queue()
excludequeue=Queue()
lockvar=threading.Lock()
statsqueue=Queue()

def msgintflog(msg):
	if EVNTDEBUG: print 'event:{0}'.format(msg)

#function to evaluate event
msgintf={'onevnt':msgintflog} 

kernel=get_ipython().kernel

LOGINNODE='192.107.94.227'

URL=None
POSTDB="commands"
HANDLE="schedule"
OPERATION="append"
HPCSESSIONID="4f5abbf08000cf9b9948dbf42c003415"
URL=POSTSERVER+"/"+POSTDB+"/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID

WORKDIR="{0}/fermi/.".format(HOME)

COMMANDPOSTURL=POSTSERVER+"/commands/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID
RUNJOBPOSTURL=POSTSERVER+"/commands/_design/"+HANDLE+"/_update/pbssub/"+HPCSESSIONID
DEFAULTFOLDER="webfolder"

FILEDIR=WORKDIR.replace("/.","/")+DEFAULTFOLDER

