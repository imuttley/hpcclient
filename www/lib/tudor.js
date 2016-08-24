var localdb;
var remotedb='http://192.107.94.227:5984/';
var pbsformaction='commands/_design/schedule/_update/pbssub/';
var qstatformaction='commands/_design/schedule/_update/qstat/';
var folderdb="folders"

var subm=new XMLHttpRequest(); 

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


function log(ev){
	if (ev.origin){
		if (ev.origin!=window.location.origin)
			console.log('message from external:',ev);
	} else
		console.log('message from internal:',ev);
}

window.onmessage=log;
          
function events(){
	
	var jobqueue=eventfordiv('jobquery','queue');
	var jobstats=eventfordiv('stats','stat');
	//var graph=eventfordiv('','graph');
	
}
function jobsubmit(e){
	var max={nodes:3000,cpus:36,mem:1000};
	
	if (window.location.protocol!='data:'){
		subm.open("POST",remotedb+pbsformaction+userstatus.streams.stdin[0]);
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
		window.top.postMessage({method:'runjob',params:query},'*');
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
