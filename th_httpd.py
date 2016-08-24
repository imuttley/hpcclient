"""Http server for local web folder"""
#from tornado.options import define,options
#from tornado import web
#from tornado.httpserver import HTTPServer
from HTMLParser import HTMLParser
from urllib import base64
import mimetypes
import threading

#for widget
import ipywidgets as wdg
from traitlets import Unicode

#import os
#from IPython.display import IFrame 

#define("port",default=9123,help="hpcclient webinterface",type=int)

params={'fileinputid':'loadfile','objname':__name__.split('.')[1],'guiid':'hpcclientwebui','width':900,'height':900,'port':9123,'srcdoc':'','page':'fermi.html'}

openfiles=dict()


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

class th_m(threading.Thread):
	from IPython.core.display import Javascript as js
	from IPython.core.display import display_javascript as dj 
	import time
	
	def __init__(self,msg,kernel=None):
		super(th_m,self).__init__()
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
			
			msg=session.send(self.kernel.iopub_socket,session.msg("hpcclient",content={"data":"{0}".format(self.msg)}))
			self.time.sleep(10)

def runjob(arg):
	ker=get_ipython().kernel
	th=th_m(arg,kernel=ker)
    	#th.daemon=True
	th.start()


def write2file(filename,chunck=''):
	""" write filename to localhost, with base64 data decode """
	if not chunck:
		data=base64.b64decode(openfiles.pop(filename).split(',')[1])
		with open(filename,'w') as f:
			f.write(data)
	else:
		if filename in openfiles:
			openfiles[filename]+=chunck
		else:
			openfiles.update({filename:chunck})
		
		
	

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

	

def _repr_javascript_():

	path='{0}/www'.format(__name__.split('.')[0])
	filepath='{0}/{1}'.format(path,params['page'])
	compiler=myhtmlparse(path)
	with open(filepath,'r') as root:
		compiler.feed(root.read())
	params['srcdoc']="data:{0};base64,{1}".format(mimetypes.guess_type(filepath)[0],base64.b64encode(compiler.compiledhtml))


	js="""

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

/* append iframe and fileinput as child */
if (newifr){{
	var fi=document.createElement('input');
	fi.setAttribute('id','{fileinputid}');
	fi.setAttribute('type','file');
	fi.setAttribute('onchange','window.fload(this)');
	fi.setAttribute('multiple','true');
	fi.setAttribute('size','20');
	var fs=document.createElement('p');
	fs.setAttribute('id','filesize');
	el.appendChild(ifr);
	el.appendChild(fs);
	el.appendChild(fi);
}}
/* or generate a message and TODO: #hpcclientwebui reference */
else el.innerHTML='<h1 style="color:red;">web gui already showed</h1>';

/* function for message broadcasts to iframes */
window.postbroadcast=function(ms){{
	var fr=window.frames;
	for (var i=0;i<fr.length;i++){{
		fr[i].postMessage(ms,'*');
	}}
}};
window.sendchunck=function(name,totalsize,data){{
	var ker=IPython.notebook.kernel;
	var chuncksize=1024*4;
	console.log('data len:',data.length);
	var obj=document.getElementById('filesize');
	obj.innerHTML='<h1>'+String(Math.floor((1-data.length/totalsize)*100))+'</h1>';
	var cmd="{objname}.write2file('"+name+"',chunck='";
	if (data.length>0){{
		var subdata=data.slice(chuncksize);
		//console.log('subdata len:',subdata.length);
		var cb={{shell:{{reply:function(sh){{if(sh.content.status=='ok')window.sendchunck(name,totalsize,subdata);}}}},
			iopub:{{output:function(out){{console.log('stdout from write2file:',out);}}}}}};
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
						window.sendchunck(e.target.filename,e.target.result.length,e.target.result);
						//var cmd="base64datafile='"+part+"'";
						//window.myexec(cmd);
						//var cmd="{objname}.writefile('"+this.filename+"','"+e.target.result+"')";
						//window.myexec(cmd);	
						}}
					fr.onerror=function(e){{
						console.log('something wrong: ',e);
					}}
					fr.readAsDataURL(obj.files[i]);
				}}
			}}
		}}
	}}
}};
window.myregister=function(){{
	var ker=IPython.notebook.kernel
	if (ker!=null)
        	ker.register_iopub_handler('hpcclient',postbroadcast,ker);
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
/* channel gateway for remote host and iframe */
if (1){{
	var cb={{shell:{{reply:window.postbroadcast}},iopub:{{output:window.postbroadcast}}}};
	window.myregister(); 
	window.onmessage=function(e){{
		if (e.origin){{
			if (window.location.origin!=e.origin){{
        			console.log('message from {guiid} iframe',e);
        			//var nb=IPython.notebook;
				//var kernel=nb.kernel;
				/* sandbox method execution */	
				var cmd='{objname}.';
				if (e.data.method)
        				cmd+=e.data.method+'(';
				if (e.data.params)
					cmd+='"'+e.data.params+'"';
				cmd+=')';
				window.myexec(cmd);
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
