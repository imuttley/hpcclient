"""View controller for widget"""
from config import *
from HTMLParser import HTMLParser
import uuid,requests,base64,mimetypes,threading,os
import myxattr as xattr 

params={'logindone':0,'pageloaded':0,'sessionid':-1,'window':0,'destfolder':'{0}'.format(DEFAULTFOLDER),'fileinputid':'loadfile','objname':__name__.split('.')[1],'guiid':'hpcclientwebui','width':1080,'height':900,'port':9123,'srcdoc':'','page':'fermi.html'}
openfiles=dict()
sharefiles=[]
eventslistener=[]

def fsevent(*evnt):
	if (evnt[0]=='folderchange'):
		filelist()
#register event listener for filesystem
msgintf.update({'onfolderchange':fsevent})

"""thread for listen events from message server, parameters: server, db, include_docs, docid, since"""
class th_eventlistener(threading.Thread):
    import requests,time

    def __init__(self,id,kernel=None,**params):
        super(th_eventlistener,self).__init__()
        self.params=params
	self.name=id
	self.kernel=kernel	
    
    def reply(self,msg,raw=False):
	session=self.kernel.session
        msend=session.send(self.kernel.iopub_socket,session.msg("hpcclient",content={"response":self.name,"data":msg}))
 
    def proxyevent(self,resp,*arg,**kwarg):
	if not resp._content_consumed:	
		for line in resp.iter_lines():
			try:
              			if (len(line)>1):
					jsonresp=eval(line.replace("null","None").replace("true","True").replace("false","False"))
					self.reply(jsonresp,raw=True)
            		except Exception as e:
                		self.reply(e)

    def run(self):
        url="{server}/{db}/_changes?feed=continuous&include_docs={include_docs}&id={docid}&since={since}".format(**self.params)
        if DEBUG: print 'listen to:{0}'.format(url)
	try:
                self.requests.get(url,stream=False,hooks=dict(response=self.proxyevent))
        except Exception as e:
                if DEBUG: print 'exception {0}'.format(e)
		self.time.sleep(10)
                self.run()


""" create a thread for listen and share msg """
def eventproxy(obj):
        obj.update({'kernel':get_ipython().kernel})
        if obj['id'] not in [ ev.name for ev in eventslistener]:
                th=th_eventlistener(**obj)
                eventslistener.append(th)
                th.start()
        sendmsg("eventproxy",obj['id'])

def sendevent(id,msg):
        sendmsg("event",{"listenerid":id,"msg":msg})



"""utility and interface functions"""



"""send message to channel hpcclient"""
def sendmsg(sender,msg,raw=False):
	#kernel=get_ipython().kernel
	session=kernel.session
	if not raw:
        	msend=session.send(kernel.iopub_socket,session.msg("hpcclient",content={"response":sender,"data":"{0}".format(msg)}))
	else:
		msend=session.send(kernel.iopub_socket,session.msg("hpcclient",content={"response":sender,"data":msg}))
"""full stat request"""
def fullstat(jobid=None):
	print 'fullstat request for {0}'.format(jobid)

"""runjob procedure message from iframe"""
def runjob(arg):
	url='{0}?{1}'.format(RUNJOBPOSTURL,arg)
	reqid=requests.post(url)		
	if RJDEBUG: print 'runjob response:{0}'.format(reqid)

"""get a block of selected file"""
def fileselect(name,offset=0,size=4*1024):
	try:
		with open('{0}/{1}'.format(DEFAULTFOLDER,name),'r') as f:
			f.seek(offset)
			block=f.read(size)
	except Exception as e:
		block='{0}'.format(e)
        sendmsg("fileselect",{"name":name,"offset":offset,"blocksize":size,"block":block},raw=True)
"""write a block on selected file and offset"""
def writeblock(name,offset=0,data=''):
	with open('{0}/{1}'.format(DEFAULTFOLDER,name),'r+') as f:
		f.seek(offset)
		f.write(data)

"""unblocking file transfer. TODO: filter for filetype"""	
def write2file(filename,chunck=''):
	""" write filename to localhost, with base64 data decode """
	if not chunck:
		data=base64.b64decode(openfiles.pop(filename).split(',')[1])
		#data=base64.b64decode(openfiles.pop(filename))
		with open('{0}/{1}'.format(DEFAULTFOLDER,filename),'w') as f:
			f.write(data)
	else:
		if filename in openfiles:
			openfiles[filename]+=chunck
		else:
			openfiles.update({filename:chunck})
		

"""create a list of files with shared attribute set/clear.TODO:filter fo filetype"""
def filelist():
	resp=os.listdir(DEFAULTFOLDER)
        checked=[ k for k in resp if 'user.share' in xattr.listxattr('{0}/{1}'.format(DEFAULTFOLDER,k))]
        checkable=[ local for local in resp if 'user.author' not in xattr.listxattr('{0}/{1}'.format(DEFAULTFOLDER,local))]
	sendmsg("filelist",{"dir":resp,"checked":checked,"local":checkable},raw=True)

"""set/clear file shared attribute."""		
def sharedlist(*list):
	sharefiles=[ f for f in list ]
	allfiles=os.listdir(DEFAULTFOLDER)
	unsharefile=[ file for file in allfiles if file not in list]
	for file in unsharefile:
		try:
			test=xattr.removexattr('{0}/{1}'.format(DEFAULTFOLDER,file),'user.share')
		except:
			pass
	for file in sharefiles:
		try:
			test=xattr.setxattr('{0}/{1}'.format(DEFAULTFOLDER,file),'user.share','true')
		except:
			pass



"""parse and embed to base64string the webpage tree"""
class myhtmlparse(HTMLParser):
	def __init__(self,path,debug=False):
		self.compiledhtml=''
		self.path=path
		self.reset()
		
	def handle_starttag(self,tag,attr):
		if DEBUG: print self.get_starttag_text()
		if DEBUG: print "at position:",self.getpos()
		
		if DEBUG: print "start tag:",tag
		newobj="<{0} ".format(tag)
		linkimport=""
		for k,v in attr:
			if DEBUG: print "attrib:",k
			if DEBUG: print "value:",v
			if ((k=='src')|((k=='href')&(tag=='link'))):
				if DEBUG: print "<{0}>".format(tag)
				with open ('{0}/{1}'.format(self.path,v),'rb') as link:
					linkimport=link.read()
				newobj=newobj+"""{0}="data:{1};base64,{2}" """.format(k,mimetypes.guess_type('www/'+v)[0],base64.b64encode(linkimport))
			else:
				newobj=newobj+"""{0}="{1}" """.format(k,v)
		newobj=newobj[:-1]+">"
		#+linkimport
		#if tag=='link':
		#	newobj=newobj+"</{0}>".format(tag)
		if DEBUG: print newobj
			
		self.compiledhtml=self.compiledhtml+newobj
	def handle_endtag(self,tag):
		if DEBUG: print "</{0}>".format(tag)
		self.compiledhtml=self.compiledhtml+"</{0}>".format(tag)
	def handle_data(self,data):
		if DEBUG: print data
		self.compiledhtml=self.compiledhtml+data
	#def close(self,filename):
	#	self.goahead(1)
	#	with open(filename,'w') as fw:
	#		fw.write(self.compiledhtml)


"""procedure for login"""
def verifypasswd(user=None,passwd=None):
	if DEBUG: print 'login for {0}, passwd {1}'.format(user,passwd)
	try:
		[msgid for msgid in msgintf if msgintf[msgid](('verifypasswd',user,passwd))]
	except:
		pass
	#TODO: verify an hash
	#if ((user=='test') and (passwd=='test')):
	#	params['logindone']=1
	#	_render('fermi.html')

"""http method for widget"""
def _httpget(page):
	""" www tree from $HOME/modulename/www/ """
	path='{0}/www'.format(__name__.split('.')[0])
        filepath='{0}/{1}'.format(path,page)
        if DEBUG: print "parse html from: ".format(filepath)
        compiler=myhtmlparse(path)
        with open(filepath,'r') as root:
                compiler.feed(root.read())	
	params['srcdoc']="data:{0};base64,{1}".format(mimetypes.guess_type(filepath)[0],base64.b64encode(compiler.compiledhtml))

def _render(page):
	[msgid for msgid in msgintf if msgintf[msgid](('render',page))]
	_httpget(page)
	sendmsg("render",params['srcdoc'])

def _logedon(arg):
	if arg=='tunnelok':
		params['logindone']=1
		_render('fermi.html')
msgintf.update({'ontunnel':_logedon})

	
""" javascript for widget """
def _repr_javascript_():
	if params['logindone']==0:
		_httpget('index.html')

	js="""
if (true){{
/* javascript for enhanced widget */
/* get first output cell */
var el=element.get(0);
var targetwindow=null;
var couchsessionid={sessionid};

/* prevent cache from output cell */
if (!IPython.notebook.kernel) {{
	console.log('reload module {objname}');
	while (el.hasChildNodes()) el.removeChild(el.firstChild);
	el.innerHTML='<h1 style="color:red;">reload {objname} for show gui</h1>';	
}} else {{
if ({window}){{
	if (window.hasloaded)
		targetwindow=window.open(window.hasloaded,'{guiid}','width={width},height={height},menubar=no,location=no,resizable=no,scrollbars=yes,status=no');
	else
		targetwindow=window.open('{srcdoc:s}','{guiid}','width={width},height={height},menubar=no,location=no,resizable=no,scrollbars=yes,status=no');
		
}} 
/* search an iframe for render */
var ifr=document.getElementById('{guiid}');
console.log(ifr);

/* is a new iframe */
var newifr=(!ifr);

/* if none present, create it */
if(newifr){{
	ifr=document.createElement('iframe');
	/* set all attribute for iframe */
	ifr.setAttribute('id','{guiid}');
	ifr.setAttribute('width',{width});
	ifr.setAttribute('height',{height});
	ifr.setAttribute('sandbox','allow-top-navigation allow-scripts allow-forms allow-same-origin');
	ifr.setAttribute('seamless','true');
	//ifr.src='http://localhost:{port}/{page}';
	if (window.hasloaded)
		ifr.src=window.hasloaded;
	else
		ifr.src='{srcdoc:s}';
}}

/* append iframe and fileinput as child */
if (newifr){{
	var fi=document.createElement('input');
	fi.setAttribute('id','{fileinputid}');
	fi.setAttribute('type','file');
	fi.setAttribute('onchange','window.fload(this)');
	fi.setAttribute('multiple','true');
	fi.setAttribute('size','20');
	
	var fs=document.createElement('p');
	fs.setAttribute('id','filespercent');
	
	//var sty=document.createElement('style');
	//sty.textContent="#filesize > h1{{transition: all 1s ease;-webkit-transition:all 1s ease;opacity:1;}}";
	if (!{window}) el.appendChild(ifr);
	//document.body.appendChild(sty);
	el.appendChild(fi);
	el.appendChild(fs);
}}
/* or generate a message and TODO: #hpcclientwebui reference */
else el.innerHTML='<h1 style="color:red;">web gui already showed</h1>';

/* function for send message to iframes or window */
window.communicate=function(ms){{
        console.log('msg from notebook ');
	var a='render';
        switch (ms.content.response){{
        	case 'render':
			window.hasloaded=ms.content.data;
       			if({window}){{
				targetwindow.close();
				targetwindow=window.open(window.hasloaded,'{guiid}','width={width},height={height},menubar=no,location=no,resizable=no,scrollbars=yes,status=no');
			}}
			else {{
				var ifr=document.getElementById('{guiid}');
				ifr.src=window.hasloaded;
			}}
		default:
			if ({window}){{
				targetwindow.postMessage({{content:{{data:'setorigin'}}}},'*');
				targetwindow.postMessage(ms,'*');
			}}
			else {{
				var fr=window.frames;
				for (var i=0;i<fr.length;i++) {{
					fr[i].postMessage({{content:{{data:'setorigin'}}}},'*');
					fr[i].postMessage(ms,'*');
				}}
			}}
			
	}}
}};
window.setorigin=function(){{
	var msg={{content:{{data:'setorigin'}}}};
	window.communicate(msg);
}};
window.sendchunck=function(name,totalsize,data){{
	var ker=IPython.notebook.kernel;
	var chuncksize=1024*4;
	var filed=document.getElementById(name);
	console.log('data len:',data.length);
	var obj=document.getElementById('filespercent');
	//obj.innerHTML='<h1 id="'+name+'">'+name+' '+String(Math.floor((1-data.length/totalsize)*100))+'&#37;</h1>';
	//var h=obj.childNodes[0];
	//h.style.opacity=0;
	var cmd="{objname}.write2file('"+name+"',chunck='";
	if (data.length>0){{
		var subdata=data.slice(chuncksize);
		//console.log('subdata len:',subdata.length);
		var cb={{shell:{{reply:function(sh){{if(sh.content.status=='ok')window.sendchunck(name,totalsize,subdata);}}}},
			iopub:{{output:function(out){{console.log('stdout from write2file:',out);}}}}}};
		
        	if (!filed){{
                	filed=document.createElement('h1');
                	filed.setAttribute('id',name);
                	obj.appendChild(filed);
		}}
		filed.innerHTML=''+name+' '+String(Math.floor((1-data.length/totalsize)*100))+'&#37;';
        }}
	else {{
		if(filed) filed.remove();	
	}}
	cmd+=data.slice(0,chuncksize)+"')";
	var nb=IPython.notebook;
        var kernel=nb.kernel;
	//console.log('cmd:',cmd);
	kernel.execute(cmd,cb);
}};
window.fload=function(obj){{
	if (obj.files){{
		if(obj.files.length>0){{
			for (var i=0;i<obj.files.length;i++){{
				console.log('file: '+obj.files[i].name+' '+obj.files[i].size);	
				if (obj.files[i].size<(1024*1024*20)){{
					var fr=new FileReader();
					fr.filename=obj.files[i].name;
					fr.totalsize=obj.files[i].size;
					fr.onload=function(e){{
						console.log('send file to backend');
						var data=e.target.result;
						window.sendchunck(e.target.filename,data.length,data);
						//var cmd="base64datafile='"+part+"'";
						//window.myexec(cmd);
						//var cmd="{objname}.writefile('"+this.filename+"','"+e.target.result+"')";
						//window.myexec(cmd);	
						}};
					fr.onerror=function(e){{
						console.log('something wrong: ',e);
					}};
					fr.readAsDataURL(obj.files[i]);
				}}
			}}
		}}
	}}
}};
window.myregister=function(){{
	var ker=IPython.notebook.kernel
	if (ker!=null)
        	ker.register_iopub_handler('hpcclient',communicate,ker);
	else{{
		console.log('retry to register msg_type');
		setTimeout(myregister,2000);
		}}
}};
window.myexec=function(cmd){{
	var nb=IPython.notebook;
        var kernel=nb.kernel;
	var nextcell=nb.get_selected_cell();
        //var code=nextcell.toJSON();
        //code.source=cmd;
        var cellcb=nextcell.get_callbacks();
        kernel.execute(cmd,cellcb,{{silent:false}});
}};
window.arraytostr=function(ab){{
	var uint=new Uint8Array(ab);
	var data='';
	for (var i=0;i<uint.length;i++) data+=String.fromCharCode(uint[i]);
   	return data;
}};
window.hb=function(){{
	var msg={{content:{{data:'heartbeat'}}}};
	window.communicate(msg);
	setTimeout(hb,10000);
}};
/* channel gateway for remote host and iframe */
if (1){{
	var cb={{shell:{{reply:window.communicate}},iopub:{{output:window.communicate}}}};

	window.myregister();
	window.hb(); 
	window.onmessage=function(e){{
		if (e.origin){{
			if (window.location.origin!=e.origin){{
        			console.log('message from {guiid} iframe',e);
        			//var nb=IPython.notebook;
				//var kernel=nb.kernel;
				/* sandbox method execution */	
				
				var cmd='{objname}.';
				switch (e.data.method){{
					case 'write2file':
						var name=e.data.params.name;
						var data=window.arraytostr(e.data.params.data);
						window.sendchunck(name,data.length,data);
						break;
					case 'script':
						var data=(e.data.params.data);
						eval(data);
						break;
					case 'targetwindow':
						targetwindow=e.source;
						window.setorigin();	
						break;
					case 'eventproxy':
						cmd+=e.data.method+'('+JSON.stringify(e.data.params)+')';
						window.myexec(cmd);
						break;		
					default:	
        					cmd+=e.data.method+'(';
						if (e.data.params){{
							var prm=[];
							var obj=e.data.params;
							// Object.values experimental!!
							if (!obj.hasOwnProperty('forEach')){{
								var keys=Object.keys(obj);
								keys.forEach(function(key){{prm.push(obj[key]);}});
							}}else	
						 		obj.forEach(function(value){{prm.push(value);}});
							while(prm.length){{
								var val=prm.shift();
								if (typeof(val)==='string') cmd+='"'+val+'"';
								else cmd+=val;
								if (prm.length) cmd+=',';
							}}
						}}
						cmd+=')';
						window.myexec(cmd);
				}}
				//var nextcell=nb.get_selected_cell();
				//var code=nextcell.toJSON();
				//code.source=cmd;
				//var cellcb=nextcell.get_callbacks();
				//kernel.execute(cmd,cellcb,{{silent:false}});
				//nextcell.fromJSON(code);
				//nextcell.execute();
				//nb.insert_cell_below();
				//nb.select_next();


			}}
        	}}
	}};
}}
}}
}}else{{
	var el=element.get(0);
	el.appendChild(window.hasloaded[0]);
}}
""".format(**params)
	params['pageloaded']=1
	return js

if __name__=="__main__":
	print "reload in module"
