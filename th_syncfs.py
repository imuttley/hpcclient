""" object for listen db _attachments change """
from config import *
from th_getattach import *

# from db to host
class th_syncfilesystem(threading.Thread):
    import pyuv,requests,time
    def __init__(self,id,sessionid):
        super(th_syncfilesystem,self).__init__()
    	self.id=id
	self.sessionid=sessionid
    def getfilename(self,r,*arg,**kwarg):
	[msgid for msgid in msgintf if msgintf[msgid]('getfilename')]
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
                    		if DEBUG:print "exception from method getfilename {0}: {1}".fomart(self.id,e)
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

def getattach(files,folder,stats):
    if DEBUG:print "folder {0}/".format(folder)
    lockvar.acquire()
    while not statsqueue.empty():
        statsqueue.get()
    statsqueue.put(stats)
    lockvar.release()
    if DEBUG:print "stats: {0}".format(stats)
    for filename in files:
        attrib=files[filename]
        if DEBUG:print "{0} {1} size: {2}".format(filename,attrib['digest'].replace("md5-","md5: "),attrib['length'])
        ttg=th_getattach(filename,folder,stats[filename],attrib)
        getattachs.append(ttg)
        ttg.start()


