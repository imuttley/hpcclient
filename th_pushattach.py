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
                self.filestat={self.filename:{"author":ME,"comment":"created from xxxxxxx","mtime":"now"}}
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


