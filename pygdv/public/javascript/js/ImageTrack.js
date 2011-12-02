function ImageTrack(trackMeta, url, refSeq, browserParams) {
    Track.call(this, trackMeta.label, trackMeta.key,
               false, browserParams.changeCallback);
    this.refSeq = refSeq;
    this.gdv_id=trackMeta.gdv_id;
    this.tileToImage = {};
    this.zoomCache = {};
    this.baseUrl = (browserParams.baseUrl ? browserParams.baseUrl : "");
    this.load(this.baseUrl + url);
    this.color=trackMeta.color;
    this.imgErrorHandler = function(ev) {
        var img = ev.target || ev.srcElement;
        img.style.display = "none";
        dojo.stopEvent(ev);
    };
    //inner zoom in each track
    this.inzoom = 1;
}

ImageTrack.prototype = new Track("");

ImageTrack.prototype.loadSuccess = function(o) {
    //CHANGES (pass the min and the max to the current track)
    this.min = o.min;
    this.max = o.max;
    this.getScale(this.inzoom);
    drawScale(this.scale);


    //tileWidth: width, in pixels, of the tiles
    this.tileWidth = o.tileWidth;
    //zoomLevels: array of {basesPerTile, scale, height, urlPrefix} hashes
    this.zoomLevels = o.zoomLevels;
    //console.log(this.zoomLevels);
    this.setLoaded();
};

ImageTrack.prototype.setViewInfo = function(heightUpdate, numBlocks,
                                            trackDiv, labelDiv,
                                            widthPct, widthPx, scale) {
    Track.prototype.setViewInfo.apply(this, [heightUpdate, numBlocks,
                                             trackDiv, labelDiv,
                                             widthPct, widthPx, scale]);
    this.setLabel(this.key);
};

ImageTrack.prototype.getZoom = function(scale) {
    //console.log(scale);
    var result = this.zoomCache[scale];
    if (result) return result;

    result = this.zoomLevels[0];
    var desiredBases = this.tileWidth / scale;
    for (i = 1; i < this.zoomLevels.length; i++) {
    //console.log(Math.abs(this.zoomLevels[i].basesPerTile - desiredBases) < Math.abs(result.basesPerTile - desiredBases));
        if (Math.abs(this.zoomLevels[i].basesPerTile - desiredBases)
            < Math.abs(result.basesPerTile - desiredBases)){
            result = this.zoomLevels[i];
    }
    }
    this.zoomCache[scale] = result;
    return result;
};
//CHANGES (adding scale)
ImageTrack.prototype.setScale = function(scale){
    this.scale = scale;
}
/**
 * init the scale
 *@param{inzoom} the zoom on the track
 */
ImageTrack.prototype.getScale = function(inzoom){
    this.scale.min = this.min;
    this.scale.max = this.max/inzoom;
};

/**
 * get the HTML images corresponding to the parameters
 * @param {zoom} current zoom on the view
 * @param {startBase} the start of the view
 * @param {endBase} the end of the view
 * @param {inzoom} the inner zoom of the current track -optionnal-
 */
ImageTrack.prototype.getImages = function(zoom, startBase, endBase, inzoom) {
    //var startTile = ((startBase - this.refSeq.start) / zoom.basesPerTile) | 0;
    //var endTile = ((endBase - this.refSeq.start) / zoom.basesPerTile) | 0;
    // console.log(zoom);
    // console.log(startBase+"     "+endBase);
    var startTile = (startBase / zoom.basesPerTile) | 0;
    var endTile = (endBase / zoom.basesPerTile) | 0;
    startTile = Math.max(startTile, 0);
    var result = [];
    var im;
    for (var i = startTile; i <= endTile; i++) {
	im = this.tileToImage[i];
	
	if (!im) {
            im = document.createElement("canvas");
	    im.className = "track_scores";
	    im.db = zoom.urlPrefix;
	    im.nb = i+1;
            im.min = this.min;
	    im.max = this.max;
	    
	    
            im.color = this.color;
	    //        im = document.createElement("img");
            dojo.connect(im, "onerror", this.imgErrorHandler);
            ////prepend this.baseUrl if zoom.urlPrefix is relative
            //var absUrl = new RegExp("^(([^/]+:)|\/)");
            //im.src = (zoom.urlPrefix.match(absUrl) ? "" : this.baseUrl)
            //        + zoom.urlPrefix + i + ".png";
            ////TODO: need image coord systems that don't start at 0?
            im.startBase = (i * zoom.basesPerTile); // + this.refSeq.start;
            im.baseWidth = zoom.basesPerTile;
            im.tileNum = i;
            this.tileToImage[i] = im;
	    im.inzoom = inzoom;
	    

	};
	im.inzoom = inzoom;
	result.push(im);
	
    };
    return result;
};

ImageTrack.prototype.fillBlock = function(blockIndex, block,
                                          leftBlock, rightBlock,
                                          leftBase, rightBase,
                                          scale, stripeWidth,
                                          containerStart, containerEnd) {
    var zoom = this.getZoom(scale);
    var blockWidth = rightBase - leftBase;
    if(!this.inzoom){
	this.inzoom = 1;
    }
    var images = this.getImages(zoom, leftBase, rightBase, this.inzoom);
    var im;
    //CHANGES (adding image drawer)
    var imd = new ImageDrawer();
    imd.getAllScores(images);


    for (var i = 0; i < images.length; i++) {
	im = images[i];
	if (!(im.parentNode && im.parentNode.parentNode)) {
            im.style.position = "absolute";
	    //console.log(im);
            im.style.left = (100 * ((im.startBase - leftBase) / blockWidth)) + "%";
            im.style.width = (100 * (im.baseWidth / blockWidth)) + "%";
            //im.style.top = "0px";
            im.style.height = zoom.height + "px";
            block.appendChild(im);
	};
    };
    
    this.heightUpdate(zoom.height, blockIndex);
};

ImageTrack.prototype.startZoom = function(destScale, destStart, destEnd) {
    if (this.empty) return;
    this.tileToImage = {};
    this.getImages(this.getZoom(destScale), destStart, destEnd);
};

ImageTrack.prototype.endZoom = function(destScale, destBlockBases) {
    Track.prototype.clear.apply(this);
};

ImageTrack.prototype.clear = function() {
    Track.prototype.clear.apply(this);
    this.tileToImage = {};
};

ImageTrack.prototype.transfer = function(sourceBlock, destBlock, scale,
                                         containerStart, containerEnd) {
    if (!(sourceBlock && destBlock)) return;

    var children = sourceBlock.childNodes;
    var destLeft = destBlock.startBase;
    var destRight = destBlock.endBase;
    var im;
    for (var i = 0; i < children.length; i++) {
    im = children[i];
    if ("startBase" in im) {
        //if sourceBlock contains an image that overlaps destBlock,
        if ((im.startBase < destRight)
        && ((im.startBase + im.baseWidth) > destLeft)) {
        //move image from sourceBlock to destBlock
        im.style.left = (100 * ((im.startBase - destLeft) / (destRight - destLeft))) + "%";
        destBlock.appendChild(im);
        } else {
        delete this.tileToImage[im.tileNum];
        }
    }
    }
};


/**
 * Fonction which will launch the zoom in each track
 * @param{gv} the GenomeView Object
 * @param{scale} the scale
 * @param{factor}  eg.+1 or -1
 */
ImageTrack.prototype.innerZoom = function(gv,scale,factor){
    if(this.inzoom<=1 && factor<0){
    return;
    } else {
    this.inzoom+=factor;
    this.getScale(this.inzoom);
    drawScale(this.scale);
    var pos = gv.getPosition();
    var startX = pos.x - (gv.drawMargin * gv.dim.width);
    var endX = pos.x + ((1 + gv.drawMargin) * gv.dim.width);
    var leftVisible = Math.max(0, (startX / gv.stripeWidth) | 0);
    var rightVisible = Math.min(gv.stripeCount - 1, (endX / gv.stripeWidth) | 0);
    var bpPerBlock = Math.round(gv.stripeWidth / gv.pxPerBp);
    var startBase = Math.round(gv.pxToBp((leftVisible * gv.stripeWidth)+ gv.offset));
    var containerStart = Math.round(gv.pxToBp(gv.offset));
    var containerEnd = Math.round(gv.pxToBp(gv.offset + (gv.stripeCount * gv.stripeWidth)));
    var zoom = this.getZoom(gv.pxPerBp);
    var endBase = ((rightVisible-leftVisible)*bpPerBlock)+startBase;
    var images = this.getImages(zoom,startBase,endBase,this.inzoom);
    var imd = new ImageDrawer();
    imd.getAllScores(images);
    }
};
/*

Copyright (c) 2007-2011 The Evolutionary Software Foundation

Created by Mitchell Skinner <mitch_skinner@berkeley.edu>
Modified by Yohan Jarosz <yohan.jarosz@epfl.ch>

This package and its accompanying libraries are free software; you can
redistribute it and/or modify it under the terms of the LGPL (either
version 2.1, or at your option, any later version) or the Artistic
License 2.0.  Refer to LICENSE for the full license text.

*/
