""" object for listen db _attachments change """

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

