""" push file from file system to _attachment in db """
from config import *

# filesystem syncs thread
class th_pushattach(threading.Thread):
    import os,requests,base64,mimetypes
    from hashlib import md5
    import myxattr as xattr

    def __init__(self,folder):
        super(th_pushattach,self).__init__()
        #self.filename=filename
        self.folder=folder
    def delete(self,localfile):
	dsturl=POSTSERVER+"/folders/"+self.folder
	try:
		filename=localfile.split('/').pop()
		req=self.requests.get(dsturl)
		jsoncontent=eval(req.content.replace("true","True").replace("false","False"))
		rev=req.headers['ETag'].replace("\"","")
		headers={"If-Match":rev}
		url=dsturl+"/"+filename
		req=self.requests.delete(url,headers=headers)
		if REQ:print "attachment delete, response:{0}".format(req)
    		if req.status_code != 409 :
                        deleteurl=POSTSERVER+"/folders/_design/folder/_update/deletea/"+self.folder
                        if DEBUG:print deleteurl
                        req=self.requests.put(deleteurl+"?filename="+filename)
                        if REQ:print req.text
                        self.xattr.removexattr(localfile,'user.sync')
		#TODO remove db stat
	except Exception as e:
		if REQ:print "exception on requests:".format(e)
    def put(self,localfile):
	if QUEUE: print "send {0}".format(localfile)
	dsturl=POSTSERVER+"/folders/"+self.folder
	if QUEUE: print "{0}->{1}".format(localfile,dsturl)
	sync=False
	filename=localfile.split('/').pop()
	self.filestat={filename:{"author":ME,"comment":"created from xxxxxxx","mtime":"now"}}
	try:
		req=self.requests.get(dsturl)
		jsoncontent=eval(req.content.replace("true","True").replace("false","False"))
		if jsoncontent.has_key("stats"):
			jsonstats=(jsoncontent['stats'])
			jsonstats.update(self.filestat)
		else:
			jsonstats=self.filestat
		rev=req.headers['ETag'].replace("\"","")
		with open(localfile,"rb") as fhnd: filedata=(fhnd.read())
		self.mimetypes.init()
		filecontenttype, encode=self.mimetypes.guess_type(localfile)
		jsonobj={"_attachments":{filename:{"content_type":filecontenttype,"data":filedata}}}
		headers={"Content-Transfer-Encoding": "base64","Content-Type":filecontenttype,"If-Match":rev}
		data=str(jsonobj).replace("\'","\"")
		url=dsturl+"/"+filename
		req=self.requests.put(url,headers=headers,data=filedata)
		if REQ:print "attachment send, response:{0}".format(req)
		if req.status_code != 409 :
			updateurl=POSTSERVER+"/folders/_design/folder/_update/append/"+self.folder
			if DEBUG:print updateurl
			req=self.requests.put(updateurl+"?filename="+filename+"&author="+ME+"&comment=none")
			if REQ:print req.text
			self.xattr.setxattr(localfile,'user.sync','true')
	except Exception as e:
		if QUEUE:print "pushattch exception  {0}".format(e)
    def run(self):
        while True:
                #lockvar.acquire()
               	#filequeue.not_empty.acquire()
		#filequeue.not_empty.wait()
		#self.filename=filequeue.get(block=True)
		#filequeue.not_empty.release()	
		localfile=filequeue.get(block=True)
                #lockvar.release()
                #srcdir=WORKDIR.replace("/.","")+"/"+self.folder
                #srcfile=srcdir+"/"+self.filename
                #localfile=self.filename
		#if QUEUE: print "pushattach: {0} queue size:{1}".format(localfile,filequeue.qsize())
		# TODO delete my files from db stat
                try:
		    if self.os.path.exists(localfile):
                    	if self.os.stat(localfile).st_size<1:continue
                    else: 
			if QUEUE: print "file not exists {0}".format(localfile)
		except Exception as e:
                    self.delete(localfile)
               
		sync=self.xattr.getxattr(localfile,'user.sync')
		share=self.xattr.getxattr(localfile,'user.share') 
		#print 'sync:{0} share:{1} file:{2}'.format(sync,share,localfile)
		if ((share=='true') and (sync!='true')):
			#print 'share {0}'.format(localfile)
			self.put(localfile)
		if (share!='true'):
			#print 'delete {0}'.format(localfile)
			self.delete(localfile)
