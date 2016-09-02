""" fs event listener for new/change file to syncronize, delete TODO """
from config import *

# from host --> db
class th_fsevent(threading.Thread):
    import pyuv,os
    import myxattr as xattr
 
    def __init__(self):
        super(th_fsevent,self).__init__()
        # filestate dict: { filename(string):[events..](array)}
        self.filestate={}
    def fsprocess(self,event,filename,evnt,error):
        [msgid for msgid in msgintf if msgintf[msgid]('fsprocess')]
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
                val=self.xattr.getxattr(file,'user.share')
            except Exception as e:
                val={}
	    finally:
		if ((append) and (val=='true')):
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
        else:
            if DEBUG:print "{1} : {0} ".format(event,filename)
    def run(self):
        self.uvloop=self.pyuv.Loop.default_loop()
        self.fsevent=self.pyuv.fs.FSEvent(self.uvloop)
        self.fsevent.start(WORKDIR.replace("/.","/")+"webfolder",0,self.fsprocess)
        self.uvloop.run()
