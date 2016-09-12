var localdb;
var remoteserver='http://192.107.94.227:5984/';
var pbsformaction='commands/_design/schedule/_update/pbssub/';
var qstatformaction='commands/_design/schedule/_update/qstat/';
var dbfolder='folders';
var filetype={'other':0,'hoc':1,'mod':2,'py':3};
var record={_id:'',_rev:'',stats:'',date:'',_attachments:''};
var remotedb=remoteserver;//+dbfolder;
var subm=new XMLHttpRequest(); 

//link to python response messages
var msgfunction={'filelist':{elemid:'folder',onmessage:showlist},
		'qstat':{elemid:'queue',onmessage:msglog},
		'fileselect':{elemid:'editor',onmessage:showfile},
		'eventproxy':{elemid:'',onmessage:eventregistered},
		'test':{elemid:'',onmessage:msglog},
		'queuelist':{elemid:'queue',onmessage:queuelist},
		'showmime':{elemid:'graph',onmessage:showmime},
		'hpcout':{elemid:'cli',onmessage:tocli},
		'jobstat':{elemid:'stat',onmessage:msglog}};

var behaviour={'fullscreencloser':{'onclick':'closefs','onmouseover':'delay(1,closefs)','onmouseleave':'cleardelay(closefs)'},
		'graphexpander':{'onclick':'openfs','onmouseover':'delay(1,openfs)','onmouseleave':'cleardelay(openfs)'},
		'editorexpander':{'onclick':'openfseditor','onmouseover':'delay(1,openfseditor)','onmouseleave':'cleardelay(openfseditor)'}};


var getquery={id:'',server:'http://localhost:9999',db:'',include_docs:'true',docid:'',since:'now'};
var dbfunction={};

var mainwindow=null;
var filecheck=[];
var livetime=20;

var resourcelist={
	ncpus:1,select:1,mem:'1gb',walltime:'00:30:00',mpiprocs:1,ompthreads:1
};
var variablelist={
	name:'webjob',nrnarg:['python']
};
var modulelist={
	module:['intel','intelmpi']	
};
var userstatus;
var credential={
	user:'tnicosia',password:null
};

function tocli(id,msg){
	var cli=document.getElementById(id);
	var stream=Object.keys(msg);
	stream.map(function(str){cli.insertAdjacentHTML('beforeend', msg[str]+'<br>');});
}

function setevent(elem,msg){
	var that=document.getElementById(elem);
	var ev=Object.keys(msg);
	ev.map(function(evnt){that[evnt]=eval(msg[evnt]);});
}

function elemmap(vr){
        var elem=Object.keys(vr);
        elem.map(function(id){setevent(id,vr[id]);});
}
function closefs(elem){
	var fs=document.getElementById('fullscreen');
	var head=document.getElementById('fshead');
	head.innerText='';
	fs.childNodes.forEach(function(node){if (node.id!='fullscreencloser') fs.removeChild(node);});
	fs.classList.remove('active');
}
function openfs(elem){
	var fs=document.getElementById('fullscreen');
	var head=document.getElementById('fshead');
	head.innerText=elem.target.innerText+' '+elem.target.filename;
	fs.classList.add('active');
}
function openfseditor(elem){
	var fs=document.getElementById('fullscreen');
	var source=document.getElementById('diveditor');
	fs.core=null;
	fs.destination=null;
	fs.childNodes.forEach(function(node){if (node.id!='fullscreencloser') fs.removeChild(node);});
	
	source.childNodes.forEach(function(node){if (node.id=='preeditor'){
											fs.core=node.children[0];
											fs.destination=node;}});
	if (fs.core){
		var textarea=document.createElement('textarea');
		textarea.textContent=fs.core.filedata;
		var savebutton=document.createElement('button');
		savebutton.value='save';
		textarea.style.width="100%";
		textarea.style.height="90%";
	
		var head=document.getElementById('fshead');
		head.innerText='Editor';
		//fs.listen=new Proxy(editor,{set:function(t,k,v){if (k=='innerHTML') return fs[k]=v;}});
		fs.appendChild(textarea);
		fs.classList.add('active');
	}
}
function cleardelay(func){
	return function(i){TweenLite.killDelayedCallsTo(func);};
}
//var jobqueue=eventfordiv('jobquery','queue');
function delay(d,func){
	return function(i){TweenLite.delayedCall(d,func,[i]);};
}
function filechecked(){
	var fc=document.getElementsByClassName('fileselection');
	var list=[];
	fc.map=function(f){for (var i=0;i<this.length;i++)f(this[i]);};	
	fc.map(function(inp){if(inp.checked)list.push(inp.name);});
	sendmsg('sharedlist',list);
}
function filesync(filename){
	var fc=document.getElementsByClassName('fileselection');
	fc.search=function(f){for (var i=0;i<this.length;i++){if(this[i].name==f)return this[i];}};
	var el=fc.search(filename);
}
function showmime(id,datamsg){
        var divembed=document.getElementById(id);
	var embed=document.createElement('iframe');
	embed.setAttribute('type',datamsg.src.split(';')[0].replace('data:',''));
        embed.style.width='100%';
	embed.style.height='100%';
	embed.src=datamsg.src;
	while (divembed.hasChildNodes()) divembed.removeChild(divembed.firstChild);
	divembed.appendChild(embed);
}
function showfile(id,datamsg){
	var el=document.getElementById(id);
	var same=(datamsg['offset']!=0);
	el.eof=false;
	if (el.hasOwnProperty('blockoffset')&&same){
		el.eof=datamsg['blocksize']==0;
	}
	if (!same){
		el.filedata='';
		el.filename=datamsg['name'];
		el.blockoffset=0;
		el.blocksize=datamsg['blocksize'];
	}
	if (!el.eof) el.filedata+=datamsg['block'];
	el.blockoffset=datamsg['offset'];
	var res=window.hljs.highlightAuto(el.filedata);
	el.innerHTML=res.value;
	if (!el.eof) setTimeout(getblock(el.filename,el.blockoffset+el.blocksize),1000);	
}
function fileelement(filename,el,ischecked,islocal){
	var inp=document.createElement('input');
        var spn=document.createElement('span');
        var br=document.createElement('br');
        inp.type='checkbox';
        inp.name=filename;
        inp.className='fileselection';
        inp.onclick=filechecked;
        inp.checked=ischecked;
        if (islocal) el.appendChild(inp);
        spn.id=filename;
        spn.setAttribute('onclick','getblock(this.id,0)');
        spn.textContent=filename;
        el.appendChild(spn);
        el.appendChild(br);
}
function showlist(id,listmsg){
        var el=document.getElementById(id);
        var files=eval(listmsg.dir);
        var checked=eval(listmsg.checked);
	var local=eval(listmsg.local);
        var ul=document.createElement('ul');
	while (el.hasChildNodes()) el.removeChild(el.firstChild);
	files.map(function(name){fileelement(name,el,checked.indexOf(name)!=-1,local.indexOf(name)!=-1);});
}
function oldshowlist(id,listmsg){
	var el=document.getElementById(id);
	var files=eval(listmsg.dir);
	checked=eval(listmsg.checked);
	var ul=document.createElement('ul');
	while (el.hasChildNodes()) el.removeChild(el.firstChild);
	for (var i=0;i<files.length;i++){
		var inp=document.createElement('input');
		var spn=document.createElement('span');
		var br=document.createElement('br');
		inp.type='checkbox';
		inp.name=files[i];
		inp.className='fileselection';
		inp.onclick=filechecked;
		inp.checked=(checked.indexOf(inp.name)!=-1);
		el.appendChild(inp);
		spn.id=files[i];
		spn.setAttribute('onclick','getblock(this.id,0)');
		spn.textContent=files[i];
		el.appendChild(spn);
		el.appendChild(br);
	}
}
function getblock(filename,offset){
	sendmsg('fileselect',{filename:filename,offset:offset,size:400});
}
function sendmsg(req,obj){
	if (mainwindow){
		document.body.classList.remove('idle');
		mainwindow.postMessage({method:req,params:obj},'*');
	}else{
		document.body.classList.add('idle');
		console.log('mainwindow not defined');
	}
}
function msglog(id,msg){
	console.log(msg);
}
function noact(e){
	e.stopPropagation();
	e.preventDefault();
	//console.log('noact ',e);
}
function strtoab(str){
	var buffer=new ArrayBuffer(str.length);
        var convert=new Uint8Array(buffer);
    	for (var i=0;i<str.length;i++) convert[i]=str.charCodeAt(i);
	return buffer;
}
function setorigin(msg){	
}


function registertoeventproxy(){
	getquery.id='queuelist';
	getquery.db='users';
	getquery.since=0;
	sendmsg('eventproxy',getquery);
	if (!msgfunction[getquery.id].registered)
		setTimeout(registertoeventproxy,5000);
}
function eventregistered(id,e){
	msgfunction[e].registered=true;
	console.log('new eventsource from:',e);
}

// function for queue div object
function addjobelement(line,dstel){
	//var jobqre=/([0-9]{5}\.[0-9a-zA-Z]+)[ \t]+([a-z0-9A-Z]+)[ \t]+([a-z0-9A-Z]+)[ \t]+([a-z0-9A-Z]+).*/;
	var jobre=/([0-9]{5}\.[0-9a-zA-Z]+)/
	var sl=line.split(' ');
	j=[];
	sl.map(function(e){if (e!='')j.push(e);});
	var el=null;
	if (j.length>8){
		if (!j[0].match(jobre)) return el
		el=document.createElement('p');
		el.setAttribute('onclick','sendmsg("fullstat",{jodid:this.id});');
		el.id=j[0];
		el.classList.add('queueid');
		el.textContent=j[0]+' <'+j[3]+'> status:'+j[9];
		// in accord to qstat man
		var colors={'B':'white','E':'orange','H':'white','M':'white','R':'orangered','T':'lawngreen','U':'floralwhite','W':'white','X':'azure','S':'red','F':'green','Q':'yellow'};
		el.style.color=colors[j[9]];
		dstel.appendChild(el);
	}
	return el;
}
function queuelist(id,msg){
	//var bug=msg.replace(/\'/g,'\"');
	//var jsonobj=JSON.parse(bug.replace('True','true').replace('False','false'));
	var doc=msg.doc;
	if (doc){
		if (doc._id==credential.user){
			userstatus=doc;
			console.log(doc);
			var divel=document.getElementById(id);
			while (divel.hasChildNodes()) divel.removeChild(divel.firstChild);
			doc.jobquery.split('\n').map(function(e){addjobelement(e,divel);});
			var fstatel=document.getElementById('stat');
			fstatel.textContent=doc.fullstat;
		}
        }
}
function assignfilereader(file){
	if (file.size<(1024*1024*20)){
		var fr=new FileReader();
                fr.filename=file.name;
                fr.totalsize=file.size;
                fr.lm=file.lastModified;
                fr.onload=function(e){
			console.log('send file to main window:',this.filename);
			var fd=e.target.result;
                        var buffer=strtoab(fd);
                        mainwindow.postMessage({method:'write2file',params:{name:this.filename,data:buffer}},'*',[buffer]);
                };
		fr.onerror=function(e){
            		console.log('something wrong: ',e);
            	};
		fr.readAsDataURL(file);
	}
}

function getfile(e){
	e.stopPropagation();
	e.preventDefault();
	var obj=e.dataTransfer;
	obj.files.map=function(f){for (var i=0;i<this.length;i++)f(this[i]);};
	obj.files.map(assignfilereader);
}

function oldgetfile(e){
	e.stopPropagation();
	e.preventDefault();
	var obj=e.dataTransfer;
	for (var i=0;i<obj.files.length;i++){
		if (obj.files[i].size<(1024*1024*20)){
			var fr=new FileReader();
			fr.filename=obj.files[i].name;
			fr.totalsize=obj.files[i].size;
			fr.lm=obj.files[i].lastModified;
			fr.onload=function(e){
                		console.log('send file to main window:',this.filename);
                		//var pattern=/data:(.*)\;base64,(.*)/
				//record._id='webfolder';
				//record.date=Date.now();
				//var stat={};
				//stat[this.filename]={"mtime":this.lm,"author":"tommaso","comment":"created with web interface"};
                                //var part=e.target.result.replace(pattern,'$1 $2');
                                //var data=part.split(' ')[1];
                                //var type=part.split(' ')[0]||"text/plain";
                                //var obj={};
                                //obj[this.filename]={"data":data,"content_type":type};

                                //record._attachments=obj;
                                //record.stats=stat;

	                        //file was read and record is ready for db, try to put new document
        	                //localdb.emit('newdoc',record);
				var fd=e.target.result;
				var buffer=strtoab(fd);
				mainwindow.postMessage({method:'write2file',params:{name:this.filename,data:buffer}},'*',[buffer]);
				//window.sendchunck(e.target.filename,e.target.result.length,e.target.result);
                		//var cmd="base64datafile='"+part+"'";
                		//window.myexec(cmd);
                		//var cmd="{objname}.writefile('"+this.filename+"','"+e.target.result+"')";
                		//window.myexec(cmd);
                };
            fr.onerror=function(e){
            console.log('something wrong: ',e);
            };
            fr.readAsDataURL(obj.files[i]);
		}
	}
}
function editorfunc(e){
	var off=e.target.blockoffset;
	if (e.code=='ArrowDown')
		off+=e.target.blocksize;
	if (e.code=='ArrowUp'){
		off-=e.target.blocksize;
		if (off<0) off=0;
	}
	getblock(e.target.filename,off);
	//console.log('editor text area blocksize:',e.target.textLength);	
	//console.log('editor cursor position:',e.target.selectionEnd);
}
function getdir(){
	sendmsg('filelist',null);
	setTimeout(getdir,13000);
}
function countdown(){
	livetime-=10;
	if (livetime<0){
		console.log('bye bye world!');
		window.close();
	}
	setTimeout(countdown,10000);
}
function tudorevents(){
	
	//var jobqueue=eventfordiv('jobquery','queue');
	//var jobstats=eventfordiv('stats','stat');
	//var graph=eventfordiv('','graph');

	var editor=document.getElementById('editor');
	editor.onkeyup=editorfunc;

	document.addEventListener('dragenter', noact, false);
	document.addEventListener('dragover', noact, false);
	document.addEventListener('drop', getfile, false);

	registertoeventproxy();	
	getdir();	
	countdown();

	elemmap(behaviour);	
	
	//window.localdb=new PouchDB(dbfolder);	
	window.onmessage=function(e){
	        if (window.location.origin!=e.origin){
			var response=e.data.content.response;
			if (msgfunction.hasOwnProperty(response)){
				(msgfunction[response].onmessage)(msgfunction[response].elemid,e.data.content.data);	
                	}else{
				mainwindow=e.source;
				console.log('message from external iframe:',e.data.content);
				//if (response){
				//	var bug=e.data.content.data.replace(/\'/g,'\"');
				//	var jsonobj=JSON.parse(bug.replace('True','true').replace('False','false'));
				//			
				//}
				switch(e.data.content.data){
					case 'heartbeat':
						livetime+=10;
						break;
					default:
						break;
				}
				//sendmsg('targetwindow',{});
        		}
		}
	}
}

function jobsubmit(e){
    var max={nodes:3000,cpus:36,mem:1000};

    if (window.location.protocol!='data:'){
            //subm.open("POST",remotedb+pbsformaction+userstatus.streams.stdin[0]);
        subm.open("POST",remotedb+pbsformaction+'1234567890stdin');
    	subm.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    }else console.log("i'm a frame!");
    var params=document.getElementById("marconi").getElementsByTagName("input");
    var form={};
    for (var i=0;i<params.length;i++){
            form[params[i].name]=params[i].value;
    }
    var nodes=Math.ceil(form.processes/max.cpus);
    var resource={exe:form.exe,walltime:form.walltime,job_name:form.job_name,select:nodes,ncpus:Math.floor(form.processes/nodes),mem:(Math.floor(form.mem/nodes).toString())+"mb"};
    var query="";
    for (k in resource){
            query+=k+"="+encodeURIComponent(resource[k])+"&";
    }
    query=query.substr(0,query.length-1);
    if (window.location.protocol!='data:')
            subm.send(query);
    else
            mainwindow.postMessage({method:'runjob',params:{'query':query}},'*');
    console.log(query);
    var el=document.getElementById("marconi");
    el.classList.remove("active");
}


function eventfordiv(attr,div){
	var evs=new EventSource(remotedb+'users/_changes?feed=eventsource&include_docs=true');
	evs.onopen=function(e){
		console.log('connection for '+attr+' is on');
	};
	evs.onmessage=function(e){
		var data=JSON.parse(e.data);
		var doc=data['doc'];
		if (doc){
			if (doc._id==credential.user)
				userstatus=doc;
				//pbsformaction+=doc.streams.stdin[0];
				//var pbsform=document.getElementById('pbssubform');
				//pbsform.setAttribute("action",pbsformaction);
				console.log(doc);
				var divel=document.getElementById(div);
				divel.innerHTML=doc[attr];
		}
		console.log('message for '+attr+' is '+data.id);
	};
	evs.onerror=function(e){
		console.log('connection error '+attr);
	};
	return evs;
}
