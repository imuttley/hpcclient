from Queue import Queue
import threading,os

if 'HPCAGENT' in os.environ:
	POSTSERVER="http://127.0.0.1:5984"
	kernel=None
	ME=os.environ['HPCAGENT']
else:
	POSTSERVER="http://localhost:9999"
	kernel=get_ipython().kernel
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
EVNTDEBUG=False
FSDEBUG=False
RJDEBUG=False
REQ=False
QUEUE=False
HPCIO=True
filequeue=Queue()
excludequeue=Queue()
lockvar=threading.Lock()
statsqueue=Queue()

def msgintflog(msg):
	if EVNTDEBUG: print 'event:{0}'.format(msg)

#function to evaluate event
msgintf={'onevnt':msgintflog} 

LOGINNODE='login.marconi.cineca.it'

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

