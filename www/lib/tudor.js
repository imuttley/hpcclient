var localdb;
var remoteserver='http://192.107.94.227:5984/';
var pbsformaction='commands/_design/schedule/_update/pbssub/';
var qstatformaction='commands/_design/schedule/_update/qstat/';
var dbfolder='folders';
var filetype={'other':0,'hoc':1,'mod':2,'py':3};
var record={_id:'',_rev:'',stats:'',date:'',_attachments:''};
var remotedb=remoteserver+dbfolder;
var subm=new XMLHttpRequest(); 

var msgfunction={'filelist':{elemid:'folder',onmessage:showlist},'fileselect':{elemid:'editor',onmessage:showfile}};
var mainwindow=null;

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

var jobqueue=eventfordiv('jobquery','queue');

function showfile(id,datamsg){
	var el=document.getElementById(id);
	el.textContent=datamsg['block'];
	el.filename=datamsg['name'];
}
function showlist(id,listmsg){
	var el=document.getElementById(id);
	var files=eval(listmsg);
	var ul=document.createElement('ul');
	while (el.hasChildNodes()) el.removeChild(el.firstChild);
	for (var i=0;i<files.length;i++){
		var item=document.createElement('li');
		item.setAttribute('id',files[i]);
		item.setAttribute('onclick','getblock(this.id,0)');	
		item.textContent=files[i];
		el.appendChild(item);
	}
}
function getblock(filename,offset){
	sendmsg('fileselect',{filename:filename,offset:offset,size:400});
}
function sendmsg(req,obj){
	if (mainwindow)
		mainwindow.postMessage({method:req,params:obj},'*');
	else
		console.log('mainwindow not defined');
}
function log(id,msg){
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
function getfile(e){
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
	if ((e.code=='ArrowDown')||(e.code=='ArrowUp')){
		console.log('editor text area blocksize:',e.target.textLength);	
		console.log('editor cursor position:',e.target.selectionEnd);
	}

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

	


	window.localdb=new PouchDB(dbfolder);	
	window.onmessage=function(e){
	        if (window.location.origin!=e.origin){
			var response=e.data.content.response;
			if (msgfunction.hasOwnProperty(response)){
				(msgfunction[response].onmessage)(msgfunction[response].elemid,e.data.content.data);	
                	}else{
				mainwindow=e.source;
				console.log('message from external iframe:',e.data.content);
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
