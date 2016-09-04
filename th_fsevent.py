""" fs event listener for new/change file to syncronize, delete TODO """
from config import *
import myxattr as xattr
import os

def xattrprocess(arg):
	if ((arg[0]=='setxattr') or (arg[0]=='removexattr')):
		print 'xattrprocess:{0}'.format(arg)
		filedir=os.listdir(DEFAULTFOLDER)
                toshare=[ file for file in filedir if 'user.share' in xattr.listxattr('{0}/{1}'.format(DEFAULTFOLDER,file))]
		file=arg[1]
		for ind in range(filequeue.qsize()):
			upload=filequeue.get()
			if upload==file: break
			filequeue.put(upload)
		filequeue.put(file)
	
		
# from host --> db
class th_fsevent(threading.Thread):
    import pyuv,os
    import myxattr as xattr
 
    def __init__(self):
        super(th_fsevent,self).__init__()
        # filestate dict: { filename(string):[events..](array)}
        msgintf.update({'onxattr':xattrprocess})
	self.filestate={}
    def folderchange(self,event,filename,evnt,error):
	try:
		if error is not None:
            		if FSDEBUG:print "error: {0}".format(error)
            		pass
        	file='{0}/{1}'.format(DEFAULTFOLDER,filename)
        	#attrs=self.xattr.listxattr(file)
		#remove file in XFILE if deleted
		#filedir=self.os.listdir(FILEDIR)
        	#toshare=[ share for share in filedir if 'user.share' in self.xattr.listxattr(file)]
		
		#filequeue.put(filename)
        	if FSDEBUG:print "file {0} {1}".format(file,evnt)
		#with lockvar:
        		#stat=statsqueue.get()
       			#if stat is None:
         		#	append=True
        		#else:
            		#	append=(stat[filename]['author']==ME)
        		#	statsqueue.put(stat)
        	if evnt:
            		exists=self.os.path.exists(file)
			if exists:
                		if FSDEBUG: print "{0}: created".format(filename)
               			# who create, me or not ?!
                		#LOCK
                		#if not append:print "excluded {0}".format(filename)
            			append=self.xattr.getxattr(file,'user.share')
				if (append=='true'):
					for ind in range(filequeue.qsize()):
                                        	upload=filequeue.get()
                                        	if upload==file:break
                                        	filequeue.put(upload)
                                	filequeue.put(file)
				
			else:
                		if FSDEBUG: print "{0}: deleted".format(filename)
    				for ind in range(filequeue.qsize()):
                        		upload=filequeue.get()
                        		if upload==file: break
                        		filequeue.put(upload)
                		filequeue.put(file)
	except Exception as e:
		if FSDEBUG:print "fsexception: {0}".format(e)
    	finally:
		[msgid for msgid in msgintf if msgintf[msgid]('folderchange')]
    def run(self):
        self.uvloop=self.pyuv.Loop.default_loop()
        self.fsevent=self.pyuv.fs.FSEvent(self.uvloop)
        self.fsevent.start(FILEDIR,0,self.folderchange)
        self.uvloop.run()
