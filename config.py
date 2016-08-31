from Queue import Queue
import threading,os

POSTSERVER="http://localhost:9999"
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

URL=None
POSTDB="commands"
HANDLE="schedule"
OPERATION="append"
HPCSESSIONID="4f5abbf08000cf9b9948dbf42c003415"
URL=POSTSERVER+"/"+POSTDB+"/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID
WORKDIR="{0}/fermi/.".format(os.environ.get("HOME"))
COMMANDPOSTURL=POSTSERVER+"/commands/_design/"+HANDLE+"/_update/"+OPERATION+"/"+HPCSESSIONID
DEFAULTFOLDER="webfolder"
