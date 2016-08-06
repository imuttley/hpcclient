#!/usr/bin/env python

import subprocess,requests,time,threading,os,sys
from multiprocessing import Process


agentname='Morg'
os.environ['agentname']=agentname
# file replication module
from hpcclient import *


ar=[threading.Event() for i in range(10)]
bashout=''
proc=dict()
pid=0
me=ME
#os.environ['USER']

submitformkey=set(["job_type","job_name","output","input","error","shell","wall_clock_limit","notification","notify_user","bg_size","bg_connectivity","account_no","environment","comment","arguments","step_name","initialdir","requirements","restart","shell"])
runjobkey=set(["np","stdinrank","raise","python","mpi"])
resources=set(["ncpus","select","mpiprocs","ompthreads","mem"])



# thread for pipe redirector
# arg: fd pipe file descriptor from subprocess
# arg: sessionid uuid from couchdb
# arg: name of pipe for post chunk message
# arg: bufsize of buffer for r
class th_pipe2post(threading.Thread):
    import requests,xmlrpclib
    def __init__(self,fd,sessionid,name,bufsize=1000):
    	super(th_pipe2post,self).__init__()
    	self.pipe=fd
    	self.sessionid=sessionid
    	self.bufsize=bufsize
    	self.name=name
    	self.chunk=''
    def run(self):
        print 'pipe {0} post'.format(self.name)
        while True:
        	try:
			buf=self.pipe.readline(self.bufsize)
        		if (len(buf)>0):
            			self.chunk+=buf
            			self.updateresp=self.requests.post('http://127.0.0.1:5984/{0}/_design/pipe/_update/post/{1}'.format(self.name,self.sessionid),data=buf)
                except Exception:
			print e
			break
                                                
# thread object redirect stdout of process to couchdb post
class th_stdout_to_post(threading.Thread):
    import requests,xmlrpclib
    def __init__(self,stdo,sessionid):
        super(th_stdout_to_post,self).__init__()
        self.stdo=stdo
        self.sessionid=sessionid
        self.bufsize=1000
        self.chunk=''

    def run(self):
        print 'th_stdout_to_post is running'
        while True:
            buf=self.stdo.readline(self.bufsize)
            if (len(buf)>0):
                self.chunk+=buf
                print 'update doc'
                self.updateresp=self.requests.post('http://127.0.0.1:5984/commands/_design/schedule/_update/post/{0}'.format(self.sessionid),data=buf)
#bashout+=buf
#TODO update chunck response, filter by session and queryid
#self.requests.post('http://127.0.0.1:5984/sessions/{0}'.format(self.sessionid),buf)

class th_popandexec(threading.Thread):
    import os,pycurl,requests,time
    import xmlrpclib,subprocess,sys

    def getagentvars(self,res,*arg,**kwargs):
	print res
    def __init__(self,id,sessionid):
        super(th_popandexec,self).__init__()
        self.qid=id
	self.sessionid=sessionid
	#if (not id):
	#	self.requests.get("http://127.0.0.1:5984/agents/{0}".format(self.name),hooks=dict(response=self.agentvars))
        self.updaterev=0
        #TODO get shell from db
        self.shell=self.subprocess.Popen(['/bin/bash'],stdin=self.subprocess.PIPE,stdout=self.subprocess.PIPE,stderr=self.subprocess.PIPE,shell=True)
        self.outtopost=th_pipe2post(self.shell.stdout,sessionid,'stdout')
        self.errtopost=th_pipe2post(self.shell.stderr,sessionid,'stderr')

    def printexception(self,msg,e):
	print msg
	print e

    def run(self):
        self.outtopost.start()
        self.errtopost.start()
        self.fetch()
        self.killme()
        #self.execute()

    def chunckres(self,r,*args,**kwargs):
	#print r.content
    	self.requests.post('http://127.0.0.1:5984/commands/_design/schedule/_update/next/{0}'.format(self.sessionid),data=None,hooks=dict(response=self.route))
    def fetch(self):
	# verify for session stdin input
       	try:	
            while True: self.requests.get('http://127.0.0.1:5984/commands/_changes?id={0}&dst={2}&rev={1}&filter=schedule/session&feed=longpoll&heartbeat=5000&since=now'.format(self.sessionid,self.updaterev,'tommaso'),stream=False,hooks=dict(response=self.chunckres))
        except Exception as e: self.printexception("fetch",e)

    def do(self,linein):
        print 'do it'
        for p in self.param: linein+='{0} '.format(p)
        try: 
            #maybe shell in crashed
            self.shell.stdin.writelines(linein+'\n')
        except Exception as e:
            self.printexception("do",e)
            self.killme()

        self.updateresp=self.requests.post('http://127.0.0.1:5984/commands/_design/schedule/_update/next/{0}'.format(self.sessionid),data=None)

    def execute(self):
        print 'execute'
        line=''
        return self.do(line)
    def domethod(self):
        print 'domethod'
        line='{0} '.format(self.method)
        return self.do(line)
    #utility function for simple runjob submit
    def runjob(self):
        param=self.param[0]
        print 'job {0}'.format(set(param.keys()))
        envparam=submitformkey.intersection(set(param.keys()))
        runjobparam=runjobkey.intersection(set(param.keys()))
    	resourceparam=resources.intersection(set(param.keys()))
        #moduleparam=set(param['module'])
	
        #generate batch script for PBS standard
        #resources
        resl=['{0}={1}'.format(k,param[k]) for k in resourceparam]
        lbuf='#PBS -l '
	while len(resl)>0: lbuf=lbuf+resl.pop()+':'
	
	lla=['']
	lla.append(lbuf[:-1])
	lla.append('#PBS -l walltime={0}'.format(param['walltime']))
	#account
	lla.append('#PBS -A {0}'.format(param['account']))
        #environment
    	lla.append('#PBS -N {0}'.format(param['job_name']))
        #variables
   	#lla.append('#PBS -d {0}'.format(param['initialdir'])) 
        #mail
    	lla.append('#PBS -m {0}'.format(param['notification']))
    	lla.append('#PBS -M {0}'.format(param['mail']))
        #stdio
    	lla.append('#PBS -o {0}'.format(param['initialdir']))
    	lla.append('#PBS -e {0}'.format(param['initialdir']))
        #other
	
        rja=['-{0} {1}'.format(k,param[k]) for k in runjobparam]
        buffer='#!/bin/bash\n'
        while len(lla)>0: buffer=buffer+lla.pop()+'\n'
        #buffer=buffer+'#@ queue\n'
        if param.has_key('modules'):
            for m in param['modules']:
                buffer=buffer+'module load '+m+'\n'
	#buffer=buffer+'module load args\n'
	# insert runjob for computation node execute
	#buffer=buffer+'nrniv '
	buffer=buffer+param['engine']+' '
	# insert dll for mech selection
        while len(rja)>0: buffer=buffer+rja.pop()+' '
	buffer=buffer+param['exe']+' '
        if param.has_key('args'):
            for arg in param['args']: buffer=buffer+' '+arg+' '
            buffer=buffer+'\n'
        with open('web.job','w') as file: file.write(buffer)

	
	submit=self.subprocess.Popen(['qsub','web.job'],stdout=self.subprocess.PIPE)
	result=submit.communicate()[0]
	#send to couchdb jobid or error to display
	print 'qsub response:{0}'.format(result)
	##res=requests.post('http://127.0.0.1:5984/users/_design/jobs/_update/batch/{0}'.format(me),data=@open('web.job','r'))
	res=requests.post('http://127.0.0.1:5984/users/_design/jobs/_update/submit/{0}'.format(me),data=result)

        return
    def qselect(self):
        qselect=self.subprocess.Popen(['qselect','-xu','{0}'.format(me)],stdout=self.subprocess.PIPE)
        result=qselect.communicate()[0]
        print 'qselect response:{0}'.format(result)
        res=requests.post('http://127.0.0.1:5984/users/_design/jobs/_update/history/{0}'.format(me),data=result)
        return
    def qstat(self):
        #qselect=self.subprocess.Popen(['qselect','-xu','{0}'.format(me)],stdout=self.subprocess.PIPE)
        qstat=self.subprocess.Popen(['qstat','-fx','-u','{0}'.format(me)],stdin=qselect.stdout,stdout=self.subprocess.PIPE)
        result=qstat.communicate()[0]
        print 'qstat response:{0}'.format(result)
        res=requests.post('http://127.0.0.1:5984/users/_design/jobs/_update/stat/{0}'.format(me),data=result)
        return
    def restart(self):
        print 'execute restart from main thread'
        return
    def signal(self):
        print 'send singnal to shell'
        return
    def killme(self):
        self.pid=self.os.getpid()
        print 'kill myself pid:{0}'.format(self.pid)
        self.os.system("kill -9 {0}".format(self.pid))
	#me=th[self.sessionid].currentThread()
	#me.exit()

    def pyexec(self):
    	linein=''
	for p in self.param:
            linein+='{0} '.format(p)
        try:
            exec(linein)
	    res='pyexec'
        except Exception as e:
            self.printexception("pyexec",e)

    def __dir__(self):
        res=[a for a in dir(self) if not a.startswith('__')]
        print res


    def route(self,recv,*args,**kwargs):
        try:
	    print recv
	    buffer=recv.content
	    if (len(buffer)<2):	return
            print 'xmlrpc:\n {0} '.format(buffer)
	    self.param,self.method=self.xmlrpclib.loads(buffer)
            func=getattr(self,self.method,self.domethod)
            func()
	except Exception as e:
	    self.printexception("route exception",e)	

#def kill():
#    os.kill()
#    sys.exit()

def createthread(sessionid):
    print "create thread {0}".format(sessionid)
    th=th_popandexec(0,sessionid)
    th.start()
    th.join()

def createprocess(resp,*arg,**kwarg):
    json=eval(resp.content)
    print json
    for key in json.get('sessions'):
	if not key in proc:
		print "create process"
		proc[key]=Process(target=createthread,args=(key,))
		proc[key].start()
	else:
		print "process {0}".format(key)
		if proc[key].is_alive():
			print "is alive"
		else:
			print "is dead"
 
    res=0
    for key in json.get('sessions'):
	res+=proc[key].is_alive()
    if(res==0):
	print 'no session active: suicide!'
	os.system("kill -9 {0}".format(os.getpid()))
	

def main():
    pid=os.getpid()
    #me=os.environ['USER']
    #th_main=th_popandexec(0)
    #th_main.daemon=True
    #th_main.start()
    print 'heartbeat here'
    while True:
	requests.post('http://127.0.0.1:5984/agents/_design/heartbeat/_update/agent/{0}'.format(agentname),hooks=dict(response=createprocess))
	
	print 'qselect'
	#qselect=subprocess.Popen(['qselect','-u','{0}'.format(me)],stdout=subprocess.PIPE)
	qstat=subprocess.Popen(['qstat','-T','-x','-u','{0}'.format(me)],stdout=subprocess.PIPE)
	result=qstat.communicate()[0]
	print 'qstat response:{0}'.format(result)

	#joblist=subprocess.Popen(['llq','-u','{0}'.format(me),'-l'],stdout=subprocess.PIPE)
	#result=joblist.communicate()[0]
	#print result
	res=requests.post('http://127.0.0.1:5984/users/_design/jobs/_update/jobqueue/{0}'.format(me),data=result)
	time.sleep(5)

if __name__=="__main__":
    main()


