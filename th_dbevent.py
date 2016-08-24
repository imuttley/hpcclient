""" thread object for listen db events """

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



