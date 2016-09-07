import threading
from config import couchinfo

# thread for pipe redirector
# arg: fd pipe file descriptor from subprocess
# arg: sessionid uuid from couchdb
# arg: name of pipe for post chunk message
# arg: bufsize of buffer for r
class th_pipe2post(threading.Thread):
    import requests,xmlrpclib
    def __init__(self,server,fd,sessionid,name,bufsize=1000):
        super(th_pipe2post,self).__init__()
        self.pipe=fd
	self.server=server
        self.sessionid=sessionid
        self.bufsize=bufsize
        self.name=name
        self.chunk=''
    def run(self):
        couchinfo('pipe {0} post'.format(self.name))
        while True:
                try:
                        buf=self.pipe.readline(self.bufsize)
                        if (len(buf)>0):
                                #self.chunk+=buf
                                self.updateresp=self.requests.post('{0}/{1}/_design/pipe/_update/post/{2}'.format(self.server,self.name,self.sessionid),data=buf)
                except Exception as e:
                        couchinfo(e)
                        break

