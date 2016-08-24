""" object for download _attachment from db and write to filesystem """

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



