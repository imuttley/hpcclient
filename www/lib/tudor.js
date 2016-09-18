var localdb;
var remoteserver='http://192.107.94.227:5984/';
var pbsformaction='commands/_design/schedule/_update/pbssub/';
var qstatformaction='commands/_design/schedule/_update/qstat/';
var dbfolder='folders';
var filetype={'other':0,'hoc':1,'mod':2,'py':3};
var record={_id:'',_rev:'',stats:'',date:'',_attachments:''};
var remotedb=remoteserver;//+dbfolder;
var subm=new XMLHttpRequest(); 
var _filefolder={};
var filefolder=new Proxy(_filefolder,{set:function(e,k,v){e[k]=v;},get:function(e,k){return e[k];}});

//link to python response messages
var msgfunction={'filelist':{elemid:'folder',onmessage:showlist},
					'qstat':{elemid:'queue',onmessage:msglog},
					'fileselect':{elemid:'editor',onmessage:showfile},
					'eventproxy':{elemid:'',onmessage:eventregistered},
					'test':{elemid:'',onmessage:msglog},
					'queuelist':{elemid:'queue',onmessage:queuelist},
					'showmime':{elemid:'graph',onmessage:showmime},
					'hpcout':{elemid:'cli',onmessage:tocli},
					'filestats':{elemid:'filefolder',onmessage:assignstats},
					'jobstat':{elemid:'stat',onmessage:msglog}};

var behaviour={'fullscreencloser':{'onclick':'closefs','onmouseover':'delay(1,closefs)','onmouseleave':'cleardelay(closefs)'},
		'graphexpander':{'onclick':'openfsgraph','onmouseover':'delay(1,openfsgraph)','onmouseleave':'cleardelay(openfsgraph)'},
		'editorexpander':{'onclick':'openfseditor','onmouseover':'delay(1,openfseditor)','onmouseleave':'cleardelay(openfseditor)'},
		'statexpander':{'onclick':'openfsstat','onmouseover':'delay(1,openfsstat)','onmouseleave':'cleardelay(openfsstat)'},
		'fileexpander':{'onclick':'openfsfile','onmouseover':'delay(1,openfsfile)','onmouseleave':'cleardelay(openfsfile)'},
		'cliexpander':{'onclick':'openfscli','onmouseover':'delay(1,openfscli)','onmouseleave':'cleardelay(openfscli)'}};


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
	while (fs.childNodes.length>1){
		fs.childNodes.forEach(function(node){if (node.id!='fullscreencloser') fs.removeChild(node);});
	}
	if ((fs.mid) && (fs.msg)){
		msgfunction[fs.msg]=fs.mid;
		delete fs.mid;
		delete fs.msg;
	}
	fs.style.overflow='';
	fs.classList.remove('active');
}
function stdinsend(cmd){
	var stdin=cmd.target.value;
	cmd.target.value='';
	sendmsg('hpcexecute',{'cmd':(btoa(stdin))});
}
function runscript(cmd){
	var stdin='/bin/bash $WORK/middleware-tn/webfolder/';
	stdin+=cmd.value;
	document.getElementById('marconi').classList.remove('active');
	cmd.value='';
	sendmsg('hpcexecute',{'cmd':(btoa(stdin))});
}

/* <div class='icon'> filename
 * 	<ul class='menu'>
 * 		<li class='spread'><a class='unit' href='#'> share </a></li>
 * 		<li class='spread'><a class='unit' href='#'> delete </a></li>
 * 		<li class='spread'><a class='unit' href='#'> rename </a></li>
 * 	</ul>
 * </div>
 */	
function menuitem(text,onc){
	var fspread=document.createElement('span');
	fspread.classList.add('spread');
	var fa=document.createElement('a');
	fa.classList.add('unit');
	fa.innerText=text;
	fa.onclick=onc;
	fspread.appendChild(fa);
	return fspread;
}
function filerename(orig,dest){
	console.log('rename ',orig);
	//sendmsg('filerename',{src:orig,dst:dest});
	removediv(orig);
}
function fileshare(orig,val){
	sendmsg('filexattr',{'name':orig,'xattr':'user.share','value':val});
	removediv(orig);
}
function filedelete(orig){
	sendmsg('hpcexecute',{'cmd':(btoa('rm $WORK/middleware-tn/webfolder/'+orig))})
	sendmsg('filedelete',{'name':orig});
	removediv(orig);
	
}

function fileitem(file){
	var fdiv=document.createElement('div');
	//fdiv.innerText=file;
	//fdiv.classList.add('delayedfunc');
	fdiv.id=file;
	var fname=document.createElement('span');
	fname.id='name'+file;
	fname.innerText=file;
	//fname.style.float='left';
	//fname.style.position='fixed';
	fname.style.margin='1em';
	fname.classList.add('icon');
	
	var fsize=document.createElement('span');
	fsize.id='size'+file;
	//fsize.style.float='';
	fsize.style.marginLeft='1em';
	fsize.classList.add('icon');
	var fdate=document.createElement('span');
	fdate.id='date'+file;
	fdate.style.marginLeft='1em';
	//fdate.style.float='left';
	fdate.classList.add('icon');
	//fdate.classList.add('two');
	
	fdiv.appendChild(fdate);
	fdiv.appendChild(fsize);
	fdiv.appendChild(fname);
	
	var fmenur=document.createElement('span');
	fmenur.classList.add('menu');
	fmenur.appendChild(menuitem('rename',function(){filerename(file);}));
	fname.appendChild(fmenur);
	
	// if file.stat.local
	//fmenu.appendChild(menuitem('share',function(){console.log('share ',file);}));
	//fmenu.appendChild(menuitem('rename',function(){console.log('rename ',file);}));
	//fdiv.appendChild(fmenu);
	
	return fdiv;
}
function removediv(file){
	var el=document.getElementById('fullscreen');
	if (!(el.classList.contains('active')))
		return;
	var loc=el.getElementsByClassName('localdiv')[0];
	var rem=el.getElementsByClassName('remotediv')[0];
	var fl=[];
	loc.childNodes.forEach(function(e){if (e.id==file) loc.removeChild(e);});
	rem.childNodes.forEach(function(e){if (e.id==file) rem.removeChild(e);});
}
function populatediv(el,file,statk,statv){
	if (!(el.classList.contains('active')))
		return;
	var loc=el.getElementsByClassName('localdiv')[0];
	var rem=el.getElementsByClassName('remotediv')[0];
	var fl=[];
	if ((loc) && (rem)){
		loc.height='100%';
		rem.height='100%';
		loc.childNodes.forEach(function(e){fl.push(e.id);});
		rem.childNodes.forEach(function(e){fl.push(e.id);});
	}
	if (fl.indexOf(file)>-1){
		switch (statk){
		case ('ctime'):
			var fspan=document.getElementById('date'+file);
			//var d=new Date(statv*1000);
			var toptions = {
					  hour: 'numeric', minute: 'numeric', second: 'numeric',
					  year: 'numeric', month: 'numeric', day: 'numeric',
					  hour12: false
					};
			fspan.textContent=Intl.DateTimeFormat('it-IT',toptions).format(new Date(statv*1000));
			var fmenud=document.createElement('span');
			fmenud.classList.add('menu');
			fspan.classList.add('picol_trash');
			fmenud.appendChild(menuitem('delete',function(){filedelete(file);}));
			fspan.appendChild(fmenud);
			
			break;
		case ('size'):
			var fspan=document.getElementById('size'+file);
			var i = Math.floor( Math.log(statv) / Math.log(1024) );
			fspan.textContent=''+( statv / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
			var fdiv=document.getElementById(file);
			var par=fdiv.parentElement;
			if ((par==loc)&&(statv<(1024*1024*20))){
				var fmenus=document.createElement('span');
				fmenus.classList.add('menu');
				if (fdiv.share==''){
					fspan.classList.remove('picol_globe');
					fmenus.appendChild(menuitem('share',function(){fileshare(file,'true');}));
				}else{
					fspan.classList.add('picol_globe');
					fmenus.appendChild(menuitem('unshare',function(){fileshare(file,'');}));
				}
				fspan.appendChild(fmenus);
			}
			break;
		case('xattr'):
			var fdiv=document.getElementById(file);
			var par=fdiv.parentElement;
			fdiv.classList.remove('transparent');
			var w=loc.getElementsByClassName('spinner');
			if (w.length>0)
				loc.removeChild(w[0]);
			w=rem.getElementsByClassName('spinner');
			if (w.length>0)
				rem.removeChild(w[0]);
			
			if ('user.author' in statv){
				if(par!=rem){
					par.removeChild(fdiv);
					rem.appendChild(fdiv);
				}
			} else{
				if (par!=loc){
					par.removeChild(fdiv);
					loc.appendChild(fdiv);		
				}
				fdiv.share='';
				if ('user.share' in statv){
					fdiv.share=statv['user.share'];
				}
			}
			
		default:
			break;
		}
				
		// update values
		return;
	}
	var fdiv=fileitem(file);
	fdiv.classList.add('transparent');
	loc.appendChild(fdiv);
	
}

function openfsfile(elem){
	var fs=document.getElementById('fullscreen');
	if (fs.classList.contains('active')) 
		return;
	filefolder=new Proxy(_filefolder,{get:function(t,k){
										return t[k];},
									set:function(t,filename,v){
										//populatediv(fs,k,t[k]);
										t[filename]=new Proxy({},{
											get:function(st,sk){return st[sk];},
											set:function(st,sk,sv){
												if (st[sk]!=sv)
													populatediv(fs,filename,sk,sv);
												st[sk]=sv;
											}
										});	
										}
									}
				);
	
	fs.style.overflow='auto';
	var head=document.getElementById('fshead');
	head.innerText='Close';
	var localdiv=document.createElement('div');
	var remotediv=document.createElement('div');
	localdiv.classList.add('localdiv');
	localdiv.classList.add('picol_computer');
	
	remotediv.classList.add('remotediv');
	remotediv.classList.add('picol_cloud');
	
	fs.appendChild(localdiv);
	fs.appendChild(remotediv);
	localdiv.innerHTML='<div class="spinner"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div>';
	remotediv.innerHTML='<div class="spinner"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div>';
	
	
	
	fs.classList.add('active');
}

function openfscli(elem){
	var fs=document.getElementById('fullscreen');
	if (fs.classList.contains('active')) 
		return;
	fs.msg='hpcout';
	fs.mid=msgfunction['hpcout'].onmessage;
	var source=document.getElementById('cli');
	var output=document.createElement('div');
	var input=document.createElement('input');
	var head=document.getElementById('fshead');
	head.innerText='Close';
	fs.style.overflow='auto';
	fs.appendChild(output);
	output.innerHTML=source.innerHTML;
	
	input.type='text';
	input.size='110';
	
	fs.appendChild(input);
	
	input.onchange=stdinsend;
    //input.onkeyup=stdinchange;
	
    fs.classList.add('active');
	msgfunction['hpcout'].onmessage=function(id,msg){
													var str=Object.keys(msg);
													str.map(function(io){output.insertAdjacentHTML('beforeend',msg[io]+'<br>');});
													fs.mid(id,msg);
													};
		
}
function openfsgraph(elem){
	var fs=document.getElementById('fullscreen');
	if (fs.classList.contains('active')) 
		return;
	var source=document.getElementById('graph');
	var obj=document.createElement('object');
	fs.core=source.childNodes[0];
	fs.destination=source;
	//while (fs.childNodes.length>1){
	//	fs.childNodes.forEach(function(node){if (node.id!='fullscreencloser') fs.removeChild(node);});	
	//}
	if (fs.core){
		var head=document.getElementById('fshead');
		head.innerText='Close';
		obj.data=fs.core.src;
		obj.style.width='95%';
		obj.style.height='95%';
		fs.appendChild(obj);
		fs.classList.add('active');
	}
}
function openfsstat(elem){
	var fs=document.getElementById('fullscreen');
	if (fs.classList.contains('active')) 
		return;
	var source=document.getElementById('stat');
	var textarea=document.createElement('textarea');
	textarea.textContent=source.textContent;
	textarea.style.width="100%";
	textarea.style.height="90%";
	fs.appendChild(textarea);
	var head=document.getElementById('fshead');
	head.innerText='Close';
	fs.classList.add('active');
}
function openfseditor(elem){
	var fs=document.getElementById('fullscreen');
	if (fs.classList.contains('active')) 
		return;
	var source=document.getElementById('diveditor');
	fs.core=null;
	fs.destination=null;
	//while (fs.childNodes.length>1){
	//	fs.childNodes.forEach(function(node){if (node.id!='fullscreencloser') fs.removeChild(node);});
	//}
	source.childNodes.forEach(function(node){if (node.id=='preeditor'){
											fs.core=node.children[0];
											fs.destination=node;}});
	if ((fs.core)&&(fs.core.eof)){
		var textarea=document.createElement('textarea');
		textarea.textContent=fs.core.filedata;
		var savebutton=document.createElement('p');
		
		//savebutton.onclick=function(e){filesave(fs.core.filename,textarea.textContent);};
		savebutton.onmouseover=function(e){TweenLite.delayedCall(2,filesave,[fs.core.filename,textarea,savebutton]);};
		savebutton.onmouseleave=function(e){TweenLite.killDelayedCallsTo(filesave);}
		
		fs.appendChild(savebutton);
		savebutton.innerHTML='<b class="picol_floppy_disk" >Save</b>';
		
		savebutton.classList.add('delayedfunc');
		savebutton.classList.add('two');
		
		textarea.style.width="100%";
		textarea.style.height="90%";
		fs.appendChild(textarea);
		var head=document.getElementById('fshead');
		head.innerText='Close';
		//fs.listen=new Proxy(editor,{set:function(t,k,v){if (k=='innerHTML') return fs[k]=v;}});
		fs.classList.add('active');
		//savebutton.addEventListener('onclick',filesave(fs.core.filename,textarea.textContent),false);
		//savebutton.onmouseover=TweenLite.delayedCall(2,filesave,[fs.core.filename,textarea.textContent]);
		//savebutton.onmouseleave=TweenLite.killDelayedCallsTo(filesave);
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
function assignstats(id,stat){
	var key=Object.keys(stat);
	eval(id)[stat.file]={};
	key.map(function(k){eval(id)[stat.file][k]=stat[k];});
	//eval(id)[stat.file]={stat};
	//console.log('stat to',datamsg.file);
}

function showmime(id,datamsg){
	var divembed=document.getElementById(id);
	var embed=document.createElement('iframe');
	embed.setAttribute('type',datamsg.src.split(';')[0].replace('data:',''));
	embed.style.width='99%';
	embed.style.height='95%';
	embed.style.position='relative';
	embed.src=datamsg.src;
	while (divembed.hasChildNodes()) divembed.removeChild(divembed.firstChild);
	divembed.appendChild(embed);
}
function filesave(filename,elem,that){
	TweenLite.killDelayedCallsTo(filesave);
	//console.log('save ',filename,data);
	var str=elem.value;
	var data=btoa(str);
	sendmsg('filesave',{name:filename,data:data});
	that.classList.remove('two');
	that.classList.add('saved');
	setTimeout(function(){that.classList.add('two');
						that.classList.remove('saved');},1000);
	getblock(filename,0);
}
function showfile(id,datamsg){
	var el=document.getElementById(id);
	var same=(datamsg['offset']!=0);
	var head=document.getElementById('editorexpander');
	
	el.eof=false;
	if (el.hasOwnProperty('blockoffset')&&same){
		el.eof=datamsg['blocksize']==0;
	}
	if (!el.eof)
		head.classList.add('transparent');
	else
		head.classList.remove('transparent');
	
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
	//filefolder[filename]={};
	/*filefolder[filename].local=islocal;
	filefolder[filename].shared=ischecked;*/
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
	_filefolder={};
	files.map(function(name){fileelement(name,el,checked.indexOf(name)!=-1,local.indexOf(name)!=-1);sendmsg('filestats',{'name':name});});
	
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
	setTimeout(getdir,7000);
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
