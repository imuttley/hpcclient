"""
example module for remote procedure call with asyncronous response
"""
from Queue import Queue
import os,xmlrpclib,threading
if not 'marconiout' in globals(): marconiout=Queue()
if not 'marconierr' in globals(): marconierr=Queue()
#if not 'agentname' in globals(): raise Exception('Agent name not set')

DB=os.environ['dbhost']

# TODO: postserver with public authenticated access
POSTSERVER="http://{0}:5984".format(DB)
WORKDIR="{0}/middleware-tn/.".format(os.environ.get("WORK"))


ME=os.environ['USER']
getattachs=[]
pushattachs=[]
DEBUG=True
REQ=True
QUEUE=True
MARCONISID=os.environ.get("SID")

filequeue=Queue()
excludequeue=Queue()
lockvar=threading.Lock()
statsqueue=Queue()

def printfilequeue():
    for ind in range(excludequeue.qsize()):
        file=excludequeue.get()
        print file
        excludequeue.put(file)



# output post channel
class th_get(threading.Thread):
    import requests,time
    def __init__(self,id,sessionid,db,q):
        super(th_get,self).__init__()
	self.session=sessionid
	self.db=db
	self.queue=q
    def chunck(self,r,*arg,**kwarg):
	for line in r.iter_lines():
	    try:
		if (len(line)>1):
                	jsonresp=eval(line)
                	#NO-LOCK-WAIT
			self.queue.put(jsonresp['doc']['post'].replace("\n",""),False)
            except Exception as e:
                #print e
		pass
    def run(self):
        handle="_changes"
        feed="continuous"
        heartbeat="6000"
        includedocs="true"
        since="now"
        filter="session/filter"
        url=POSTSERVER+"/"+self.db+"/"+handle+"?feed="+feed+"&heartbeat="+heartbeat+"&include_docs="+includedocs+"&id="+self.session
        try:
            self.requests.get(url,stream=False,hooks=dict(response=self.chunck))
        except Exception as e:
            self.time.sleep(10)
            self.run()
# TODO empty queue response for new command event


# filesystem syncs thread
class th_pushattach(threading.Thread):
    import couchdb,os,requests,base64,mimetypes
    from hashlib import md5
    import xattr
    def __init__(self,folder):
        super(th_pushattach,self).__init__()
        #self.filename=filename
        self.folder=folder
    def run(self):
        while True:
                #lockvar.acquire()
                self.filename=filequeue.get(True)
                #lockvar.release()
                srcdir=WORKDIR.replace("/.","")+"/"+self.folder
                srcfile=srcdir+"/"+self.filename
                # TODO delete my files from db stat
                try:
                    if self.os.stat(srcfile).st_size<1:continue
                except Exception as e:
                    print "{0} must be deleted TODO".format(self.filename)
                
                if QUEUE: print "send {0}".format(srcfile)
                dsturl=POSTSERVER+"/folders/"+self.folder
                if DEBUG: print "{0}->{1}".format(srcfile,dsturl)
                sync=False
                self.filestat={self.filename:{"author":ME,"comment":"created from {0}".format(ME),"mtime":"now"}}
                try:
                    req=self.requests.get(dsturl)
                    jsoncontent=eval(req.content.replace("true","True").replace("false","False"))
                    #print jsoncontent
                    if jsoncontent.has_key("stats"):
                        jsonstats=(jsoncontent['stats'])
                        jsonstats.update(self.filestat)
                    else:
                        jsonstats=self.filestat
                    rev=req.headers['ETag'].replace("\"","")
                    with open(srcfile,"rb") as fhnd:
                        filedata=(fhnd.read())
                    self.mimetypes.init()
                    filecontenttype, encode=self.mimetypes.guess_type(srcfile)
                    jsonobj={"_attachments":{self.filename:{"content_type":filecontenttype,"data":filedata}}}
                    headers={"Content-Transfer-Encoding": "base64","Content-Type":filecontenttype,"If-Match":rev}
                    data=str(jsonobj).replace("\'","\"")
                    url=dsturl+"/"+self.filename
                    req=self.requests.put(url,headers=headers,data=filedata)
                    if REQ:print "attachment send, response:{0}".format(req)
                    if req.status_code != 409 :
                        updateurl=POSTSERVER+"/folders/_design/folder/_update/append/"+self.folder
                        if DEBUG:print updateurl
                        req=self.requests.put(updateurl+"?filename="+self.filename+"&author="+ME+"&comment=none")
                        if REQ:print req.text
                except Exception as e:
                    if DEBUG:print "pushattch exception  {0}".format(e)

class th_getattach(threading.Thread):
    import os,requests,base64
    from hashlib import md5
    import xattr
    def __init__(self,filename,folder,stat,attrib):
        super(th_getattach,self).__init__()
        self.filename=filename
        self.folder=folder
        self.stat=stat
        self.attrib=attrib
    def run(self):
        dstdir=WORKDIR.replace("/.","")+"/"+self.folder
        dstfile=dstdir+"/"+self.filename
        srcurl=POSTSERVER+"/folders/"+self.folder+"/"+self.filename
        if DEBUG:print "{0}->{1}".format(srcurl,dstfile)
        exists=(os.path.exists(dstfile))
        sync=False
        if self.stat['author']!=ME:
            if exists:
                try:
                    sizesync=(self.attrib['length']!=self.os.stat(dstfile).st_size)
                    #if DEBUG:print "{0} calculate: {1} stat: {2}\n".format(dstfile,self.xattr.getxattr(dstfile,"user.md5"),self.attrib['digest'].replace("md5-",""))
                    md5sync=False
                		#=str(self.xattr.getxattr(dstfile,"user.md5"))!=str(self.attrib['digest'].replace("md5-",""))
               			 #if (md5sync&DEBUG): print "md5 differs!"
				#print "stat:{0} xattr:{1}".format(self.stat['author'],self.xattr.getxattr(dstfile,"user.author"))
                    authsync=self.xattr.getxattr(dstfile,"user.author")!=self.stat['author']
                    if (authsync&DEBUG): print "{0} author {1} download".format(self.filename,self.stat['author'])
                    sync=sizesync|md5sync|authsync
                except Exception as e:
                    if DEBUG:print e
                    sync=True
        if ((not exists)|(sync)):
            try:
                self.os.makedirs(dstdir)
            except Exception as e:
                pass
            if DEBUG:print "exclude {0} for upload".format(self.filename)

            with open(dstfile,"wb") as fhnd:
                res=self.requests.get(srcurl,stream=True)
                if res.ok:
                    md5sum=self.md5()
                    for chunck in res.iter_content(1024*10):
                        md5sum.update(chunck)
                        fhnd.write(chunck)
                    fhnd.flush()
                    self.xattr.setxattr(dstfile,'user.md5',self.base64.b64encode(md5sum.digest()))
                    self.xattr.setxattr(dstfile,'user.author',self.stat['author'])
                    self.xattr.setxattr(dstfile,'user.comment',self.stat['comment'])
            if DEBUG:print '{0} writed'.format(self.filename)


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


# from db to host
class th_syncfilesystem(threading.Thread):
    import pyuv,requests,time
    def __init__(self,id,sessionid):
        super(th_syncfilesystem,self).__init__()
    def getfilename(self,r,*arg,**kwarg):
	    for line in r.iter_lines():
            	if len(line)>2:
                	try:
                    		tr=line.replace("true","True").replace("false","False")
                    		jsonresp=eval(tr)
                    		doc=jsonresp['doc']
                    		if doc.has_key("_attachments"):
                        		getattach(doc['_attachments'],doc['_id'],doc['stats'])
				#print "folder {0} filename {1}".format(doc['_id'],doc['_attachments'])
				#for files in jsonresp['doc']['_attachments']:
				#	getattach(filename)
				#transfer file and set attr user.author
                	except Exception as e:
                    		if DEBUG:print e
                    		pass
		#else:
		#	print "heartbeat"
    def run(self):
        db="folders"
        handle="_changes"
        feed="continuous"
        heartbeat="16000"
        includedocs="true"
        since="now"
        filter="dimension/filter"
        url=POSTSERVER+"/"+db+"/"+handle+"?feed="+feed+"&heartbeat="+heartbeat+"&include_docs="+includedocs
        try:
            self.requests.get(url,stream=False,hooks=dict(response=self.getfilename))
        except Exception as e:
            self.time.sleep(10)
            self.run()

# from host --> db
class th_fsevent(threading.Thread):
    import pyuv,os,xattr
    
    def __init__(self):
        super(th_fsevent,self).__init__()
        # filestate dict: { filename(string):[events..](array)}
        self.filestate={}
    def fsprocess(self,event,filename,evnt,error):
        if error is not None:
            if DEBUG:print "error: {0}".format(error)
            pass
        file=WORKDIR.replace("/.","/")+"webfolder/"+filename
        #filequeue.put(filename)
        #if DEBUG:print "file {0} {1}".format(filename,evnt)
        lockvar.acquire()
        stat=statsqueue.get()
        if not stat.has_key(filename):
            append=True
        else:
            append=(stat[filename]['author']==ME)
        statsqueue.put(stat)
        lockvar.release()
        if evnt:
            exists=self.os.path.exists(file)
            if exists:
                if DEBUG: print "{0}: created".format(filename)
                # who create, me or not ?!
                #LOCK
                if not append:print "excluded {0}".format(filename)
            else:
                if DEBUG: print "{0}: deleted".format(filename)
            try:
                self.xattr.getxattr(file,'user.author')
            except Exception as e:
                if append:
                    #lockvar.acquire()
                    for ind in range(filequeue.qsize()):
                        upload=filequeue.get()
                        if upload==filename:break
                        filequeue.put(upload)
                    filequeue.put(filename)
                    #lockvar.release()
                if DEBUG:print "fsevent exception {0}".format(e)
                if DEBUG:print "{0} not have xattr user.author, push to db".format(filename)
                #if QUEUE: print "{0} events {1}".format(filename,self.filestate[filename])
            finally:
                pass
        else:
            if DEBUG:print "{1} : {0} ".format(event,filename)
    def run(self):
        self.uvloop=self.pyuv.Loop.default_loop()
        self.fsevent=self.pyuv.fs.FSEvent(self.uvloop)
        self.fsevent.start(WORKDIR.replace("/.","/")+"webfolder",0,self.fsprocess)
        self.uvloop.run()

def log(event,filename,evnt,error):
    if error is not None:
        if DEBUG:print "error: {0}".format(error)
    else:
        if DEBUG:print "{0} {1}".format(filename,evnt)

URL=None
POSTDB="commands"
HANDLE="schedule"
OPERATION="append"
URL=POSTSERVER+"/"+POSTDB+"/_design/"+HANDLE+"/_update/"+OPERATION+"/"+MARCONISID
# input channel
if not 'marconirpc' in globals(): marconirpc=xmlrpclib.ServerProxy(URL)
if not 'th_out' in globals():
	th_out=th_get('marconiout_thread',MARCONISID,'stdout',marconiout)
	th_out.daemon=True
	th_out.start() 
if not 'th_err' in globals():
        th_err=th_get('marconiout_thread',MARCONISID,'stderr',marconierr)
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
    th_push=th_pushattach("webfolder")
    th_push.daemon=True
    th_push.start()

