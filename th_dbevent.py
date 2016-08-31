""" thread object for listen db events """
from config import *

# output post channel
class th_dbeventlisten(threading.Thread):
    import requests,time
    def __init__(self,id,sessionid,db,q):
        super(th_dbeventlisten,self).__init__()
	self.name=id
	self.session=sessionid
	self.db=db
	self.queue=q
    def chunck(self,r,*arg,**kwarg):
	for line in r.iter_lines():
	    try:
		if (len(line)>1):
                	jsonresp=eval(line)
			self.queue.put(jsonresp['doc']['post'].replace("\n",""),False)
            except Exception as e:
                if DEBUG: print "excetion from call chunck {0}: {1}".format(self.name,e)
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
            if DEBUG: print "thread {0} start".format(self.name)
	    self.requests.get(url,stream=False,hooks=dict(response=self.chunck))
        except Exception as e:
	    if DEBUG: print "excetion from run {0}: {1}".format(self.name,e)
            self.time.sleep(10)
            self.run()
# TODO empty queue response for new command event



