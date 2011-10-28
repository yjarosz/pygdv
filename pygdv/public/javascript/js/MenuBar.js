
/*
 * This file contains everything about the left Menu.
 * - the navigation menu (Home, Projects, ...)
 * - the gFeatMiner menu
 */

/*function initMenuBar(browser){*/
dojo.declare("ch.epfl.bbcf.gdv.GDVMenuBar",null,{
    constructor: function(args){
        dojo.mixin(this, args);
        if(this.toolbar && this.menu_navigation){
	    this.build_navigation(this.menu_navigation);
	    this.build_gminer();
	} else {
	    console.warn('cannot build toolbar, no json specified');
        }
    },
    
    /**
     * Build the ``Navigation`` menu
     *@param{item_list} : the menu items
     */
    build_navigation : function(item_list){
	
	var container = dojo.byId('gdv_menu');
	var navig = document.createElement('div');
	navig.innerHTML = 'Navigation';
	navig.className = 'menu_entry';
	container.appendChild(navig);
	var len = item_list.length;
	for (var i=0; i<len; i++){
	    link_name = item_list[i];
	    link_end = link_name.toLowerCase();
	    var cont = document.createElement('div');
	    var link = document.createElement('a');
	    cont.appendChild(link);
	    // Make an image
	    var img = document.createElement('img');
	    img.src = window.picsPathRoot + "menu_" + link_end + ".png";
	    img.className='gdv_menu_image';
	    link.appendChild(img);
	    // Create a span
	    var span = document.createElement('span');
	    span.innerHTML=link_name;
	    span.className='gdv_menu_item';
	    link.appendChild(span);
	    // Configure the link
	    link.href=_GDV_URL+'/'+link_end;
	    link.className='hl';
	    container.appendChild(cont);
	}
    },
    /**
     * Build the HTML Menu
     */
    build_gminer : function(){
        var toolbar = this.toolbar;
        this.form_ids_template = toolbar['form_ids_template'];
        /* title */
        var htmlroot = dojo.byId("gdv_menu");
        var div = document.createElement("div");
        div.className = "menu_entry";
        div.innerHTML=toolbar['title'];
        htmlroot.appendChild(div);
        /* pricipal menu */
        var pmenu = this.getMenu(toolbar,'100%')
        pmenu.placeAt("gdv_menu")
    },
    /**
     * Get the children of the item and not other parameters
     * in order to loop over them. They all begin by
     * 'form_ids_template' variable
     */
    getChilds : function(item){
        var prefix = this.form_ids_template
        data=[];
        for(i in item){
	    if (this.start_with(i, prefix)) {
		data.push(item[i]);
	    }
        }
        return data
    },
    /**
     * Look if a string start with the string specified.
     * This is the most efficient way to do this.
     * @param data : the string to check on
     * @param str : the prefix to look on.
     */
    start_with : function(data, str){
        return data.lastIndexOf(str, 0) === 0
    },
    
    /**
     * Build the menu for an item that has children
     *@param{item} the item
     *@Pparam{w} the width of the menu
     */
    getMenu : function(item,w){
        /* define the menu */
        var menu = new dijit.Menu({
	    colspan:1,
	    style:{width:w}
        });
	
        /* loop over childs */
        var childs = this.getChilds(item);
        var len=childs.length;
        for(var i=0; i<len; i++){
	    var child = childs[i];
	    /** connect the menu if it's a leaf or
	     * recursivly get childs
	     */
	    if(child.doform){
		var ctx=this;
		menu.addChild(ctx.getMenuItem(ctx,child));
	    } else {
		var child_menu = this.getMenu(child,'10em');
		var popup_item = new dijit.PopupMenuItem({
		    label:child.name,
		    popup: child_menu
		});
		menu.addChild(popup_item);
	    }
	    if(i+1<len){
		menu.addChild(new dijit.MenuSeparator());
	    }
        }
        return menu;
    },
    /**
     * Build a Menuitem corresponding to the given item
     * @param{ctx} the context
     * @param{item} the menu item
     */
    getMenuItem : function(ctx,item){
        var o = new dijit.MenuItem({
	    label:item.name,
	    onClick: function(event) {
		ctx.displayForm(item);
		dojo.stopEvent(event);
	    }});
        return o;
    },
    
    /**
     * Display the form corresponding to the item clicked
     */
    displayForm : function(item){
        _tc.addFormTab(item);
        _tc.container.selectChild("tab_form");
    }
});
