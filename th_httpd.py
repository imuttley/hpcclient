"""Http server for local web folder"""
#from tornado.options import define,options
#from tornado import web
#from tornado.httpserver import HTTPServer
from HTMLParser import HTMLParser
import uuid,requests,xattr,base64,mimetypes,threading,os
from sshtunnel import SSHTunnelForwarder as tunnel

#for widget
#import ipywidgets as wdg
#from traitlets import Unicode

#import os
#from IPython.display import IFrame 

#define("port",default=9123,help="hpcclient webinterface",type=int)

"""object variables"""
params={'sessionid':-1,'window':0,'destfolder':'webfolder','fileinputid':'loadfile','objname':__name__.split('.')[1],'guiid':'hpcclientwebui','width':1080,'height':900,'port':9123,'srcdoc':'','page':'fermi.html'}
openfiles=dict()
sharefiles=[]
eventslistener=[]

#try:
#	with open('moduletest/www/compiled.html','rb') as html:
#		text=html.read()
#	params['srcdoc']="data:text/html;base64,{0}".format(base64.b64encode(text))
#except:	
#	print 'wrong directory'


#sendmsg="""
#var ifr=document.getElementById('{0:s}');
#ifr.contentWindow.postMessage('ciao','*');
#""".format(guiid)


class gwwidget(wdg.DOMWidget):
    _view_name=Unicode('gw widget').tag(sync=True)
    _view_module=Unicode(params['objname']).tag(sync=True)

    msg=Unicode().tag(sync=True)

    def __init__(self,**kwargs):
        wdg.DOMWidget.__init__(self,**kwargs)
        self.err=wdg.CallbackDispatcher(accepted_nargs=[0,1])
        self.on_msg(self._handle_msg)

    def _handle_msg(self,content):
        if 'event' in content:
            print content['event']





class test():
        from IPython.core.display import Javascript as js 
	from IPython.core import display
	import time
        from ipykernel import jsonutil 

        def __init__(self,msg):
                self.msg=msg
        def run(self):
                var="""console.log('run call');var fr=window.frames;for (var i=0;i<fr.length;i++){{fr[i].postMessage('{0}','*');}};""".format(self.msg)
		vt=self.jsonutil.json_clean(var)
		javaobj=self.js(vt)
		self.display.display_javascript(javaobj)

"""packet message hpcchannel to iframe"""
class th_hpcchannel(threading.Thread):
	from IPython.core.display import Javascript as js
	from IPython.core.display import display_javascript as dj 
	import time
	
	def __init__(self,msg,kernel=None):
		super(th_hpcchannel,self).__init__()
		self.msg=msg
		self.kernel=kernel
        	self.name='javascriptthread'
	def run(self):
        	while(1):
	            	#var="""var el=IPython.notebook.get_selected_cell();
			#	console.log('call run for {0:s}');
			#	window.postbroadcast('{0:s}');
			#	el.output_area.outputs.pop();""".format(self.msg)
			#var="""{0}""".format(self.msg)
			#self.dj(self.js(var))
			session=self.kernel.session
			
			msend=session.send(self.kernel.iopub_socket,session.msg("hpcclient",content={"data":"{0}".format(self.msg)}))
			self.time.sleep(10)


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
            		#finally:
				#print 'event from {0}:{1}'.format(self.params['server'],message)
				#self.reply(message)
                        	#msend=session.send(self.kernel.iopub_socket,session.msg("hpcclient",content={"data":msg}))
				#sendmsg(self.id,message,raw=True)
                		#js="""window.postMessage({response},'*');""".format(**obj)
                		#Javascript(data=js)


    def run(self):
        url="{server}/{db}/_changes?feed=continuous&include_docs={include_docs}&id={docid}&since={since}".format(**self.params)
        print 'listen to:{0}'.format(url)
	try:
                self.requests.get(url,stream=False,hooks=dict(response=self.proxyevent))
        except Exception as e:
                print 'exception {0}'.format(e)
		self.time.sleep(10)
                self.run()



#def proxymessage(msg):
"""send message to channel hpcclient"""
def sendmsg(sender,msg,raw=False):
	kernel=get_ipython().kernel
	session=kernel.session
	if not raw:
        	msend=session.send(kernel.iopub_socket,session.msg("hpcclient",content={"response":sender,"data":"{0}".format(msg)}))
	else:
		msend=session.send(kernel.iopub_socket,session.msg("hpcclient",content={"response":sender,"data":msg}))

"""packet message hpcchannel from iframe"""
def runjob(arg):
	ker=get_ipython().kernel
	th=th_hpcchannel(arg,kernel=ker)
    	#th.daemon=True
	th.start()
"""get a block of selected file"""
def fileselect(name,offset=0,size=4*1024):
	with open('{0}/{1}'.format(params['destfolder'],name),'r') as f:
		f.seek(offset)
		block=f.read(size)
        sendmsg("fileselect",{"name":name,"offset":offset,"blocksize":size,"block":block},raw=True)
"""write a block on selected file and offset"""
def writeblock(name,offset=0,data=''):
	with open('{0}/{1}'.format(params['destfolder'],name),'r+') as f:
		f.seek(offset)
		f.write(data)

"""dir"""
def filelist():
	resp=os.listdir(params['destfolder'])
	checked=[ k for k in resp if 'user.share' in xattr.listxattr('{0}/{1}'.format(params['destfolder'],k))]
	sendmsg("filelist",{"dir":resp,"checked":checked},raw=True) 
"""unblocking file transfer"""	
def write2file(filename,chunck=''):
	""" write filename to localhost, with base64 data decode """
	if not chunck:
		data=base64.b64decode(openfiles.pop(filename).split(',')[1])
		#data=base64.b64decode(openfiles.pop(filename))
		with open('{0}/{1}'.format(params['destfolder'],filename),'w') as f:
			f.write(data)
	else:
		if filename in openfiles:
			openfiles[filename]+=chunck
		else:
			openfiles.update({filename:chunck})
		
		
def sharedlist(*list):
	sharefiles=[ f for f in list ]
	allfiles=os.listdir(params['destfolder'])
	unsharefile=[ file for file in allfiles if file not in list]
	for file in unsharefile:
		try:
			test=xattr.removexattr('{0}/{1}'.format(params['destfolder'],file),'user.share')
		except:
			pass
	for file in sharefiles:
		try:
			test=xattr.setxattr('{0}/{1}'.format(params['destfolder'],file),'user.share','true')
		except:
			pass

""" create a thread for listen and share msg """		
def eventproxy(obj):
	#id=uuid.uuid1().get_hex()	
	obj.update({'kernel':get_ipython().kernel})
	#obj.update({'id':id})
	if obj['id'] not in [ ev.name for ev in eventslistener]: 
		th=th_eventlistener(**obj)
		eventslistener.append(th)
		th.start()
	sendmsg("eventproxy",obj['id'])
	
def sendevent(id,msg):
	sendmsg("event",{"listenerid":id,"msg":msg})

#class myfilehandler(web.StaticFileHandler):
#    def prepare(self):
#        print 'My get!'

#        self.add_header("myhead","test-header")
#	self.add_header("Cache-Control","no-cache, no-store, must-revalidate")
#	self.add_header("Pragma","no-cache")
#	self.add_header("Expires","0")





class myhtmlparse(HTMLParser):
	def __init__(self,path,debug=False):
		self.compiledhtml=''
		self.debug=debug
		self.path=path
		self.reset()
		
	def handle_starttag(self,tag,attr):
		if self.debug: print self.get_starttag_text()
		if self.debug: print "at position:",self.getpos()
		
		#print "start tag:",tag
		newobj="<{0} ".format(tag)
		linkimport=""
		for k,v in attr:
			#print "attrib:",k
			#print "value:",v
			if ((k=='src')|((k=='href')&(tag=='link'))):
				if self.debug: print "<{0}>".format(tag)
				with open ('{0}/{1}'.format(self.path,v),'rb') as link:
					linkimport=link.read()
				newobj=newobj+"""{0}="data:{1};base64,{2}" """.format(k,mimetypes.guess_type('www/'+v)[0],base64.b64encode(linkimport))
			else:
				newobj=newobj+"""{0}="{1}" """.format(k,v)
		newobj=newobj[:-1]+">"
		#+linkimport
		#if tag=='link':
		#	newobj=newobj+"</{0}>".format(tag)
		if self.debug: print newobj
			
		self.compiledhtml=self.compiledhtml+newobj
	def handle_endtag(self,tag):
		if self.debug: print "</{0}>".format(tag)
		self.compiledhtml=self.compiledhtml+"</{0}>".format(tag)
	def handle_data(self,data):
		if self.debug: print data
		self.compiledhtml=self.compiledhtml+data
	#def close(self,filename):
	#	self.goahead(1)
	#	with open(filename,'w') as fw:
	#		fw.write(self.compiledhtml)




#"""Main procedure for local http server"""
    #def startserver():
	# set local www folder 
    #pwd='./'+__name__.split('.')[0]+'/www/'
	# create a file application
    #webinterface=web.Application([(r"/(.*)",myfilehandler,{"path":pwd}),])
	# create an http server for application
    #httpd=HTTPServer(webinterface)
    #try:
		# if not used, listen to localhost:port
        #	httpd.listen(params['port'])
		#IOLoop.current().start()
        #except Exception as e:
		#print 'httpd exception: {0}'.format(e)
#pass

#"""Html iframe element rapresentation"""
#def _repr_html_():
#	wmain()
	

#	return """<iframe id="hpcclientwebui" src="http://localhost:9123/fermi.html" width="800px" height="900px"></iframe>"""

	
""" javascript for widget """
def _repr_javascript_():

	path='{0}/www'.format(__name__.split('.')[0])
	filepath='{0}/{1}'.format(path,params['page'])
	compiler=myhtmlparse(path)
	with open(filepath,'r') as root:
		compiler.feed(root.read())
	params['srcdoc']="data:{0};base64,{1}".format(mimetypes.guess_type(filepath)[0],base64.b64encode(compiler.compiledhtml))


	js="""
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
""".format(**params)

	newjs="""
    
    /* search an iframe for render */
    var ifr=document.getElementById('{guiid}');
    console.log(ifr);
    
    /* is a new iframe */
    var newifr=(!ifr);
    
    /* if none present, create it */
    if(newifr) ifr=document.createElement('iframe');
    
    /* set all attribute for iframe */
    ifr.setAttribute('id','{guiid}');
    ifr.setAttribute('width',{width});
    ifr.setAttribute('height',{height});
    ifr.setAttribute('sandbox','allow-top-navigation allow-scripts allow-forms allow-same-origin');
    ifr.setAttribute('seamless','true');
    //ifr.src='http://localhost:{port}/{page}';
    ifr.src='{srcdoc:s}';
    console.log(ifr);
    
    /* get first output cell */
    var el=element.get(0);
    
    /* append iframe as child */
    if (newifr) el.appendChild(ifr);
    /* or generate a message and TODO: #hpcclientwebui reference */
    else el.innerHTML='<h1 style="color:red;">web gui already showed</h1>';
    
    /* function for message broadcasts to iframes */
    window.postbroadcast=function(ms){{
        if (!{window}){{
		var fr=window.frames;
        	for (var i=0;i<fr.length;i++){{
        		fr[i].postMessage(ms,'*');
        	}}
    }}
    /* channel gateway for remote host and iframe */
    if (1){{
        var cb={{shell:{{reply:window.postbroadcast}}}};
        
        requirejs.undef('{objname}');
        define('{objname}',["jupyter-js-widgets"],function(widgets){{
            var gw=widgets.DOMWidgetView.extend({{
                render:function(){{this.setElement(window);}},
                events:{{'message':'handle_msg'}},
                handle_msg:function(e){{console.log('handle {objname} message:',e);}}
            }});
        }});
    }}
""".format(**params)

	#startserver()
	#print js
	return js

if __name__=="__main__":
	startserver()
