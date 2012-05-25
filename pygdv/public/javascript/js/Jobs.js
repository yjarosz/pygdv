var JOB_LOADING_TIME = 5000

function JobPane(){
    this.prefix = 'gdvjobs_';
    this.showed = false;
};


JobPane.prototype.init_panel = function(DomNode, DijitNode){
    var cont = dojo.create('div', {}, DomNode);
    var job_container = new dijit.layout.ContentPane({
	title: "Jobs",
	id:'tab_jobs'
    }, cont);
    DijitNode.addChild(job_container);
    
    this.jobs = job_container;
    
    
    //init jobs                                                                                                      
    var jobs = init_jobs;
    var jobs_table = dojo.create("table", {id:"jobs_table", className: 'pane_table',}, cont);
    this.jobstable = jobs_table;
    this.display_jobs(jobs);
    
};

/**
* Return the right display for the job output
* And set the contect pane to "Running" state
*/
JobPane.prototype.job_output = function(job){
    var job_output = job.output;
    switch(job_output){
    case 'job_image': return dojo.create('a', {target:'_blank', href: _GDV_JOB_URL + '/result?id=' + job.id, innerHTML:'view output'});
    case 'job_failure': return dojo.create('a', {target:'_blank', href: _GDV_JOB_URL + '/traceback?id=' + job.id, innerHTML:'failure'});
    case 'job_track' : return dojo.create('a', {innerHTML : 'reload', href : 'javascript:location.reload(true);'});
    default : 
	var p = dojo.create('div', {className : 'tiny_loading_gif'}); 
	this.running = true;
	return p
	
	
    }
};

/**
* Fetch the jobs from the server and callback them.
*/
JobPane.prototype.get_jobs = function(callback, context){
    var pdata="project_id=" + _gdv_info.project_id;
    var xhrArgs = {
	url : _GDV_JOB_URL + '/get_jobs',
	postData : pdata,
	handleAs : 'json',
	load : function(data){
	    callback(data, context);
	},
	error : function(data){
	    console.error(data);
	},
    };
    dojo.xhrPost(xhrArgs);
};

/**
* Delete job on the server and remove it from the view
*/
JobPane.prototype.deljob = function(job_id){
    var pdata= '_id=' + job_id;
    var xhrArgs = {
	url : _GDV_JOB_URL + '/_delete',
	postData : pdata,
	handleAs : 'json',
	load : function(data){
	},
	error : function(data){
	    console.error(data);
	},
    };
    dojo.xhrPost(xhrArgs);
    
    dojo.destroy(this.prefix + job_id);
    
};


/**
* Display jobs on the panel, can specify on which context 
* to call this function
*/
JobPane.prototype.display_jobs = function(jobo, context){
    var ctx = this;
    if(context){
	ctx = context;
    }
    ctx.running = false;
    
    var jobs = jobo['jobs'];
    var jbl = jobs.length;
    for(var i=0; i<jbl; i++){
	var job = jobs[i];
	var tr = null;
	if (dojo.byId(ctx.prefix + job.id)){
	    tr = dojo.byId(ctx.prefix + job.id);
	    dojo.empty(tr);
	} else {
	    tr = dojo.create("tr", {id: ctx.prefix + job.id}, ctx.jobstable);
	}
	
	var m = dojo.create("table", {className: 'pane_element'}, tr);
	var tr = dojo.create("tr", {}, m);
	var td = dojo.create("td", {className: 'pane_unit', innerHTML: job.name, title: job.description}, tr);
	var td = dojo.create("td", {className: 'pane_unit'}, tr);
	
	
	td.appendChild(ctx.job_output(job));
	
	var del = dojo.create("td", {className:"delete"}, tr);
	dojo.create("div", {innerHTML:"", className:"delete_img_field"}, del);
	ctx.connect_delete(del, job);
    }
    if (ctx.running && ctx.showed){
	setTimeout(function(){
	    var fn = ctx.display_jobs;
		ctx.get_jobs(fn, ctx);
	}, JOB_LOADING_TIME);
    }
};

/**
* Activate or deactivate the routine to fetch jobs from server
*/
JobPane.prototype.routine = function(bool){
    if(bool){
	this.showed = true;
	var ctx = this;
	setTimeout(function(){
            var fn = ctx.display_jobs;
            ctx.get_jobs(fn, ctx);
	}, JOB_LOADING_TIME);
    } else {
	this.showed = false;
    }

};

/**
* Connect a deletion event to a DomNode
*/
JobPane.prototype.connect_delete = function(HTMLnode, job){
    var ctx = this;
    dojo.connect(HTMLnode, 'click', function(e){
	if (confirm('Are you sure ?')){
	    ctx.deljob(job.id);
	}
	dojo.stopEvent(e);
    });
    
};

function op_form_submitted(){
    setTimeout(function(){
	var fn = _gdv_pc.jobs.display_jobs;
	_gdv_pc.show_jobs();
	_gdv_pc.jobs.get_jobs(fn, _gdv_pc.jobs);
    }, 1250);
    
};